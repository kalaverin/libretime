from typing import Any

from uvicorn.workers import UvicornWorker


class Worker(UvicornWorker):
    CONFIG_KWARGS: dict[str, Any] = {"lifespan": "off"}
