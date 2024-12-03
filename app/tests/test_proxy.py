# test_with_pytest.py
import pytest
import asyncio
import aiomqtt
import logging

from mock import patch, Mock
from singleton import Singleton
from proxy import Proxy
from mqtt import Mqtt
from gen3plus.solarman_v5 import SolarmanV5
from config.config import Config


pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="module", autouse=True)
def module_init():
    def new_init(cls, cb_mqtt_is_up):
        pass  # empty test methos

    Singleton._instances.clear()
    with patch.object(Mqtt, '__init__', new_init):
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
                        'inverters': {
                            'allow_all': True,
                            "R170000000000001":{
                                'node_id': 'inv_1'
                            }
                        }
    }

@pytest.mark.asyncio
async def test_inverter_cb(config_conn):
    _ = config_conn

    with patch.object(Proxy, '_cb_mqtt_is_up', wraps=Proxy._cb_mqtt_is_up) as spy:
        print('call Proxy.class_init')
        Proxy.class_init()
        assert 'homeassistant/' == Proxy.discovery_prfx
        assert 'tsun/' == Proxy.entity_prfx
        assert 'test_1/' == Proxy.proxy_node_id
        await Proxy._cb_mqtt_is_up()
        spy.assert_called_once()

@pytest.mark.asyncio
async def test_mqtt_is_up(config_conn):
    _ = config_conn

    with patch.object(Mqtt, 'publish') as spy:
        Proxy.class_init()
        await Proxy._cb_mqtt_is_up()
        spy.assert_called()

@pytest.mark.asyncio
async def test_mqtt_proxy_statt_invalid(config_conn):
    _ = config_conn

    with patch.object(Mqtt, 'publish') as spy:
        Proxy.class_init()
        await Proxy._async_publ_mqtt_proxy_stat('InValId_kEy')
        spy.assert_not_called()
