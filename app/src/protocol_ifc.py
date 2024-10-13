from abc import abstractmethod

if __name__ == "app.src.protocol_ifc":
    from app.src.iter_registry import AbstractIterMeta
    from app.src.async_ifc import AsyncIfc
else:  # pragma: no cover
    from iter_registry import AbstractIterMeta
    from async_ifc import AsyncIfc


class ProtocolIfc(metaclass=AbstractIterMeta):
    _registry = []

    @abstractmethod
    def __init__(self, addr, ifc: "AsyncIfc", server_side: bool,
                 client_mode: bool = False, id_str=b''):
        pass  # pragma: no cover

    @abstractmethod
    def close(self):
        pass  # pragma: no cover
