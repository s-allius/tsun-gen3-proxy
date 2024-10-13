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
from app.src.inverter_base import InverterBase
from app.src.messages import Message, State
from app.src.proxy import Proxy
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


class FakeReader():
    RD_TEST_0_BYTES = 1
    RD_TEST_TIMEOUT = 2
    RD_TEST_13_BYTES = 3
    RD_TEST_SW_EXCEPT = 4
    RD_TEST_OS_ERROR = 5

    def __init__(self):
        self.on_recv =  asyncio.Event()
        self.test  = self.RD_TEST_0_BYTES

    async def read(self, max_len: int):
        print(f'fakeReader test: {self.test}')
        await self.on_recv.wait()
        if self.test == self.RD_TEST_0_BYTES:
            return b''
        elif self.test == self.RD_TEST_13_BYTES:
            print('fakeReader return 13 bytes')
            self.test = self.RD_TEST_0_BYTES
            return b'test-data-req'
        elif self.test == self.RD_TEST_TIMEOUT:
            raise TimeoutError
        elif self.test == self.RD_TEST_SW_EXCEPT:
            self.test = self.RD_TEST_0_BYTES
            self.unknown_var += 1    
        elif self.test == self.RD_TEST_OS_ERROR:
            self.test = self.RD_TEST_0_BYTES
            raise ConnectionRefusedError

    def feed_eof(self):
        return


class FakeWriter():
    def __init__(self, conn='remote.intern'):
        self.conn = conn
        self.closing = False
    def write(self, buf: bytes):
        return
    async def drain(self):
        await asyncio.sleep(0)
    def get_extra_info(self, sel: str):
        if sel == 'peername':
            return self.conn
        elif sel == 'sockname':
            return 'sock:1234'
        assert False
    def is_closing(self):
        return self.closing
    def close(self):
        self.closing = True
    async def wait_closed(self):
        await asyncio.sleep(0)


@pytest.fixture
def patch_open():
    async def new_conn(conn):
        await asyncio.sleep(0)
        return FakeReader(), FakeWriter(conn)
    
    def new_open(host: str, port: int):
        return new_conn(f'{host}:{port}')

    with patch.object(asyncio, 'open_connection', new_open) as conn:
        yield conn

@pytest.fixture
def patch_open_timeout():
    def new_open(host: str, port: int):
        raise TimeoutError

    with patch.object(asyncio, 'open_connection', new_open) as conn:
        yield conn

@pytest.fixture
def patch_open_value_error():
    def new_open(host: str, port: int):
        raise ValueError

    with patch.object(asyncio, 'open_connection', new_open) as conn:
        yield conn

@pytest.fixture
def patch_open_conn_abort():
    def new_open(host: str, port: int):
        raise ConnectionAbortedError

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
        del inverter

    for _ in InverterBase:
        assert False

    assert Infos.stat['proxy']['Inverter_Cnt'] == 0

@pytest.mark.asyncio
async def test_modbus_no_cnf():
    assert Infos.stat['proxy']['Inverter_Cnt'] == 0
    loop = asyncio.get_event_loop()
    ModbusTcp(loop)
    assert Infos.stat['proxy']['Inverter_Cnt'] == 0

@pytest.mark.asyncio
async def test_modbus_timeout(config_conn, patch_open_timeout):
    _ = config_conn
    _ = patch_open_timeout
    assert asyncio.get_running_loop()
    Proxy.class_init()

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
async def test_modbus_value_err(config_conn, patch_open_value_error):
    _ = config_conn
    _ = patch_open_value_error
    assert asyncio.get_running_loop()
    Proxy.class_init()

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
async def test_modbus_conn_abort(config_conn, patch_open_conn_abort):
    _ = config_conn
    _ = patch_open_conn_abort
    assert asyncio.get_running_loop()
    Proxy.class_init()

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
    assert asyncio.get_running_loop()
    Proxy.class_init()

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
    assert asyncio.get_running_loop()
    Proxy.class_init()

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
    assert asyncio.get_running_loop()
    Proxy.class_init()

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
    assert asyncio.get_running_loop()
    Proxy.class_init()

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
