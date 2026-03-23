import logging
import socket

from pathlib import Path

from typing_extensions import Self

logger = logging.getLogger(__name__)


class InvalidConnection(Exception):
    """
    Call was made with an invalid connection
    """


class LiquidsoapConnection:
    _host: str
    _port: int
    _path: Path | None = None
    _timeout: int

    _sock: socket.socket | None = None
    _eof: bytes = b"END"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 0,
        path: Path | None = None,
        timeout: int = 5,
    ) -> None:
        """
        Create a connection to a Liquidsoap server.

        Args:
            host: Host of the Liquidsoap server. Defaults to "localhost".
            port: Port of the Liquidsoap server. Defaults to 0.
            path: Unix socket path of the Liquidsoap server. If defined, use a unix
                socket instead of the host and port address. Defaults to None.
            timeout: Socket timeout. Defaults to 5.
        """
        self._path = path
        self._host = host
        self._port = port
        self._timeout = timeout

    def address(self) -> str:
        return (
            f"{self._host}:{self._port}"
            if self._path is None
            else str(self._path)
        )

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, _traceback) -> None:
        self.close()

    def connect(self) -> None:
        try:
            logger.debug("connecting to %s", self.address())

            if self._path is not None:
                self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self._sock.settimeout(self._timeout)
                self._sock.connect(str(self._path))
            else:
                self._sock = socket.create_connection(
                    address=(self._host, self._port),
                    timeout=self._timeout,
                )

        except (OSError, ConnectionError):
            self._sock = None
            raise

    def close(self) -> None:
        if self._sock is not None:
            logger.debug("closing connection to %s", self.address())

            try:
                self.write("exit")
                # Reading for clean exit
                while self._sock.recv(2**10):
                    continue

            finally:
                self._sock.close()
                self._sock = None

    def write(self, *messages: str) -> None:
        if self._sock is None:
            raise InvalidConnection

        for message in messages:
            logger.debug("sending %s", message)
            buffer = message.encode(encoding="utf-8")
            buffer += b"\n"

            self._sock.sendall(buffer)

    def read(self) -> str:
        if self._sock is None:
            raise InvalidConnection

        chunks = []
        while True:
            chunk = self._sock.recv(2**10)
            if not chunk:
                break

            eof_index = chunk.find(self._eof)
            if eof_index >= 0:
                chunk = chunk[:eof_index]
                chunks.append(chunk)
                break

            chunks.append(chunk)

        buffer = b"".join(chunks)
        buffer = buffer.replace(b"\r\n", b"\n")
        buffer = buffer.rstrip(b"END")
        buffer = buffer.strip(b"\n")
        message = buffer.decode("utf-8")

        logger.debug("received %s", message)
        return message
