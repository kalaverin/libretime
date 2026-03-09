from queue import Queue
from unittest.mock import MagicMock

from playout.config import Config
from playout.player.push import PypoPush


def test_push_thread(config: Config):
    PypoPush(
        Queue(),
        MagicMock(),
        config,
    )
