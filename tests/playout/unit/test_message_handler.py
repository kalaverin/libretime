from queue import Queue

from playout.config import Config
from playout.message_handler import MessageListener


def test_message_listener(config: Config):
    MessageListener(config, Queue())
