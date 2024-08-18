# test_with_pytest.py
import pytest
import asyncio
from unittest.mock import Mock
from app.src.mqtt import Mqtt
from app.src.config import Config
from os import getenv

pytest_plugins = ('pytest_asyncio',)



@pytest.fixture(scope="module")
def test_port():
    return 1883

@pytest.fixture(scope="module")
def test_hostname():
    if getenv("GITHUB_ACTIONS") == "true":
        return 'mqtt'
    else:
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

def test_native_client(test_hostname, test_port):
    """Sanity check: Make sure the paho-mqtt client can connect to the test
    MQTT server.
    """

    import paho.mqtt.client as mqtt
    import threading

    c = mqtt.Client()
    c.loop_start()
    try:
        # Just make sure the client connects successfully
        on_connect = threading.Event()
        c.on_connect = Mock(side_effect=lambda *_: on_connect.set())
        c.connect_async(test_hostname, test_port)
        assert on_connect.wait(5)
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
        await asyncio.sleep(1)
        assert not on_connect.is_set()
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
        # assert 1 == m.ha_restarts
    except TimeoutError:
        assert False
    finally:
        await m.close()
