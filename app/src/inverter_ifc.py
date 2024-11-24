from abc import abstractmethod
import logging
from asyncio import StreamReader, StreamWriter

from iter_registry import AbstractIterMeta

logger_mqtt = logging.getLogger('mqtt')


class InverterIfc(metaclass=AbstractIterMeta):
    _registry = []

    @abstractmethod
    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 config_id: str, prot_class,
                 client_mode: bool):
        pass  # pragma: no cover

    @abstractmethod
    def __enter__(self):
        pass  # pragma: no cover

    @abstractmethod
    def __exit__(self, exc_type, exc, tb):
        pass  # pragma: no cover

    @abstractmethod
    def healthy(self) -> bool:
        pass  # pragma: no cover

    @abstractmethod
    async def disc(self, shutdown_started=False) -> None:
        pass  # pragma: no cover

    @abstractmethod
    async def create_remote(self) -> None:
        pass  # pragma: no cover
