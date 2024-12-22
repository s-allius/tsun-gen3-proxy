# test_with_pytest.py
import pytest
import asyncio
import gc

from mock import patch
from enum import Enum
from infos import Infos
from cnf.config import Config
from gen3.talent import Talent
from inverter_base import InverterBase
from singleton import Singleton
from async_stream import AsyncStream, AsyncStreamClient

from test_modbus_tcp import patch_mqtt_err, patch_mqtt_except, test_port, test_hostname

pytest_plugins = ('pytest_asyncio',)

# initialize the proxy statistics
Infos.static_init()

@pytest.fixture
def config_conn():
    Config.act_config = {
        'mqtt':{
            'host': test_hostname,
            'port': test_port,
            'user': '',
            'passwd': ''
        },
        'ha':{
            'auto_conf_prefix': 'homeassistant',
            'discovery_prefix': 'homeassistant', 
            'entity_prefix': 'tsun',
            'proxy_node_id': 'test_1',
            'proxy_unique_id': ''
        },
        'tsun':{'enabled': True, 'host': 'test_cloud.local', 'port': 1234}, 'inverters':{'allow_all':True}
    }

@pytest.fixture(scope="module", autouse=True)
def module_init():
    Singleton._instances.clear()
    yield

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
            return ('47.1.2.3', 10000)
        elif sel == 'sockname':
            return 'sock:1234'
        assert False
    def is_closing(self):
        return False
    def close(self):
        return
    async def wait_closed(self):
        return

class MockType(Enum):
    RD_TEST_0_BYTES = 1
    RD_TEST_TIMEOUT = 2
    RD_TEST_EXCEPT = 3


test  = MockType.RD_TEST_0_BYTES

@pytest.fixture
def patch_open_connection():
    async def new_conn(conn):
        await asyncio.sleep(0)
        return FakeReader(), FakeWriter()
    
    def new_open(host: str, port: int):
        global test
        if test == MockType.RD_TEST_TIMEOUT:
            raise ConnectionRefusedError
        elif test == MockType.RD_TEST_EXCEPT:
            raise ValueError("Value cannot be negative") # Compliant
        return new_conn(None)

    with patch.object(asyncio, 'open_connection', new_open) as conn:
        yield conn


@pytest.fixture
def patch_healthy():
    with patch.object(AsyncStream, 'healthy') as conn:
        yield conn

@pytest.fixture
def patch_unhealthy():
    def new_healthy(self):
        return False
    with patch.object(AsyncStream, 'healthy', new_healthy) as conn:
        yield conn
@pytest.fixture
def patch_unhealthy_remote():
    def new_healthy(self):
        return False
    with patch.object(AsyncStreamClient, 'healthy', new_healthy) as conn:
        yield conn

def test_inverter_iter():
    InverterBase._registry.clear()
    cnt = 0
    reader = FakeReader()
    writer =  FakeWriter()

    with InverterBase(reader, writer, 'tsun', Talent) as inverter:
        for inv in InverterBase:
            assert inv == inverter
            cnt += 1
            del inv
    del inverter
    assert cnt == 1
    
    for inv in InverterBase:
        assert False

def test_method_calls(patch_healthy):
    spy = patch_healthy
    InverterBase._registry.clear()
    reader = FakeReader()
    writer =  FakeWriter()

    with InverterBase(reader, writer, 'tsun', Talent) as inverter:
        assert inverter.local.stream
        assert inverter.local.ifc
        # call healthy inside the contexter manager
        for inv in InverterBase:
            assert inv.healthy() 
            del inv
        spy.assert_called_once()

    # outside context manager the health function of AsyncStream is not reachable
    cnt = 0
    for inv in InverterBase:
        assert inv.healthy()
        cnt += 1
        del inv
    assert cnt == 1
    spy.assert_called_once() # counter don't increase and keep one!

    del inverter
    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

def test_unhealthy(patch_unhealthy):
    _ = patch_unhealthy
    InverterBase._registry.clear()
    reader = FakeReader()
    writer =  FakeWriter()

    with InverterBase(reader, writer, 'tsun', Talent) as inverter:
        assert inverter.local.stream
        assert inverter.local.ifc
        # call healthy inside the contexter manager
        assert not inverter.healthy()

    # outside context manager the unhealth AsyncStream is released
    cnt = 0
    for inv in InverterBase:
        assert inv.healthy()  # inverter is healthy again (without the unhealty AsyncStream)
        cnt += 1
        del inv
    assert cnt == 1

    del inverter
    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

def test_unhealthy_remote(patch_unhealthy_remote):
    _ = patch_unhealthy
    InverterBase._registry.clear()
    reader = FakeReader()
    writer =  FakeWriter()

    with InverterBase(reader, writer, 'tsun', Talent) as inverter:
        assert inverter.local.stream
        assert inverter.local.ifc
        # call healthy inside the contexter manager
        assert not inverter.healthy()

    # outside context manager the unhealth AsyncStream is released
    cnt = 0
    for inv in InverterBase:
        assert inv.healthy()  # inverter is healthy again (without the unhealty AsyncStream)
        cnt += 1
        del inv
    assert cnt == 1

    del inverter
    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

@pytest.mark.asyncio
async def test_remote_conn(config_conn, patch_open_connection):
    _ = config_conn
    _ = patch_open_connection
    assert asyncio.get_running_loop()
    reader = FakeReader()
    writer =  FakeWriter()

    with InverterBase(reader, writer, 'tsun', Talent) as inverter:
        await inverter.create_remote()
        await asyncio.sleep(0)
        assert inverter.remote.stream
        assert inverter.remote.ifc
        # call healthy inside the contexter manager
        assert inverter.healthy()

    # call healthy outside the contexter manager (__exit__() was called)
    assert inverter.healthy()
    del inverter

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

@pytest.mark.asyncio
async def test_unhealthy_remote(config_conn, patch_open_connection, patch_unhealthy_remote):
    _ = config_conn
    _ = patch_open_connection
    _ = patch_unhealthy_remote
    assert asyncio.get_running_loop()
    InverterBase._registry.clear()
    reader = FakeReader()
    writer =  FakeWriter()

    with InverterBase(reader, writer, 'tsun', Talent) as inverter:
        assert inverter.local.stream
        assert inverter.local.ifc
        await inverter.create_remote()
        await asyncio.sleep(0)
        assert inverter.remote.stream
        assert inverter.remote.ifc
        assert inverter.local.ifc.healthy()
        assert not inverter.remote.ifc.healthy()
        # call healthy inside the contexter manager
        assert not inverter.healthy()

    # outside context manager the unhealth AsyncStream is released
    cnt = 0
    for inv in InverterBase:
        assert inv.healthy()  # inverter is healthy again (without the unhealty AsyncStream)
        cnt += 1
        del inv
    assert cnt == 1

    del inverter
    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

@pytest.mark.asyncio
async def test_remote_disc(config_conn, patch_open_connection):
    _ = config_conn
    _ = patch_open_connection
    assert asyncio.get_running_loop()
    reader = FakeReader()
    writer =  FakeWriter()

    with InverterBase(reader, writer, 'tsun', Talent) as inverter:
        await inverter.create_remote()
        await asyncio.sleep(0)
        assert inverter.remote.stream
        # call disc inside the contexter manager
        await inverter.disc()
        
    # call disc outside the contexter manager (__exit__() was called)
    await inverter.disc()
    del inverter

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0
