import logging
import sys

from itertools import zip_longest
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError
from yaml import YAMLError, safe_load

from sdk.config._env import EnvLoader

logger = logging.getLogger(__name__)

DEFAULT_ENV_PREFIX = "LIBRETIME"
DEFAULT_CONFIG_FILEPATH = Path("etc/config.yml")


# pylint: disable=too-few-public-methods
class BaseConfig(BaseModel):
    """
    Read and validate the configuration from 'filepath' and os environment.

    :param filepath: yaml configuration file to read from
    :param env_prefix: prefix for the environment variable names
    :param env_delimiter: delimiter for the environment variable names
    :returns: configuration class
    """

    def __init__(
        self,
        path: Path | str | None = None,
        *,
        prefix: str = DEFAULT_ENV_PREFIX,
        delimiter: str = "_",
        **kwargs: Any,
    ) -> None:
        if path is not None:
            path = Path(path)

        env_loader = EnvLoader(
            self.model_json_schema(),
            prefix,
            delimiter,
        )

        values = deep_merge_dict(
            kwargs,
            self.load_from_file(path or DEFAULT_CONFIG_FILEPATH),
            env_loader.load(),
        )

        try:
            super().__init__(**values)

        except ValidationError as error:
            logger.critical(error)
            sys.exit(1)

    def load_from_file(
        self,
        path: Path | None = None,
    ) -> dict[str, Any]:
        if not path:
            logger.warning("no config filepath is provided")
            return {}

        if not path.is_file():
            logger.warning(
                "provided config filepath '%s' is not a file",
                path,
            )
            return {}

        try:
            return safe_load(path.read_text(encoding="utf-8"))

        except YAMLError as exception:
            logger.fatal(
                "config file '%s' is not a valid yaml file: %s",
                path,
                exception,
            )

        return {}


def deep_merge_dict(
    base: dict[str, Any],
    *elements: dict[str, Any],
) -> dict[str, Any]:
    result = base.copy()

    for element in elements:
        for key, value in element.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge_dict(result[key], value)
                    continue

                if isinstance(result[key], list) and isinstance(value, list):
                    result[key] = deep_merge_list(result[key], value)
                    continue

            if value:
                result[key] = value

    return result


def deep_merge_list(base: list[Any], *elements: list[Any]) -> list[Any]:
    result: list[Any] = []
    for element in elements:
        for base_item, next_item in zip_longest(base, element):
            if isinstance(base_item, list) and isinstance(next_item, list):
                result.append(deep_merge_list(base_item, next_item))
                continue

            if isinstance(base_item, dict) and isinstance(next_item, dict):
                result.append(deep_merge_dict(base_item, next_item))
                continue

            if next_item:
                result.append(next_item)

    return result
