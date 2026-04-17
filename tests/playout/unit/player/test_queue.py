from queue import Queue
from unittest.mock import MagicMock

from playout.player.queue import PypoLiqQueue


def test_queue_thread():
    PypoLiqQueue(Queue(), MagicMock())
