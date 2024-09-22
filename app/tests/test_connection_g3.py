# test_with_pytest.py
import pytest
import asyncio

from mock import patch
from app.src.async_stream import AsyncStream
from app.src.gen3.connection_g3 import ConnectionG3
from app.src.gen3.talent import Talent

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



def test_method_calls(patch_async_init, patch_talent_init, patch_healthy, patch_async_close, patch_talent_close):
    spy1 = patch_async_init
    spy2 = patch_talent_init
    spy3 = patch_healthy
    spy4 = patch_async_close
    spy5 = patch_talent_close
    reader = FakeReader()
    writer =  FakeWriter()
    id_str = "id_string"
    addr = ('proxy.local', 10000)
    conn = ConnectionG3(reader, writer, addr,
                        remote_stream= None, server_side=True, id_str=id_str)
    spy1.assert_called_once_with(conn, reader, writer, addr, conn._ifc)
    spy2.assert_called_once_with(conn, True, conn._ifc, id_str)
    conn.healthy()

    spy3.assert_called_once()

    conn.close()
    spy4.assert_called_once()
    spy5.assert_called_once()

