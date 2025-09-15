# test_with_pytest.py
import pytest
import asyncio
import aiomqtt
import logging
from aiomqtt import MqttError, MessagesIterator
from aiomqtt import Message as AiomqttMessage
from mock import patch, Mock

from async_stream import AsyncIfcImpl
from singleton import Singleton
from mqtt import Mqtt
from modbus import Modbus
from gen3plus.solarman_v5 import SolarmanV5
from cnf.config import Config

NO_MOSQUITTO_TEST = False
'''disable all tests with connections to test.mosquitto.org'''

pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="function", autouse=True)
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

@pytest.fixture(scope="function")
def aiomqtt_mock(monkeypatch):
    recv_que = asyncio.Queue()
        
    async def my_aenter(self):
        return self
    async def my_subscribe(self, *arg):
        return
    async def my_anext(self):
        return await recv_que.get()
    async def my_receive(self, topic: str, payload: bytes):
        msg = AiomqttMessage(topic, payload,qos=0, retain=False, mid=0, properties=None)
        await recv_que.put(msg)
        await asyncio.sleep(0)  # dispath the msg

    monkeypatch.setattr(aiomqtt.Client, "__aenter__", my_aenter)
    monkeypatch.setattr(aiomqtt.Client, "subscribe", my_subscribe)
    monkeypatch.setattr(MessagesIterator, "__anext__", my_anext)
    monkeypatch.setattr(Mqtt, "receive", my_receive, False)

@pytest.fixture
def config_mqtt_conn(test_hostname, test_port):
    Config.act_config = {'mqtt':{'host': test_hostname, 'port': test_port, 'user': '', 'passwd': ''},
                         'ha':{'auto_conf_prefix': 'homeassistant','discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun'}
                        }

@pytest.fixture
def config_no_conn(test_port):
    Config.act_config = {'mqtt':{'host': "", 'port': test_port, 'user': '', 'passwd': ''},
                         'ha':{'auto_conf_prefix': 'homeassistant','discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun'}
                        }
    Config.def_config = {}

@pytest.fixture
def config_def_conn(test_port):
    Config.act_config = {'mqtt':{'host': "unknown_url", 'port': test_port, 'user': '', 'passwd': ''},
                         'ha':{'auto_conf_prefix': 'homeassistant','discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun'}
                        }
    Config.def_config = Config.act_config

@pytest.fixture
def spy_at_cmd():
    conn = SolarmanV5(None, ('test.local', 1234), server_side=True, client_mode= False, ifc=AsyncIfcImpl())
    conn.node_id = 'inv_2/'
    with patch.object(conn, 'send_at_cmd', wraps=conn.send_at_cmd) as wrapped_conn:
        yield wrapped_conn
    conn.close()

@pytest.fixture
def spy_modbus_cmd():
    conn = SolarmanV5(None, ('test.local', 1234), server_side=True, client_mode= False, ifc=AsyncIfcImpl())
    conn.node_id = 'inv_1/'
    with patch.object(conn, 'send_modbus_cmd', wraps=conn.send_modbus_cmd) as wrapped_conn:
        yield wrapped_conn
    conn.close()

@pytest.fixture
def spy_modbus_cmd_client():
    conn = SolarmanV5(None, ('test.local', 1234), server_side=False, client_mode= False, ifc=AsyncIfcImpl())
    conn.node_id = 'inv_1/'
    with patch.object(conn, 'send_modbus_cmd', wraps=conn.send_modbus_cmd) as wrapped_conn:
        yield wrapped_conn
    conn.close()

@pytest.fixture
def spy_dcu_cmd():
    conn = SolarmanV5(None, ('test.local', 1234), server_side=True, client_mode= False, ifc=AsyncIfcImpl())
    conn.node_id = 'inv_3/'
    with patch.object(conn, 'send_dcu_cmd', wraps=conn.send_dcu_cmd) as wrapped_conn:
        yield wrapped_conn
    conn.close()

def test_native_client(test_hostname, test_port):
    """Sanity check: Make sure the paho-mqtt client can connect to the test
    MQTT server. Otherwise the test set NO_MOSQUITTO_TEST to True and disable
    all test cases which depends on the test.mosquitto.org server
    """
    global NO_MOSQUITTO_TEST
    if NO_MOSQUITTO_TEST:
        pytest.skip('skipping, since Mosquitto is not reliable at the moment')

    import paho.mqtt.client as mqtt
    import threading

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.loop_start()
    try:
        # Just make sure the client connects successfully
        on_connect = threading.Event()
        c.on_connect = Mock(side_effect=lambda *_: on_connect.set())
        c.connect_async(test_hostname, test_port)
        if not on_connect.wait(3):
            NO_MOSQUITTO_TEST = True  # skip all mosquitto tests
            pytest.skip('skipping, since Mosquitto is not reliable at the moment')
    finally:
        c.loop_stop()

@pytest.mark.asyncio(loop_scope="session")
async def test_mqtt_connection(config_mqtt_conn):
    if NO_MOSQUITTO_TEST:
        pytest.skip('skipping, since Mosquitto is not reliable at the moment')

    _ = config_mqtt_conn
    assert asyncio.get_running_loop()

    on_connect =  asyncio.Event()
    async def cb():
        on_connect.set()

    try:
        m = Mqtt(cb)
        assert m.task
        assert await asyncio.wait_for(on_connect.wait(), 5)
        # await asyncio.sleep(1)
        assert 0 == m.ha_restarts
        await m.publish('homeassistant/status', 'online')
    except TimeoutError:
        assert False
    finally:
        await m.close()
        await m.publish('homeassistant/status', 'online')

@pytest.mark.asyncio(loop_scope="session")
async def test_ha_reconnect(config_mqtt_conn):
    if NO_MOSQUITTO_TEST:
        pytest.skip('skipping, since Mosquitto is not reliable at the moment')

    _ = config_mqtt_conn
    on_connect =  asyncio.Event()
    async def cb():
        on_connect.set()

    try:
        m = Mqtt(cb)
        msg = aiomqtt.Message(topic= 'homeassistant/status', payload= b'offline', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        assert not on_connect.is_set()

        msg = aiomqtt.Message(topic= 'homeassistant/status', payload= b'online', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        assert on_connect.is_set()

    finally:
        assert m.received == 2
        await m.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_mqtt_no_config(config_no_conn, monkeypatch):
    _ = config_no_conn
    assert asyncio.get_running_loop()

    on_connect =  asyncio.Event()
    async def cb():
        on_connect.set()
    async def my_publish(*args):
        return

    monkeypatch.setattr(aiomqtt.Client, "publish", my_publish)

    try:
        m = Mqtt(cb)
        assert m.task
        await asyncio.sleep(0)
        assert not on_connect.is_set()
        try:
            await m.publish('homeassistant/status', 'online')
            assert m.published == 1
        except Exception:
            assert False          
    except TimeoutError:
        assert False
    finally:
        await m.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_mqtt_except_no_config(config_no_conn, monkeypatch, caplog):
    _ = config_no_conn

    assert asyncio.get_running_loop()

    async def my_aenter(self):
        raise MqttError('TestException') from None
    
    monkeypatch.setattr(aiomqtt.Client, "__aenter__", my_aenter)

    LOGGER = logging.getLogger("mqtt")
    LOGGER.propagate = True
    LOGGER.setLevel(logging.INFO)

    with caplog.at_level(logging.INFO):
        m = Mqtt(None)
        assert m.task
        await asyncio.sleep(0)
        try:
            await m.publish('homeassistant/status', 'online')
            assert False
        except MqttError:
            pass
        except Exception:
            assert False          
        finally:
            await m.close()
    assert 'Connection lost; Reconnecting in 5 seconds' in caplog.text

@pytest.mark.asyncio(loop_scope="session")
async def test_mqtt_except_def_config(config_def_conn, monkeypatch, caplog):
    _ = config_def_conn

    assert asyncio.get_running_loop()

    on_connect =  asyncio.Event()
    async def cb():
        on_connect.set()

    async def my_aenter(self):
        raise MqttError('TestException') from None
    
    monkeypatch.setattr(aiomqtt.Client, "__aenter__", my_aenter)

    LOGGER = logging.getLogger("mqtt")
    LOGGER.propagate = True
    LOGGER.setLevel(logging.INFO)

    with caplog.at_level(logging.INFO):
        m = Mqtt(cb)
        assert m.task
        await asyncio.sleep(0)
        assert not on_connect.is_set()
        try:
            await m.publish('homeassistant/status', 'online')
            assert False
        except MqttError:
            pass
        except Exception:
            assert False          
        finally:
            await m.close()
    assert 'MQTT is unconfigured; Check your config.toml!' in caplog.text

@pytest.mark.asyncio(loop_scope="session")
async def test_mqtt_dispatch(config_mqtt_conn, aiomqtt_mock, spy_modbus_cmd):
    _ = config_mqtt_conn
    _ = aiomqtt_mock
    spy = spy_modbus_cmd
    try:
        m = Mqtt(None)
        assert m.ha_restarts == 0
        await m.receive('homeassistant/status', b'online')  # send the message
        assert m.ha_restarts == 1

        await m.receive(topic= 'tsun/inv_1/rated_load', payload= b'2')
        spy.assert_called_once_with(Modbus.WRITE_SINGLE_REG, 0x2008, 2, logging.INFO)

        spy.reset_mock()
        await m.receive(topic= 'tsun/inv_1/out_coeff', payload= b'100')
        spy.assert_called_once_with(Modbus.WRITE_SINGLE_REG, 0x202c, 1024, logging.INFO)
        
        spy.reset_mock()
        await m.receive(topic= 'tsun/inv_1/out_coeff', payload= b'50')
        spy.assert_called_once_with(Modbus.WRITE_SINGLE_REG, 0x202c, 512, logging.INFO)
    
        spy.reset_mock()
        await m.receive(topic= 'tsun/inv_1/modbus_read_regs', payload= b'0x3000, 10')
        spy.assert_called_once_with(Modbus.READ_REGS, 0x3000, 10, logging.INFO)

        spy.reset_mock()
        await m.receive(topic= 'tsun/inv_1/modbus_read_inputs', payload= b'0x3000, 10')
        spy.assert_called_once_with(Modbus.READ_INPUTS, 0x3000, 10, logging.INFO)

        # test dispatching with empty mapping table
        m.topic_defs.clear()
        spy.reset_mock()
        await m.receive(topic= 'tsun/inv_1/modbus_read_inputs', payload= b'0x3000, 10')
        spy.assert_not_called()

        # test dispatching with incomplete mapping table - invalid fnc defined
        m.topic_defs.append(
            {'prefix': 'entity_prefix', 'topic': '/+/modbus_read_inputs',
             'full_topic': 'tsun/+/modbus_read_inputs', 'fnc': 'addr'}
        )
        spy.reset_mock()
        await m.receive(topic= 'tsun/inv_1/modbus_read_inputs', payload= b'0x3000, 10')
        spy.assert_not_called()

    except MqttError:
        assert False
    except Exception:
        assert False          
    finally:
        await m.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_mqtt_dispatch_cb(config_mqtt_conn, aiomqtt_mock):
    _ = config_mqtt_conn
    _ = aiomqtt_mock

    on_connect =  asyncio.Event()
    async def cb():
        on_connect.set()
    try:
        m = Mqtt(cb)
        assert m.ha_restarts == 0
        await m.receive('homeassistant/status', b'online')  # send the message
        assert on_connect.is_set()
        assert m.ha_restarts == 1

    except MqttError:
        assert False
    except Exception:
        assert False          
    finally:
        await m.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_mqtt_dispatch_err(config_mqtt_conn, aiomqtt_mock, spy_modbus_cmd, caplog):
    _ = config_mqtt_conn
    _ = aiomqtt_mock
    spy = spy_modbus_cmd

    LOGGER = logging.getLogger("mqtt")
    LOGGER.propagate = True
    LOGGER.setLevel(logging.INFO)

    try:
        m = Mqtt(None)

        # test out of range param
        await m.receive(topic= 'tsun/inv_1/out_coeff', payload= b'-1')
        spy.assert_not_called()

        # test unknown node_id
        await m.receive(topic= 'tsun/inv_2/out_coeff', payload= b'2')
        spy.assert_not_called()

        # test invalid fload param
        await m.receive(topic= 'tsun/inv_1/out_coeff', payload= b'2, 3')
        spy.assert_not_called()
    
        await m.receive(topic= 'tsun/inv_1/modbus_read_regs', payload= b'0x3000, 10, 7')
        spy.assert_not_called()

        await m.receive(topic= 'tsun/inv_1/dcu_power', payload= b'100W')
        spy.assert_not_called()

        with caplog.at_level(logging.INFO):
            msg = aiomqtt.Message(topic= 'tsun/inv_1/out_coeff', payload= b'2', qos= 0, retain = False, mid= 0, properties= None)
            for _ in m.each_inverter(msg, "addr"):
                pass  # do nothing here
        assert 'Cmd not supported by: inv_1/' in caplog.text
    except MqttError:
        assert False
    except Exception:
        assert False          
    finally:
        await m.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_msg_ignore_client_conn(config_mqtt_conn, spy_modbus_cmd_client):
    '''don't call function if connnection is not in server mode'''
    _ = config_mqtt_conn
    spy = spy_modbus_cmd_client
    try:
        m = Mqtt(None)
        msg = aiomqtt.Message(topic= 'tsun/inv_1/rated_load', payload= b'2', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_not_called()
    finally:
        await m.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_ignore_unknown_func(config_mqtt_conn):
    '''don't dispatch for unknwon function names'''
    _ = config_mqtt_conn
    try:
        m = Mqtt(None)
        msg = aiomqtt.Message(topic= 'tsun/inv_1/rated_load', payload= b'2', qos= 0, retain = False, mid= 0, properties= None)
        for _ in m.each_inverter(msg, 'unkown_fnc'):
            assert False
    finally:
        await m.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_at_cmd_dispatch(config_mqtt_conn, spy_at_cmd):
    _ = config_mqtt_conn
    spy = spy_at_cmd
    try:
        m = Mqtt(None)
        msg = aiomqtt.Message(topic= 'tsun/inv_2/at_cmd', payload= b'AT+', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_awaited_once_with('AT+')
        
    finally:
        await m.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_dcu_dispatch(config_mqtt_conn, spy_dcu_cmd):
    _ = config_mqtt_conn
    spy = spy_dcu_cmd
    try:
        m = Mqtt(None)
        msg = aiomqtt.Message(topic= 'tsun/inv_3/dcu_power', payload= b'100.0', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_called_once_with(b'\x01\x01\x06\x01\x00\x01\x03\xe8')
    finally:
        await m.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_dcu_inv_value(config_mqtt_conn, spy_dcu_cmd):
    _ = config_mqtt_conn
    spy = spy_dcu_cmd
    try:
        m = Mqtt(None)
        msg = aiomqtt.Message(topic= 'tsun/inv_3/dcu_power', payload= b'99.9', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_not_called()

        msg = aiomqtt.Message(topic= 'tsun/inv_3/dcu_power', payload= b'800.1', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_not_called()
    finally:
        await m.close()
