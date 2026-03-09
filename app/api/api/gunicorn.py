from typing import Any, ClassVar

from uvicorn.workers import UvicornWorker


class Worker(UvicornWorker):

    CONFIG_KWARGS: ClassVar[dict[str, Any]] = {"lifespan": "off"}
