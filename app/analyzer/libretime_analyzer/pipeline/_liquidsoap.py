from os import getenv

from libretime_analyzer.pipeline._utils import run_


LIQUIDSOAP = getenv("LIQUIDSOAP_PATH", "liquidsoap")


def _liquidsoap(*args, **kwargs):
    return run_(LIQUIDSOAP, *args, **kwargs)
