import logging
import os

from pathlib import Path

import click
import sentry_sdk

from sdk.cli import cli_config_options, cli_logging_options
from sdk.config import DEFAULT_ENV_PREFIX
from sdk.logging import setup_logger

from analyzer import PACKAGE, VERSION
from analyzer.config import Config
from analyzer.message_listener import MessageListener
from analyzer.status_reporter import StatusReporter

logger = logging.getLogger(__name__)

DEFAULT_RETRY_QUEUE_FILEPATH = Path("retry_queue")


@click.command(context_settings={"auto_envvar_prefix": DEFAULT_ENV_PREFIX})
@cli_logging_options()
@cli_config_options()
@click.option(
    "--retry-queue-filepath",
    type=click.Path(path_type=Path),
    help="Path to the retry queue file.",
    default=DEFAULT_RETRY_QUEUE_FILEPATH,
)
def cli(
    log_level: str,
    log_filepath: Path | None,
    config_filepath: Path | None,
    retry_queue_filepath: Path,
) -> None:
    """
    Run analyzer.
    """
    setup_logger(log_level, log_filepath)
    config = Config(config_filepath)

    if "SENTRY_DSN" in os.environ:
        logger.info("installing sentry")
        sentry_sdk.init(
            traces_sample_rate=1.0,
            release=f"{PACKAGE}@{VERSION}",
        )

    # Start up the StatusReporter process
    StatusReporter.start_thread(retry_queue_filepath)

    # Start listening for RabbitMQ messages telling us about newly
    # uploaded files. This blocks until we receive a shutdown signal.
    MessageListener(config)

    StatusReporter.stop_thread()
