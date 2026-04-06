from os import getenv
from subprocess import CompletedProcess
from typing import Any

from analyzer.pipeline._utils import run_

LIQUIDSOAP = getenv("LIQUIDSOAP_PATH", "liquidsoap")


def _liquidsoap(*args: Any, **kwargs: Any) -> CompletedProcess[str]:
    return run_(LIQUIDSOAP, *args, **kwargs)
