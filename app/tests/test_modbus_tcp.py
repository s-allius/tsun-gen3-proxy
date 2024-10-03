# test_with_pytest.py
import pytest
import asyncio
from aiomqtt import MqttCodeError

from mock import patch
from enum import Enum
from app.src.singleton import Singleton
from app.src.config import Config
from app.src.infos import Infos
from app.src.mqtt import Mqtt
from app.src.messages import Message, State
from app.src.inverter import Inverter
from app.src.modbus_tcp import ModbusConn, ModbusTcp


pytest_plugins = ('pytest_asyncio',)

# initialize the proxy statistics
Infos.static_init()

@pytest.fixture(scope="module", autouse=True)
def module_init():
    Singleton._instances.clear()
    yield

@pytest.fixture(scope="module")
def test_port():
    return 1883

@pytest.fixture(scope="module")
def test_hostname():
    # if getenv("GITHUB_ACTIONS") == "true":
    #     return 'mqtt'
    # else:
        return 'test.mosquitto.org'

@pytest.fixture
def config_conn(test_hostname, test_port):
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
                        'inverters':{
                            'allow_all': True,
                            "R170000000000001":{
                                'node_id': 'inv_1'
                            },
                            "Y170000000000001":{
                                'node_id': 'inv_2',
                                'monitor_sn': 2000000000,
                                'modbus_polling': True,
                                'suggested_area': "",
                                'sensor_list': 0x2b0,
                                'client_mode':{
                                    'host': '192.168.0.1', 
                                    'port': 8899
                                }  
                            }
                        }
    }


class TestType(Enum):
    RD_TEST_0_BYTES = 1
    RD_TEST_TIMEOUT = 2


test  = TestType.RD_TEST_0_BYTES


class FakeReader():
    def __init__(self):
        self.on_recv =  asyncio.Event()
    async def read(self, max_len: int):
        await self.on_recv.wait()
        if test == TestType.RD_TEST_0_BYTES:
            return b''
        elif test == TestType.RD_TEST_TIMEOUT:
            raise TimeoutError
    def feed_eof(self):
        return


class FakeWriter():
    def __init__(self, conn='remote.intern'):
        self.conn = conn
    def write(self, buf: bytes):
        return
    def get_extra_info(self, sel: str):
        if sel == 'peername':
            return self.conn
        elif sel == 'sockname':
            return 'sock:1234'
        assert False
    def is_closing(self):
        return False
    def close(self):
        return
    async def wait_closed(self):
        return


@pytest.fixture
def patch_open():
    async def new_conn(conn):
        await asyncio.sleep(0)
        return FakeReader(), FakeWriter(conn)
    
    def new_open(host: str, port: int):
        global test
        if test == TestType.RD_TEST_TIMEOUT:
            raise TimeoutError
        return new_conn(f'{host}:{port}')

    with patch.object(asyncio, 'open_connection', new_open) as conn:
        yield conn

@pytest.fixture
def patch_no_mqtt():
    with patch.object(Mqtt, 'publish') as conn:
        yield conn

@pytest.fixture
def patch_mqtt_err():
    def new_publish(self, key, data):
        raise MqttCodeError(None)

    with patch.object(Mqtt, 'publish', new_publish) as conn:
        yield conn

@pytest.fixture
def patch_mqtt_except():
    def new_publish(self, key, data):
        raise ValueError("Test")

    with patch.object(Mqtt, 'publish', new_publish) as conn:
        yield conn

@pytest.mark.asyncio
async def test_modbus_conn(patch_open):
    _ = patch_open
    assert Infos.stat['proxy']['Inverter_Cnt'] == 0

    async with ModbusConn('test.local', 1234) as inverter:
        stream = inverter.local.stream
        assert stream.node_id == 'G3P'
        assert stream.addr == ('test.local:1234')
        assert type(stream.ifc._reader) is FakeReader
        assert type(stream.ifc._writer) is FakeWriter
        assert Infos.stat['proxy']['Inverter_Cnt'] == 1
    
    assert Infos.stat['proxy']['Inverter_Cnt'] == 0

@pytest.mark.asyncio
async def test_modbus_no_cnf():
    assert Infos.stat['proxy']['Inverter_Cnt'] == 0
    loop = asyncio.get_event_loop()
    ModbusTcp(loop)
    assert Infos.stat['proxy']['Inverter_Cnt'] == 0

@pytest.mark.asyncio
async def test_modbus_cnf1(config_conn, patch_open):
    _ = config_conn
    _ = patch_open
    global test
    assert asyncio.get_running_loop()
    Inverter.class_init()
    test = TestType.RD_TEST_TIMEOUT

    assert Infos.stat['proxy']['Inverter_Cnt'] == 0
    loop = asyncio.get_event_loop()
    ModbusTcp(loop)
    await asyncio.sleep(0.01)
    for m in Message:
        if (m.node_id == 'inv_2'):
            assert False
        
    await asyncio.sleep(0.01)
    assert Infos.stat['proxy']['Inverter_Cnt'] == 0

@pytest.mark.asyncio
async def test_modbus_cnf2(config_conn, patch_no_mqtt, patch_open):
    _ = config_conn
    _ = patch_open
    _ = patch_no_mqtt
    global test
    assert asyncio.get_running_loop()
    Inverter.class_init()
    test = TestType.RD_TEST_0_BYTES

    assert Infos.stat['proxy']['Inverter_Cnt'] == 0
    ModbusTcp(asyncio.get_event_loop())
    await asyncio.sleep(0.01)
    test = 0
    for m in Message:
        if (m.node_id == 'inv_2'):
            test += 1
            assert Infos.stat['proxy']['Inverter_Cnt'] == 1
            m.shutdown_started = True
            m.ifc._reader.on_recv.set()
            del m
        
    assert 1 == test
    await asyncio.sleep(0.01)
    assert Infos.stat['proxy']['Inverter_Cnt'] == 0

@pytest.mark.asyncio
async def test_modbus_cnf3(config_conn, patch_no_mqtt, patch_open):
    _ = config_conn
    _ = patch_open
    _ = patch_no_mqtt
    global test
    assert asyncio.get_running_loop()
    Inverter.class_init()
    test = TestType.RD_TEST_0_BYTES

    assert Infos.stat['proxy']['Inverter_Cnt'] == 0
    ModbusTcp(asyncio.get_event_loop(), tim_restart= 0)
    await asyncio.sleep(0.01)
    test = 0
    for m in Message:
        if (m.node_id == 'inv_2'):
            assert Infos.stat['proxy']['Inverter_Cnt'] == 1
            test += 1
            if test == 1:
                m.shutdown_started = False
                m.ifc._reader.on_recv.set()
                await asyncio.sleep(0.1)
                assert m.state == State.closed
                await asyncio.sleep(0.1)
            else:
                m.shutdown_started = True
                m.ifc._reader.on_recv.set()
                del m

    assert 2 == test
    await asyncio.sleep(0.01)
    assert Infos.stat['proxy']['Inverter_Cnt'] == 0

@pytest.mark.asyncio
async def test_mqtt_err(config_conn, patch_mqtt_err, patch_open):
    _ = config_conn
    _ = patch_open
    _ = patch_mqtt_err
    global test
    assert asyncio.get_running_loop()
    Inverter.class_init()
    test = TestType.RD_TEST_0_BYTES

    assert Infos.stat['proxy']['Inverter_Cnt'] == 0
    ModbusTcp(asyncio.get_event_loop(), tim_restart= 0)
    await asyncio.sleep(0.01)
    test = 0
    for m in Message:
        if (m.node_id == 'inv_2'):
            assert Infos.stat['proxy']['Inverter_Cnt'] == 1
            test += 1
            if test == 1:
                m.shutdown_started = False
                m.ifc._reader.on_recv.set()
                await asyncio.sleep(0.1)
                assert m.state == State.closed
                await asyncio.sleep(0.1)
                await asyncio.sleep(0.1)
            else:
                m.shutdown_started = True
                m.ifc._reader.on_recv.set()
                del m

    await asyncio.sleep(0.01)
    assert Infos.stat['proxy']['Inverter_Cnt'] == 0

@pytest.mark.asyncio
async def test_mqtt_except(config_conn, patch_mqtt_except, patch_open):
    _ = config_conn
    _ = patch_open
    _ = patch_mqtt_except
    global test
    assert asyncio.get_running_loop()
    Inverter.class_init()
    test = TestType.RD_TEST_0_BYTES

    assert Infos.stat['proxy']['Inverter_Cnt'] == 0
    ModbusTcp(asyncio.get_event_loop(), tim_restart= 0)
    await asyncio.sleep(0.01)
    test = 0
    for m in Message:
        if (m.node_id == 'inv_2'):
            assert Infos.stat['proxy']['Inverter_Cnt'] == 1
            test += 1
            if test == 1:
                m.shutdown_started = False
                m.ifc._reader.on_recv.set()
                await asyncio.sleep(0.1)
                assert m.state == State.closed
                await asyncio.sleep(0.1)
            else:
                m.shutdown_started = True
                m.ifc._reader.on_recv.set()
                del m

    await asyncio.sleep(0.01)
    assert Infos.stat['proxy']['Inverter_Cnt'] == 0
