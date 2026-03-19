from os import walk
from pathlib import Path
from sdk.structlog import configure
from structlog import get_logger

logger = get_logger(__name__)


def main() -> None:
    root = (Path.cwd() / '..' / 'files').resolve()
    for rt, ds, fs in walk(root):

        rt = Path(rt)
        rt.chmod(0o777)

        for d in ds:
            (rt / d).chmod(0o777)

        for f in fs:
            fp = rt / f
            if not fp.is_symlink():
                fp.chmod(0o666)


if __name__ == '__main__':
    configure(level='debug', is_textual=True)
    main()
    logger.info('permitter finished')
