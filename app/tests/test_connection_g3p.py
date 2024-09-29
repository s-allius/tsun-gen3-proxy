# test_with_pytest.py
import pytest
import asyncio

from itertools import count
from mock import patch
from app.src.singleton import Singleton
from app.src.async_stream import AsyncStream, AsyncIfcImpl, StreamPtr
from app.src.gen3plus.connection_g3p import ConnectionG3PServer
from app.src.gen3plus.solarman_v5 import SolarmanV5


class FakeInverter():
    async def async_publ_mqtt(self) -> None:
        pass  # dummy funcion

    async def async_create_remote(self, inv_prot: str, conn_class) -> None:
        pass  # dummy function

    def __init__ (self):
        self.remote = StreamPtr(None)
        self.local = StreamPtr(None)


@pytest.fixture
def patch_async_init():
    with patch.object(AsyncStream, '__init__', return_value= None) as conn:
        yield conn

@pytest.fixture
def patch_solarman_init():
    with patch.object(SolarmanV5, '__init__') as conn:
        yield conn

@pytest.fixture(scope="module", autouse=True)
def module_init():
    Singleton._instances.clear()
    yield

@pytest.fixture
def patch_healthy():
    with patch.object(AsyncStream, 'healthy') as conn:
        yield conn

@pytest.fixture
def patch_async_close():
    with patch.object(AsyncStream, 'close') as conn:
        yield conn

@pytest.fixture
def patch_solarman_close():
    with patch.object(SolarmanV5, 'close') as conn:
        yield conn

class FakeReader():
    def __init__(self):
        self.on_recv =  asyncio.Event()
    async def read(self, max_len: int):
        await self.on_recv.wait()
        return b''
    def feed_eof(self):
        return


class FakeWriter():
    def write(self, buf: bytes):
        return
    def get_extra_info(self, sel: str):
        if sel == 'peername':
            return 'remote.intern'
        elif sel == 'sockname':
            return 'sock:1234'
        assert False
    def is_closing(self):
        return False
    def close(self):
        return
    async def wait_closed(self):
        return



def test_method_calls(patch_solarman_init, patch_healthy, patch_async_close, patch_solarman_close):
    AsyncIfcImpl._ids = count(5)
    spy2 = patch_solarman_init
    spy3 = patch_healthy
    spy4 = patch_async_close
    spy5 = patch_solarman_close
    reader = FakeReader()
    writer = FakeWriter()
    addr = ('proxy.local', 10000)
    conn = ConnectionG3PServer(FakeInverter(), reader, writer, addr,
                               client_mode=False)
    assert 5 == conn._ifc.get_conn_no()
    spy2.assert_called_once_with(conn, True, False, conn._ifc)
    conn.healthy()

    spy3.assert_called_once()

    conn.close()
    spy4.assert_called_once()
    spy5.assert_called_once()

