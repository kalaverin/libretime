import copy
import os
import time

from enum import Enum
from pathlib import Path
from queue import Empty, Queue
from subprocess import DEVNULL, PIPE, run
from threading import Thread, Timer
from typing import Any

from api_client.v1 import ApiClient as LegacyClient
from api_client.v2 import ApiClient
from requests import RequestException
from structlog import get_logger
from typing_extensions import override

from playout.config import CACHE_DIR, POLL_INTERVAL, Config
from playout.liquidsoap.client import LiquidsoapClient
from playout.liquidsoap.models import (
    Info,
    MessageFormatKind,
    StreamPreferences,
    StreamState,
)
from playout.player.events import Events, FileEvent, FileEvents
from playout.player.liquidsoap import Liquidsoap
from playout.player.schedule import get_schedule

logger = get_logger(__name__)


class Commands(str, Enum):
    DisconnectSource = "disconnect_source"
    ResetLiquidsoapBootstrap = "reset_liquidsoap_bootstrap"
    SwitchSource = "switch_source"
    UpdateMessageOffline = "update_message_offline"
    UpdateSchedule = "update_schedule"
    UpdateStationName = "update_station_name"
    UpdateStreamFormat = "update_stream_format"
    UpdateTransitionFade = "update_transition_fade"


# pylint: disable=too-many-instance-attributes
class PypoFetch(Thread):

    name: str = "fetch"
    daemon: bool = True

    def __init__(
        self,
        fetch_queue: Queue[dict[str, Any]],
        push_queue: Queue[Events],
        file_queue: Queue[FileEvents],
        liq_client: LiquidsoapClient,
        liquidsoap: Liquidsoap,
        config: Config,
        api_client: ApiClient,
        legacy_client: LegacyClient,
    ) -> None:

        Thread.__init__(self)

        self.fetch_queue: Queue[dict[str, Any]] = fetch_queue
        self.push_queue: Queue[Events] = push_queue
        self.media_prepare_queue: Queue[FileEvents] = file_queue

        self.liq_client: LiquidsoapClient = liq_client
        self.liquidsoap: Liquidsoap = liquidsoap

        self.config: Config = config
        self.api_client: ApiClient = api_client
        self.legacy_client: LegacyClient = legacy_client

        self.last_update_schedule_timestamp: float = time.time()
        self.listener_timeout: int | float = POLL_INTERVAL

        self.cache_dir: Path = CACHE_DIR
        logger.debug("Cache dir", directory=str(self.cache_dir))

        self.schedule_data: Events = {}
        logger.info("PypoFetch: init complete")

    # Handle a message from RabbitMQ, put it into our yucky global var.
    # Hopefully there is a better way to do this.

    def handle_message(self, msg: dict[str, Any]) -> None:
        listener_timeout = max(
            self.last_update_schedule_timestamp - time.time() + POLL_INTERVAL,
            0,
        )
        log = logger.bind(command=msg["event_type"])
        log.debug("handling event %s: %s", msg["event_type"], msg)

        match msg["event_type"]:
            case Commands.UpdateSchedule:
                listener_timeout = POLL_INTERVAL
                self.schedule_data = get_schedule(self.api_client)
                self.process_schedule(self.schedule_data)

            case Commands.ResetLiquidsoapBootstrap:
                self.set_bootstrap_variables()

            case Commands.UpdateStreamFormat:
                log.info("Updating stream format")
                self.update_liquidsoap_stream_format(msg["stream_format"])

            case Commands.UpdateMessageOffline:
                log.info("Updating message offline")
                self.update_liquidsoap_message_offline(
                    msg["message_offline"],
                )

            case Commands.UpdateStationName:
                log.info("Updating station name")
                self.update_liquidsoap_station_name(msg["station_name"])

            case Commands.UpdateTransitionFade:
                log.info("Updating transition_fade")
                self.update_liquidsoap_transition_fade(
                    msg["transition_fade"],
                )

            case Commands.SwitchSource:
                log.info("switch_on_source show command received")
                self.liquidsoap.telnet_liquidsoap.switch_source(
                    msg["sourcename"],
                    msg["status"],
                )

            case Commands.DisconnectSource:
                log.info("disconnect_on_source show command received")
                self.liquidsoap.telnet_liquidsoap.disconnect_source(
                    msg["sourcename"],
                )

            case _:
                log.info("Unknown command")

        if self.listener_timeout != listener_timeout:
            self.listener_timeout = listener_timeout
            log.info("New timeout", timeout=listener_timeout)

    # Initialize Liquidsoap environment
    def set_bootstrap_variables(self) -> None:
        logger.debug("Getting information needed on bootstrap from Airtime")

        try:
            info = Info(**self.api_client.get_info().json())
            preferences = StreamPreferences(
                **self.api_client.get_stream_preferences().json(),
            )
            state = StreamState(**self.api_client.get_stream_state().json())

        except RequestException:
            logger.exception("Unable to get stream settings")
            return

        logger.debug("info: %s", info)
        logger.debug("preferences: %s", preferences)
        logger.debug("state: %s", state)

        cli = self.liquidsoap.liq_client

        try:
            cli.settings_update(
                station_name=info.station_name,
                message_format=preferences.message_format,
                message_offline=preferences.message_offline,
                input_fade_transition=preferences.input_fade_transition,
            )

            cli.source_switch_status(
                name="master_dj",
                streaming=state.input_main_streaming,
            )
            cli.source_switch_status(
                name="live_dj",
                streaming=state.input_show_streaming,
            )
            cli.source_switch_status(
                name="scheduled_play",
                streaming=state.schedule_streaming,
            )

        except OSError:
            logger.exception("Problem updating liquidsoap settings")

        self.liquidsoap.clear_queue_tracker()

    def update_liquidsoap_stream_format(
        self,
        stream_format: MessageFormatKind | int,
    ) -> None:
        try:
            self.liq_client.settings_update(message_format=stream_format)
        except OSError:
            logger.exception("Problem updating stream format")

    def update_liquidsoap_message_offline(self, message_offline: str) -> None:
        try:
            self.liq_client.settings_update(message_offline=message_offline)
        except OSError:
            logger.exception("Problem updating message offline")

    def update_liquidsoap_transition_fade(self, fade: float) -> None:
        try:
            self.liq_client.settings_update(input_fade_transition=fade)
        except OSError:
            logger.exception("Problem updating transition fade")

    def update_liquidsoap_station_name(self, station_name: str) -> None:
        try:
            self.liq_client.settings_update(station_name=station_name)
        except OSError:
            logger.exception("Problem updating station name")

    # Process the schedule
    #
    #  - Reads the scheduled entries of a given range
    #    (actual time +/- "prepare_ahead" / "cache_for")
    #
    #  - Saves a serialized file of the schedule
    #
    #  - playlists are prepared. (brought to liquidsoap format) and,
    #    if not mounted via nsf, files are copied to the cache dir
    #    (Folder-structure: cache/YYYY-MM-DD-hh-mm-ss)
    #
    #  - runs the cleanup routine, to get rid of unused cached files

    def process_schedule(self, events: Events) -> None:

        self.last_update_schedule_timestamp = time.time()
        logger.debug(events)

        all_events: Events = {}
        file_events: FileEvents = {}

        # Download all the media and put annotated playlists

        for key in events:
            item = events[key]
            all_events[key] = item

            if isinstance(item, FileEvent):
                file_events[key] = item

        try:
            self.media_prepare_queue.put(copy.copy(file_events))

        except Exception:
            logger.exception("Problem preparing media for schedule")

        # Send the data to pypo-push

        logger.debug("Pushing to pypo-push")
        self.push_queue.put(all_events)

        # Cleanup

        try:
            self.cache_cleanup(events)
        except Exception:
            logger.exception("Problem during cache cleanup")

    def is_file_opened(self, path: str) -> bool:
        result = run(
            ["lsof", "--", path],
            stdout=PIPE,
            stderr=DEVNULL,
            check=False,
        )
        return bool(result.stdout)

    def cache_cleanup(self, events: Events) -> None:
        """
        Get list of all files in the cache dir and remove them if they aren't
        being used anymore. Input dict() media, lists all files that are
        scheduled or currently playing. Not being in this dict() means the file
        is safe to remove.
        """

        scheduled_file_set = set()
        cached_file_set = set(os.listdir(self.cache_dir))

        for key in events:
            item = events[key]
            if isinstance(item, FileEvent):
                scheduled_file_set.add(item.local_filepath.name)

        expired_files = cached_file_set - scheduled_file_set

        logger.debug("Files to remove %s", str(expired_files))
        root = Path(self.cache_dir).resolve()

        for name in expired_files:
            path = str(root / name)
            log = logger.bind(path=path)

            try:
                log.debug("Removing file")

                # check if this file is opened (sometimes Liquidsoap is still
                # playing the file due to our knowledge of the track length
                # being incorrect!)

                if not self.is_file_opened(path):
                    os.remove(path)
                    log.info("File removed")

                else:
                    log.warning("File not removed. Still busy!")

            except Exception:
                log.exception("Problem removing file")

    def manual_schedule_fetch(self) -> bool:
        try:
            self.schedule_data = get_schedule(self.api_client)
            logger.debug(
                "Received event from API client",
                data=self.schedule_data,
            )
            self.process_schedule(self.schedule_data)

        except Exception:
            logger.exception("Unable to fetch schedule")
            return False

        return True

    def persistent_manual_schedule_fetch(self, max_attempts: int = 1) -> bool:
        success = False
        num_attempts = 0
        while not success and num_attempts < max_attempts:
            success = self.manual_schedule_fetch()
            num_attempts += 1

        return success

    # This function makes a request to Airtime to see if we need to
    # push metadata to TuneIn. We have to do this because TuneIn turns
    # off metadata if it does not receive a request every 5 minutes.

    def update_metadata_on_tunein(self) -> None:
        self.legacy_client.update_metadata_on_tunein()
        Timer(120, self.update_metadata_on_tunein).start()

    def main(self) -> None:
        # Make sure all Liquidsoap queues are empty. This is important in the
        # case where we've just restarted the pypo scheduler, but Liquidsoap
        # still is playing tracks. In this case let's just restart everything
        # from scratch so that we can repopulate our dictionary that keeps
        # track of what Liquidsoap is playing much more easily.

        self.liquidsoap.clear_all_queues()

        self.set_bootstrap_variables()

        self.update_metadata_on_tunein()

        # Bootstrap: since we are just starting up, we need to grab the
        # most recent schedule.  After that we fetch the schedule every 8
        # minutes or wait for schedule updates to get pushed.
        success = self.persistent_manual_schedule_fetch(max_attempts=5)

        if success:
            logger.info("Bootstrap schedule received: %s", self.schedule_data)

        loops = 1
        while True:
            log = logger.bind(loop=loops)

            log.info("Loop")
            manual_fetch_needed = False

            try:
                # our simple_queue.get() requires a timeout, in which case we
                # fetch the Airtime schedule manually. It is important to fetch
                # the schedule periodically because if we didn't, we would only
                # get schedule updates via RabbitMq if the user was constantly
                # using the Airtime interface.

                # If the user is not using the interface, RabbitMq messages
                # are not sent, and we will have very stale (or non-existent!)
                # data about the schedule.

                # Currently we are checking every POLL_INTERVAL seconds

                message = self.fetch_queue.get(
                    block=True,
                    timeout=self.listener_timeout,
                )
                manual_fetch_needed = False
                self.handle_message(message)

            except Empty:
                log.info("Queue timeout. Fetching schedule manually")
                manual_fetch_needed = True

            except Exception:
                log.exception("Failed to get message from queue")

            try:
                if manual_fetch_needed:
                    self.persistent_manual_schedule_fetch(max_attempts=5)

            except Exception:
                log.exception("Failed to manually fetch the schedule")

            loops += 1

    @override
    def run(self) -> None:
        """
        Entry point of the thread
        """
        self.main()
