# test_with_pytest.py
import pytest
import asyncio

from mock import patch
from enum import Enum
from app.src.infos import Infos
from app.src.config import Config
from app.src.inverter import Inverter
from app.src.singleton import Singleton
from app.src.gen3.connection_g3 import ConnectionG3Server
from app.src.gen3.inverter_g3 import InverterG3

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

@pytest.fixture
def patch_conn_init():
    with patch.object(ConnectionG3Server, '__init__', return_value= None) as conn:
        yield conn

@pytest.fixture
def patch_conn_close():
    with patch.object(ConnectionG3Server, 'close') as conn:
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
    inverter = InverterG3(reader, writer, addr)
    inverter.l_addr = ''
    inverter.r_addr = ''

    spy1.assert_called_once()
    spy1.assert_called_once_with(inverter, reader, writer, addr, None)

    inverter.close()
    spy2.assert_called_once()

@pytest.mark.asyncio
async def test_remote_conn(config_conn, patch_open_connection, patch_conn_close):
    _ = config_conn
    _ = patch_open_connection
    assert asyncio.get_running_loop()

    spy1 = patch_conn_close

    inverter = InverterG3(FakeReader(), FakeWriter(), ('proxy.local', 10000))
    
    await inverter.async_create_remote()
    await asyncio.sleep(0)
    assert inverter.remote.stream
    inverter.close()
    spy1.assert_called_once()

@pytest.mark.asyncio
async def test_remote_except(config_conn, patch_open_connection, patch_conn_close):
    _ = config_conn
    _ = patch_open_connection
    assert asyncio.get_running_loop()

    spy1 = patch_conn_close
    
    global test
    test  = TestType.RD_TEST_TIMEOUT

    inverter = InverterG3(FakeReader(), FakeWriter(), ('proxy.local', 10000))

    await inverter.async_create_remote()
    await asyncio.sleep(0)
    assert inverter.remote.stream==None

    test  = TestType.RD_TEST_EXCEPT
    await inverter.async_create_remote()
    await asyncio.sleep(0)
    assert inverter.remote.stream==None
    inverter.close()
    spy1.assert_called_once()

@pytest.mark.asyncio
async def test_mqtt_publish(config_conn, patch_open_connection, patch_conn_close):
    _ = config_conn
    _ = patch_open_connection
    assert asyncio.get_running_loop()

    spy1 = patch_conn_close
    
    Inverter.class_init()

    inverter = InverterG3(FakeReader(), FakeWriter(), ('proxy.local', 10000))
    await inverter.async_publ_mqtt()  # check call with invalid unique_id
    inverter._Talent__set_serial_no(serial_no= "123344")
    
    inverter.new_data['inverter'] = True
    inverter.db.db['inverter'] = {}
    await inverter.async_publ_mqtt()
    assert inverter.new_data['inverter'] == False

    inverter.new_data['env'] = True
    inverter.db.db['env'] = {}
    await inverter.async_publ_mqtt()
    assert inverter.new_data['env'] == False

    Infos.new_stat_data['proxy'] = True
    await inverter.async_publ_mqtt()
    assert Infos.new_stat_data['proxy'] == False

    inverter.close()
    spy1.assert_called_once()

@pytest.mark.asyncio
async def test_mqtt_err(config_conn, patch_open_connection, patch_mqtt_err, patch_conn_close):
    _ = config_conn
    _ = patch_open_connection
    _ = patch_mqtt_err
    assert asyncio.get_running_loop()

    spy1 = patch_conn_close
    
    Inverter.class_init()

    inverter = InverterG3(FakeReader(), FakeWriter(), ('proxy.local', 10000))
    inverter._Talent__set_serial_no(serial_no= "123344")
    
    inverter.new_data['inverter'] = True
    inverter.db.db['inverter'] = {}
    await inverter.async_publ_mqtt()
    assert inverter.new_data['inverter'] == True

    inverter.close()
    spy1.assert_called_once()

@pytest.mark.asyncio
async def test_mqtt_except(config_conn, patch_open_connection, patch_mqtt_except, patch_conn_close):
    _ = config_conn
    _ = patch_open_connection
    _ = patch_mqtt_except
    assert asyncio.get_running_loop()

    spy1 = patch_conn_close
    
    Inverter.class_init()

    inverter = InverterG3(FakeReader(), FakeWriter(), ('proxy.local', 10000))
    inverter._Talent__set_serial_no(serial_no= "123344")
    
    inverter.new_data['inverter'] = True
    inverter.db.db['inverter'] = {}
    await inverter.async_publ_mqtt()
    assert inverter.new_data['inverter'] == True

    inverter.close()
    spy1.assert_called_once()
