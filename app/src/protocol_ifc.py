from abc import abstractmethod
import weakref

if __name__ == "app.src.protocol_ifc":
    from app.src.iter_registry import AbstractIterMeta
    from app.src.async_ifc import AsyncIfc
else:  # pragma: no cover
    from iter_registry import AbstractIterMeta
    from async_ifc import AsyncIfc


class ProtocolIfc(metaclass=AbstractIterMeta):

    @abstractmethod
    def __init__(self, addr, ifc: "AsyncIfc", server_side: bool,
                 client_mode: bool = False, id_str=b''):
        pass  # pragma: no cover

    @abstractmethod
    def close(self):
        pass  # pragma: no cover

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


class Test():
    def test_method(self):
        return self


class ProtocolIfcImpl(ProtocolIfc, Test):
    _registry = []

    def __init__(self, addr, ifc: "AsyncIfc", server_side: bool,
                 client_mode: bool = False, id_str=b''):
        self._registry.append(weakref.ref(self))

    def close(self):
        pass  # pragma: no cover
