import logging
import math
import time

from datetime import datetime
from queue import Queue
from threading import Thread

from typing_extensions import final, override

from playout.config import PUSH_INTERVAL, Config
from playout.player.events import AnyEvent, Events, FileEvent
from playout.player.liquidsoap import Liquidsoap
from playout.player.queue import PypoLiqQueue
from sdk import UTC

logger = logging.getLogger(__name__)


@final
class PypoPush(Thread):

    name: str = "push"
    daemon: bool = True

    def __init__(
        self,
        push_queue: Queue[Events],
        liquidsoap: Liquidsoap,
        config: Config,
    ) -> None:
        Thread.__init__(self)
        self.queue: Queue[Events] = push_queue

        self.config: Config = config

        self.future_scheduled_queue: Queue[Events] = Queue()
        self.liquidsoap: Liquidsoap = liquidsoap

        self.plq: PypoLiqQueue = PypoLiqQueue(
            self.future_scheduled_queue,
            self.liquidsoap,
        )
        self.plq.start()

    def main(self) -> None:
        loops = 0
        heartbeat_period = math.floor(30 / PUSH_INTERVAL)

        events = None

        while True:
            try:
                events = self.queue.get(block=True)

            except Exception:
                logger.exception(
                    "Exception while getting media schedule from push queue",
                )
                raise

            # separate media_schedule list into currently_playing and
            # scheduled_for_future lists
            currently_playing, scheduled_for_future = (
                self.separate_present_future(events)
            )

            self.liquidsoap.verify_correct_present_media(currently_playing)
            self.future_scheduled_queue.put(scheduled_for_future)

            if loops % heartbeat_period == 0:
                logger.info("heartbeat")
                loops = 0
            loops += 1

    def separate_present_future(
        self,
        events: Events,
    ) -> tuple[list[AnyEvent], Events]:
        now = datetime.now(UTC)

        present: list[AnyEvent] = []
        future: Events = {}

        for key in sorted(events.keys()):
            item = events[key]

            # Ignore track that already ended
            if isinstance(item, FileEvent) and item.end < now:
                logger.debug("ignoring ended media_item: %s", item)
                continue

            diff_sec = (now - item.start).total_seconds()

            if diff_sec >= 0:
                logger.debug("adding media_item to present: %s", item)
                present.append(item)
            else:
                logger.debug("adding media_item to future: %s", item)
                future[key] = item

        return present, future

    @override
    def run(self) -> None:
        while True:
            try:
                self.main()
            except Exception:
                logger.exception("Exception in liquidsoap push thread")
                time.sleep(5)
