import logging
import mimetypes

from datetime import datetime
from pathlib import Path
from re import match

logger = logging.getLogger(__name__)

here = Path(__file__).parent


def seconds_between(base: datetime, target: datetime) -> float:
    """
    Get seconds between base and target datetime.

    Return 0 if target is older than base.
    """
    return max(0, (target - base).total_seconds())


mimetypes.init([str(here / "mime.types")])


def mime_guess_extension(mime: str) -> str:
    extension = (mimetypes.guess_extension(mime, strict=False) or "").lstrip(
        ".",
    )

    if m := match(r"^([0-9a-z]+)", extension):
        return "." + m.group(1)

    if not extension:
        logger.warning(
            "could not determine file extension from mime: %s",
            mime,
        )
        return ""

    return "." + extension
