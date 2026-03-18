import logging
import os

from pathlib import Path

import click

from api_client.v2 import ApiClient
from sdk.cli import cli_config_options, cli_logging_options
from sdk.config import DEFAULT_ENV_PREFIX
from sdk.logging import setup_logger

from playout.config import Config
from playout.liquidsoap.entrypoint import generate_entrypoint
from playout.liquidsoap.models import Info, StreamPreferences
from playout.liquidsoap.version import get_liquidsoap_version

logger = logging.getLogger(__name__)

here = Path(__file__).parent


@click.command(context_settings={"auto_envvar_prefix": DEFAULT_ENV_PREFIX})
@cli_logging_options()
@cli_config_options()
def cli(
    log_level: str,
    log_filepath: Path | None,
    config_filepath: Path | None,
):
    """
    Run liquidsoap.
    """
    setup_logger(log_level, log_filepath)
    config = Config(config_filepath)

    api_client = ApiClient(
        base_url=config.general.public_url,
        api_key=config.general.api_key,
    )

    version = get_liquidsoap_version(config.liquidsoap.executable)

    if not sum(version):
        logger.warning("empty liquidsoap version")

    info = Info(**api_client.get_info().json())
    preferences = StreamPreferences(
        **api_client.get_stream_preferences().json(),
    )

    entrypoint_filepath = Path.cwd() / "radio.liq"
    entrypoint_filepath.write_text(
        generate_entrypoint(
            log_filepath,
            config,
            preferences,
            info,
            version,
        ),
        encoding="utf-8",
    )

    exec_args = [
        str(config.liquidsoap.executable),
        "libretime-liquidsoap",
        "--no-stdlib",
        "--verbose",
        str(entrypoint_filepath),
    ]
    if log_level == "debug":
        exec_args.append("--debug")

    logger.debug(
        "liquidsoap %s using script: %s",
        version,
        entrypoint_filepath,
    )
    os.execl(*exec_args)
