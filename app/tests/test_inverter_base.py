# test_with_pytest.py
import pytest
import asyncio
import sys,gc

from mock import patch
from enum import Enum
from app.src.infos import Infos
from app.src.config import Config
from app.src.gen3.talent import Talent
from app.src.inverter_base import InverterBase
from app.src.singleton import Singleton
from app.src.protocol_ifc import ProtocolIfcImpl
from app.src.async_stream import AsyncStream, AsyncIfcImpl

from app.tests.test_modbus_tcp import patch_mqtt_err, patch_mqtt_except, test_port, test_hostname

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


@pytest.fixture
def patch_healthy():
    with patch.object(AsyncStream, 'healthy') as conn:
        yield conn

def test_protocol_iter():
    ProtocolIfcImpl._registry.clear()
    cnt = 0
    ifc = AsyncIfcImpl()
    prot = ProtocolIfcImpl(('test.intern', 123), ifc, True)
    for p in ProtocolIfcImpl:
        assert p == prot
        cnt += 1
        del p
    del prot
    assert cnt == 1
    for p in ProtocolIfcImpl:
        assert False

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
        # inverter.healthy()
        for inv in InverterBase:
            inv.healthy()
            del inv
        spy.assert_called_once()
    del inverter
    cnt = 0
    for inv in InverterBase:
        cnt += 1
    assert cnt == 0
