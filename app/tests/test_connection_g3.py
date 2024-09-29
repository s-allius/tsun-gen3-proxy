# test_with_pytest.py
import pytest
import asyncio

from itertools import count
from mock import patch
from app.src.async_stream import StreamPtr
from app.src.async_stream import AsyncStream, AsyncStreamServer, AsyncIfcImpl
from app.src.gen3.connection_g3 import ConnectionG3
from app.src.gen3.talent import Talent


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
    with patch.object(AsyncStream, '__init__') as conn:
        yield conn

@pytest.fixture
def patch_talent_init():
    with patch.object(Talent, '__init__') as conn:
        yield conn

@pytest.fixture
def patch_healthy():
    with patch.object(AsyncStream, 'healthy') as conn:
        yield conn

@pytest.fixture
def patch_async_close():
    with patch.object(AsyncStream, 'close') as conn:
        yield conn

@pytest.fixture
def patch_talent_close():
    with patch.object(Talent, 'close') as conn:
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



def test_method_calls(patch_healthy, patch_async_close):
    AsyncIfcImpl._ids = count(5)
    spy3 = patch_healthy
    spy4 = patch_async_close
    reader = FakeReader()
    writer = FakeWriter()
    id_str = "id_string"
    addr = ('proxy.local', 10000)
    inv = FakeInverter()
    ifc = AsyncStreamServer(reader, writer,
                            inv.async_publ_mqtt,
                            inv.async_create_remote,
                            inv.remote)

    conn = ConnectionG3(addr, ifc, server_side=True, id_str=id_str)
    assert 5 == conn.conn_no
    assert 5 == conn.ifc.get_conn_no()
    conn.healthy()

    spy3.assert_called_once()

    conn.close()
    spy4.assert_called_once()
