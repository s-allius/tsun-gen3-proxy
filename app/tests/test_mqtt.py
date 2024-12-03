# test_with_pytest.py
import pytest
import asyncio
import aiomqtt
import logging

from mock import patch, Mock
from async_stream import AsyncIfcImpl
from singleton import Singleton
from mqtt import Mqtt
from modbus import Modbus
from gen3plus.solarman_v5 import SolarmanV5
from config.config import Config


pytest_plugins = ('pytest_asyncio',)

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
def config_mqtt_conn(test_hostname, test_port):
    Config.act_config = {'mqtt':{'host': test_hostname, 'port': test_port, 'user': '', 'passwd': ''},
                         'ha':{'auto_conf_prefix': 'homeassistant','discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun'}
                        }

@pytest.fixture
def config_no_conn(test_port):
    Config.act_config = {'mqtt':{'host': "", 'port': test_port, 'user': '', 'passwd': ''},
                         'ha':{'auto_conf_prefix': 'homeassistant','discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun'}
                        }

@pytest.fixture
def spy_at_cmd():
    conn = SolarmanV5(('test.local', 1234), server_side=True, client_mode= False, ifc=AsyncIfcImpl())
    conn.node_id = 'inv_2/'
    with patch.object(conn, 'send_at_cmd', wraps=conn.send_at_cmd) as wrapped_conn:
        yield wrapped_conn
    conn.close()

@pytest.fixture
def spy_modbus_cmd():
    conn = SolarmanV5(('test.local', 1234), server_side=True, client_mode= False, ifc=AsyncIfcImpl())
    conn.node_id = 'inv_1/'
    with patch.object(conn, 'send_modbus_cmd', wraps=conn.send_modbus_cmd) as wrapped_conn:
        yield wrapped_conn
    conn.close()

@pytest.fixture
def spy_modbus_cmd_client():
    conn = SolarmanV5(('test.local', 1234), server_side=False, client_mode= False, ifc=AsyncIfcImpl())
    conn.node_id = 'inv_1/'
    with patch.object(conn, 'send_modbus_cmd', wraps=conn.send_modbus_cmd) as wrapped_conn:
        yield wrapped_conn
    conn.close()

def test_native_client(test_hostname, test_port):
    """Sanity check: Make sure the paho-mqtt client can connect to the test
    MQTT server.
    """

    import paho.mqtt.client as mqtt
    import threading

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.loop_start()
    try:
        # Just make sure the client connects successfully
        on_connect = threading.Event()
        c.on_connect = Mock(side_effect=lambda *_: on_connect.set())
        c.connect_async(test_hostname, test_port)
        assert on_connect.wait(10)
    finally:
        c.loop_stop()

@pytest.mark.asyncio
async def test_mqtt_no_config(config_no_conn):
    _ = config_no_conn
    assert asyncio.get_running_loop()

    on_connect =  asyncio.Event()
    async def cb():
        on_connect.set()

    try:
        m = Mqtt(cb)
        assert m.task
        await asyncio.sleep(0)
        assert not on_connect.is_set()
        try:
            await m.publish('homeassistant/status', 'online')
            assert False
        except Exception:
            pass          
    except TimeoutError:
        assert False
    finally:
        await m.close()

@pytest.mark.asyncio
async def test_mqtt_connection(config_mqtt_conn):
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


@pytest.mark.asyncio
async def test_msg_dispatch(config_mqtt_conn, spy_modbus_cmd):
    _ = config_mqtt_conn
    spy = spy_modbus_cmd
    try:
        m = Mqtt(None)
        msg = aiomqtt.Message(topic= 'tsun/inv_1/rated_load', payload= b'2', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_awaited_once_with(Modbus.WRITE_SINGLE_REG, 0x2008, 2, logging.INFO)
        
        spy.reset_mock()
        msg = aiomqtt.Message(topic= 'tsun/inv_1/out_coeff', payload= b'100', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_awaited_once_with(Modbus.WRITE_SINGLE_REG, 0x202c, 1024, logging.INFO)
        
        spy.reset_mock()
        msg = aiomqtt.Message(topic= 'tsun/inv_1/out_coeff', payload= b'50', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_awaited_once_with(Modbus.WRITE_SINGLE_REG, 0x202c, 512, logging.INFO)
    
        spy.reset_mock()
        msg = aiomqtt.Message(topic= 'tsun/inv_1/modbus_read_regs', payload= b'0x3000, 10', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_awaited_once_with(Modbus.READ_REGS, 0x3000, 10, logging.INFO)

        spy.reset_mock()
        msg = aiomqtt.Message(topic= 'tsun/inv_1/modbus_read_inputs', payload= b'0x3000, 10', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_awaited_once_with(Modbus.READ_INPUTS, 0x3000, 10, logging.INFO)

    finally:
        await m.close()

@pytest.mark.asyncio
async def test_msg_dispatch_err(config_mqtt_conn, spy_modbus_cmd):
    _ = config_mqtt_conn
    spy = spy_modbus_cmd
    try:
        m = Mqtt(None)
        # test out of range param
        msg = aiomqtt.Message(topic= 'tsun/inv_1/out_coeff', payload= b'-1', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_not_called()

        # test unknown node_id
        spy.reset_mock()
        msg = aiomqtt.Message(topic= 'tsun/inv_2/out_coeff', payload= b'2', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_not_called()

        # test invalid fload param
        spy.reset_mock()
        msg = aiomqtt.Message(topic= 'tsun/inv_1/out_coeff', payload= b'2, 3', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_not_called()

        spy.reset_mock()
        msg = aiomqtt.Message(topic= 'tsun/inv_1/modbus_read_regs', payload= b'0x3000, 10, 7', qos= 0, retain = False, mid= 0, properties= None)
        await m.dispatch_msg(msg)
        spy.assert_not_called()
    finally:
        await m.close()

@pytest.mark.asyncio
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

@pytest.mark.asyncio
async def test_ha_reconnect(config_mqtt_conn):
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
        await m.close()

@pytest.mark.asyncio
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

@pytest.mark.asyncio
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
