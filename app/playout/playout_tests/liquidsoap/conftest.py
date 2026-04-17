from pathlib import Path

from playout.config import EXECUTABLE
from playout.liquidsoap.version import get_liquidsoap_version

LIQ_VERSION = get_liquidsoap_version(Path(EXECUTABLE))
LIQ_VERSION_STR = ".".join(map(str, LIQ_VERSION))
