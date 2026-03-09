"""
Python part of radio playout (pypo)
"""

import logging
import os
import sys
import time

from datetime import UTC, datetime
from pathlib import Path
from queue import Queue
from typing import TYPE_CHECKING, Any

import click
import sentry_sdk

from api_client import v1, v2
from requests.exceptions import (
    ConnectionError as RequestsConnectionError,
)
from requests.exceptions import (
    HTTPError,
    Timeout,
)
from sdk.cli import cli_config_options, cli_logging_options
from sdk.config import DEFAULT_ENV_PREFIX
from sdk.logging import setup_logger

from playout import PACKAGE, VERSION
from playout.config import CACHE_DIR, RECORD_DIR, Config
from playout.history.stats import StatsCollectorThread
from playout.liquidsoap.client import LiquidsoapClient
from playout.liquidsoap.version import LIQUIDSOAP_MIN_VERSION
from playout.message_handler import MessageListener
from playout.player.fetch import PypoFetch
from playout.player.file import PypoFile
from playout.player.liquidsoap import Liquidsoap
from playout.player.push import PypoPush

if TYPE_CHECKING:
    from playout.player.events import Events, FileEvents

logger = logging.getLogger(__name__)


for module in ("amqp",):
    logging.getLogger(module).setLevel(logging.INFO)
    logging.getLogger(module).propagate = False


def wait_for_legacy(legacy_client: v1.ApiClient) -> None:
    while legacy_client.version() == -1:
        time.sleep(2)

    success = False
    while not success:
        try:
            legacy_client.register_component("pypo")
            break

        except (HTTPError, RequestsConnectionError, Timeout) as e:
            logger.exception(e)
            time.sleep(10)


def wait_for_liquidsoap(liq_client: LiquidsoapClient) -> None:
    logger.debug("Checking if Liquidsoap is running")
    liq_version = liq_client.wait_for_version()
    if not liq_version >= LIQUIDSOAP_MIN_VERSION:
        raise RuntimeError(f"Invalid liquidsoap version {liq_version}")


@click.command(context_settings={"auto_envvar_prefix": DEFAULT_ENV_PREFIX})
@cli_logging_options()
@cli_config_options()
def cli(
    log_level: str,
    log_filepath: Path | None,
    config_filepath: Path | None,
) -> None:
    """
    Run playout.
    """
    setup_logger(log_level, log_filepath)
    config = Config(config_filepath)

    if "SENTRY_DSN" in os.environ:
        logger.info("installing sentry")
        sentry_sdk.init(
            traces_sample_rate=1.0,
            release=f"{PACKAGE}@{VERSION}",
        )

    try:
        for dir_path in [CACHE_DIR, RECORD_DIR]:
            dir_path.mkdir(exist_ok=True)
    except OSError as e:
        logger.error(e)
        sys.exit(1)

    # Although all of our calculations are in UTC, it is useful to know what timezone
    # the local machine is, so that we have a reference for what time the actual
    # log entries were made
    logger.info("Timezone: %s", time.tzname)
    logger.info("UTC time: %s", datetime.now(UTC))

    api_client = v2.ApiClient(
        base_url=config.general.public_url,
        api_key=config.general.api_key,
    )

    legacy_client = v1.ApiClient(
        base_url=config.general.public_url,
        api_key=config.general.api_key,
    )
    wait_for_legacy(legacy_client)

    wait_for_liquidsoap(
        LiquidsoapClient(
            host=config.playout.liquidsoap_host,
            port=config.playout.liquidsoap_port,
        ),
    )

    fetch_queue: Queue[dict[str, Any]] = Queue()
    push_queue: Queue[Events] = Queue()
    # This queue is shared between pypo-fetch and pypo-file, where pypo-file
    # is the consumer. Pypo-fetch will send every schedule it gets to pypo-file
    # and pypo will parse this schedule to determine which file has the highest
    # priority, and retrieve it.
    file_queue: Queue[FileEvents] = Queue()

    liquidsoap = Liquidsoap(
        LiquidsoapClient(
            host=config.playout.liquidsoap_host,
            port=config.playout.liquidsoap_port,
        ),
    )

    PypoFile(file_queue, api_client).start()

    PypoFetch(
        fetch_queue,
        push_queue,
        file_queue,
        LiquidsoapClient(
            host=config.playout.liquidsoap_host,
            port=config.playout.liquidsoap_port,
        ),
        liquidsoap,
        config,
        api_client,
        legacy_client,
    ).start()

    PypoPush(push_queue, liquidsoap, config).start()

    StatsCollectorThread(config, legacy_client).start()

    message_listener = MessageListener(config, fetch_queue)
    message_listener.run_forever()
