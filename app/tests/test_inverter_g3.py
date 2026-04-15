# test_with_pytest.py
import pytest
import asyncio
import sys,gc

from mock import patch
from enum import Enum
from infos import Infos
from cnf.config import Config
from proxy import Proxy
from inverter_base import InverterBase
from singleton import Singleton
from gen3.inverter_g3 import InverterG3
from async_stream import AsyncStream

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

@pytest.mark.asyncio(loop_scope="session")
async def test_method_calls(my_loop, patch_healthy):
    spy = patch_healthy
    reader = FakeReader()
    writer =  FakeWriter()
    InverterBase._registry.clear()

    with InverterG3(reader, writer) as inverter:
        assert inverter.local.stream
        assert inverter.local.ifc
        for inv in InverterBase:
            inv.healthy()
            del inv
        spy.assert_called_once()
    del inverter
    cnt = 0
    for inv in InverterBase:
        cnt += 1
    assert cnt == 0

@pytest.mark.asyncio(loop_scope="session")
async def test_remote_conn(my_loop, config_conn, patch_open_connection):
    _ = config_conn
    _ = patch_open_connection
    assert asyncio.get_running_loop()

    with InverterG3(FakeReader(), FakeWriter()) as inverter:
        await inverter.create_remote()
        await asyncio.sleep(0)
        assert inverter.remote.stream
    del inverter

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

@pytest.mark.asyncio(loop_scope="session")
async def test_remote_except(my_loop, config_conn, patch_open_connection):
    _ = config_conn
    _ = patch_open_connection
    assert asyncio.get_running_loop()

    global test
    test  = MockType.RD_TEST_TIMEOUT

    with InverterG3(FakeReader(), FakeWriter()) as inverter:
        await inverter.create_remote()
        await asyncio.sleep(0)
        assert inverter.remote.stream==None

        test  = MockType.RD_TEST_EXCEPT
        await inverter.create_remote()
        await asyncio.sleep(0)
        assert inverter.remote.stream==None
    del inverter
    test  = MockType.RD_TEST_0_BYTES

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

@pytest.mark.asyncio(loop_scope="session")
async def test_mqtt_publish(my_loop, config_conn, patch_open_connection):
    _ = config_conn
    _ = patch_open_connection
    assert asyncio.get_running_loop()

    Proxy.class_init()

    with InverterG3(FakeReader(), FakeWriter()) as inverter:
        stream = inverter.local.stream
        await inverter.async_publ_mqtt()  # check call with invalid unique_id
        stream._Talent__set_serial_no(serial_no= "123344")

        stream.new_data['inverter'] = True
        stream.db.db['inverter'] = {}
        await inverter.async_publ_mqtt()
        assert stream.new_data['inverter'] == False

        stream.new_data['env'] = True
        stream.db.db['env'] = {}
        await inverter.async_publ_mqtt()
        assert stream.new_data['env'] == False

        Infos.new_stat_data['proxy'] = True
        await inverter.async_publ_mqtt()
        assert Infos.new_stat_data['proxy'] == False

@pytest.mark.asyncio(loop_scope="session")
async def test_mqtt_err(my_loop, config_conn, patch_open_connection, patch_mqtt_err):
    _ = config_conn
    _ = patch_open_connection
    _ = patch_mqtt_err
    assert asyncio.get_running_loop()

    Proxy.class_init()

    with InverterG3(FakeReader(), FakeWriter()) as inverter:
        stream = inverter.local.stream
        stream._Talent__set_serial_no(serial_no= "123344")
        stream.new_data['inverter'] = True
        stream.db.db['inverter'] = {}
        await inverter.async_publ_mqtt()
        assert stream.new_data['inverter'] == True

@pytest.mark.asyncio(loop_scope="session")
async def test_mqtt_except(my_loop, config_conn, patch_open_connection, patch_mqtt_except):
    _ = config_conn
    _ = patch_open_connection
    _ = patch_mqtt_except
    assert asyncio.get_running_loop()

    Proxy.class_init()

    with InverterG3(FakeReader(), FakeWriter()) as inverter:
        stream = inverter.local.stream
        stream._Talent__set_serial_no(serial_no= "123344")

        stream.new_data['inverter'] = True
        stream.db.db['inverter'] = {}
        await inverter.async_publ_mqtt()
        assert stream.new_data['inverter'] == True
