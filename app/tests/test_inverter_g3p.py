# test_with_pytest.py
import pytest
import asyncio

from mock import patch
from enum import Enum
from infos import Infos
from cnf.config import Config
from proxy import Proxy
from inverter_base import InverterBase
from singleton import Singleton
from gen3plus.inverter_g3p import InverterG3P

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
        'solarman':{'enabled': True, 'host': 'test_cloud.local', 'port': 1234}, 'inverters':{'allow_all':True}
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

def test_method_calls(config_conn):
    _ = config_conn
    reader = FakeReader()
    writer =  FakeWriter()
    InverterBase._registry.clear()

    with InverterG3P(reader, writer, client_mode=False) as inverter:
        assert inverter.local.stream
        assert inverter.local.ifc

@pytest.mark.asyncio
async def test_remote_conn(config_conn, patch_open_connection):
    _ = config_conn
    _ = patch_open_connection
    assert asyncio.get_running_loop()

    with InverterG3P(FakeReader(), FakeWriter(), client_mode=False) as inverter:
        await inverter.create_remote()
        await asyncio.sleep(0)
        assert inverter.remote.stream

@pytest.mark.asyncio
async def test_remote_except(config_conn, patch_open_connection):
    _ = config_conn
    _ = patch_open_connection
    assert asyncio.get_running_loop()
    
    global test
    test  = MockType.RD_TEST_TIMEOUT

    with InverterG3P(FakeReader(), FakeWriter(), client_mode=False) as inverter:
        await inverter.create_remote()
        await asyncio.sleep(0)
        assert inverter.remote.stream==None

        test  = MockType.RD_TEST_EXCEPT
        await inverter.create_remote()
        await asyncio.sleep(0)
        assert inverter.remote.stream==None

@pytest.mark.asyncio
async def test_mqtt_publish(config_conn, patch_open_connection):
    _ = config_conn
    _ = patch_open_connection
    assert asyncio.get_running_loop()

    Proxy.class_init()

    with InverterG3P(FakeReader(), FakeWriter(), client_mode=False) as inverter:
        stream = inverter.local.stream
        await inverter.async_publ_mqtt()  # check call with invalid unique_id   
        stream._set_serial_no(snr= 123344)

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

@pytest.mark.asyncio
async def test_mqtt_err(config_conn, patch_open_connection, patch_mqtt_err):
    _ = config_conn
    _ = patch_open_connection
    _ = patch_mqtt_err
    assert asyncio.get_running_loop()

    Proxy.class_init()

    with InverterG3P(FakeReader(), FakeWriter(), client_mode=False) as inverter:
        stream = inverter.local.stream
        stream._set_serial_no(snr= 123344)    
        stream.new_data['inverter'] = True
        stream.db.db['inverter'] = {}
        await inverter.async_publ_mqtt()
        assert stream.new_data['inverter'] == True

@pytest.mark.asyncio
async def test_mqtt_except(config_conn, patch_open_connection, patch_mqtt_except):
    _ = config_conn
    _ = patch_open_connection
    _ = patch_mqtt_except
    assert asyncio.get_running_loop()

    Proxy.class_init()

    with InverterG3P(FakeReader(), FakeWriter(), client_mode=False) as inverter:
        stream = inverter.local.stream
        stream._set_serial_no(snr= 123344)

        stream.new_data['inverter'] = True
        stream.db.db['inverter'] = {}
        await inverter.async_publ_mqtt()
        assert stream.new_data['inverter'] == True
