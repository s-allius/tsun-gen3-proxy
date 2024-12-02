from abc import abstractmethod

from async_ifc import AsyncIfc
from iter_registry import AbstractIterMeta


class ProtocolIfc(metaclass=AbstractIterMeta):
    _registry = []

    @abstractmethod
    def __init__(self, addr, ifc: "AsyncIfc", server_side: bool,
                 client_mode: bool = False, id_str=b''):
        pass  # pragma: no cover

    @abstractmethod
    def close(self):
        pass  # pragma: no cover
