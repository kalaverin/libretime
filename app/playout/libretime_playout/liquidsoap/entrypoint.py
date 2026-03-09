from pathlib import Path

from jinja2 import Environment, PackageLoader

from libretime_playout.config import Config
from libretime_playout.liquidsoap.models import Info, StreamPreferences
from libretime_playout.liquidsoap.utils import quote


here = Path(__file__).parent

templates_loader = PackageLoader(__name__, "templates")
templates = Environment(  # nosec
    loader=templates_loader,
    keep_trailing_newline=True,
)
templates.filters["quote"] = quote


def generate_entrypoint(
    log_filepath: Path | None,
    config: Config,
    preferences: StreamPreferences,
    info: Info,
    version: tuple[int, int, int],
) -> str:
    paths = {}
    paths["lib_filepath"] = here / f"{version[0]}.{version[1]}/ls_script.liq"

    if log_filepath is not None:
        paths["log_filepath"] = log_filepath.resolve()

    return templates.get_template("entrypoint.liq.j2").render(
        config=config.model_copy(),
        preferences=preferences,
        info=info,
        paths=paths,
        version=version,
    )
