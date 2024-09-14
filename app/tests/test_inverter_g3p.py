# test_with_pytest.py
import pytest
import asyncio

from mock import patch
from enum import Enum
from app.src.config import Config
from app.src.singleton import Singleton
from app.src.gen3plus.connection_g3p import ConnectionG3P
from app.src.gen3plus.inverter_g3p import InverterG3P
from app.src.gen3plus.infos_g3p import InfosG3P

from app.src.infos import Infos


pytest_plugins = ('pytest_asyncio',)

# initialize the proxy statistics
Infos.static_init()

@pytest.fixture
def config_conn():
    Config.act_config = {'solarman':{'enabled': True, 'host': 'test_cloud.local', 'port': 1234}, 'inverters':{'allow_all':True}}

@pytest.fixture(scope="module", autouse=True)
def module_init():
    Singleton._instances.clear()
    yield

@pytest.fixture
def patch_conn_init():
    with patch.object(ConnectionG3P, '__init__', return_value= None) as conn:
        yield conn

@pytest.fixture
def patch_conn_close():
    with patch.object(ConnectionG3P, 'close') as conn:
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

class TestType(Enum):
    RD_TEST_0_BYTES = 1
    RD_TEST_TIMEOUT = 2
    RD_TEST_EXCEPT = 3


test  = TestType.RD_TEST_0_BYTES

@pytest.fixture
def patch_open_connection():
    async def new_conn(conn):
        await asyncio.sleep(0)
        return FakeReader(), FakeWriter()
    
    def new_open(host: str, port: int):
        global test
        if test == TestType.RD_TEST_TIMEOUT:
            raise ConnectionRefusedError
        elif test == TestType.RD_TEST_EXCEPT:
            raise ValueError("Value cannot be negative") # Compliant
        return new_conn(None)

    with patch.object(asyncio, 'open_connection', new_open) as conn:
        yield conn


def test_method_calls(patch_conn_init, patch_conn_close):
    spy1 = patch_conn_init
    spy2 = patch_conn_close
    reader = FakeReader()
    writer =  FakeWriter()
    addr = ('proxy.local', 10000)
    inverter = InverterG3P(reader, writer, addr, client_mode=False)
    inverter.l_addr = ''
    inverter.r_addr = ''

    spy1.assert_called_once()
    spy1.assert_called_once_with(reader, writer, addr, None, server_side=True, client_mode=False)

    inverter.close()
    spy2.assert_called_once()

@pytest.mark.asyncio
async def test_remote_conn(config_conn, patch_open_connection, patch_conn_close):
    _ = config_conn
    _ = patch_open_connection
    assert asyncio.get_running_loop()

    spy1 = patch_conn_close
    reader = FakeReader()
    writer =  FakeWriter()

    addr = ('proxy.local', 10000)

    inverter = InverterG3P(reader, writer, addr, client_mode=False)
    inverter.l_addr = ''
    inverter.r_addr = ''
    inverter.node_id = 'Test'
    inverter.db = InfosG3P(client_mode= False)
    await inverter.async_create_remote()
    await asyncio.sleep(0)
    assert inverter.remote_stream
    inverter.close()
    spy1.assert_called_once()

@pytest.mark.asyncio
async def test_remote_except(config_conn, patch_open_connection, patch_conn_close):
    _ = config_conn
    _ = patch_open_connection
    assert asyncio.get_running_loop()

    spy1 = patch_conn_close
    reader = FakeReader()
    writer =  FakeWriter()

    addr = ('proxy.local', 10000)
    global test
    test  = TestType.RD_TEST_TIMEOUT

    inverter = InverterG3P(reader, writer, addr, client_mode=False)
    inverter.l_addr = ''
    inverter.r_addr = ''
    inverter.node_id = 'Test'
    inverter.db = InfosG3P(client_mode= False)
    test  = TestType.RD_TEST_TIMEOUT
    await inverter.async_create_remote()
    await asyncio.sleep(0)
    assert inverter.remote_stream==None

    test  = TestType.RD_TEST_EXCEPT
    await inverter.async_create_remote()
    await asyncio.sleep(0)
    assert inverter.remote_stream==None
    inverter.close()
    spy1.assert_called_once()
