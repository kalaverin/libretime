import logging

from subprocess import CalledProcessError, CompletedProcess, run
from typing import Any

logger = logging.getLogger(__name__)


def run_(*args: Any, **kwargs: Any) -> CompletedProcess[str]:
    try:
        return run(
            args,
            check=True,
            capture_output=True,
            text=True,
            **kwargs,
        )

    except OSError as exception:  # executable was not found
        cmd = args[0]
        logger.warning(
            "Failed to run: %s - %s. Is %s installed?",
            cmd,
            exception,
            cmd,
        )
        raise exception

    except CalledProcessError as exception:  # returned an error code
        logger.error(exception)
        raise exception
