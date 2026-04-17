from queue import Queue
from unittest.mock import MagicMock

from playout.config import Config
from playout.player.fetch import PypoFetch


def test_fetch_thread(config: Config):
    PypoFetch(
        Queue(),
        Queue(),
        Queue(),
        MagicMock(),
        MagicMock(),
        config,
        MagicMock(),
        MagicMock(),
    )
