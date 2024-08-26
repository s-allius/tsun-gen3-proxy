# test_with_pytest.py
import pytest
import asyncio

from mock import patch
from app.src.singleton import Singleton
from app.src.config import Config
from app.src.infos import Infos
from app.src.modbus_tcp import ModbusConn


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
def config_mqtt_conn(test_hostname, test_port):
    Config.act_config = {'mqtt':{'host': test_hostname, 'port': test_port, 'user': '', 'passwd': ''},
                         'ha':{'auto_conf_prefix': 'homeassistant','discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun'}
                        }

@pytest.fixture
def config_no_conn(test_port):
    Config.act_config = {'mqtt':{'host': "", 'port': test_port, 'user': '', 'passwd': ''},
                         'ha':{'auto_conf_prefix': 'homeassistant','discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun'}
                        }

class FakeReader():
    pass


class FakeWriter():
    pass


@pytest.fixture
def patch_open():
    async def new_conn(conn):
        await asyncio.sleep(0.01)
        return FakeReader(), FakeWriter()
    
    def new_open(host: str, port: int):
        return new_conn(None)

    with patch.object(asyncio, 'open_connection', new_open) as conn:
        yield conn


@pytest.mark.asyncio
async def test_modbus_conn(patch_open):
    _ = patch_open
    assert Infos.stat['proxy']['Inverter_Cnt'] == 0

    async with ModbusConn('test.local', 1234) as stream:
        assert stream.node_id == 'G3P'
        assert stream.addr == ('test.local', 1234)
        assert type(stream.reader) is FakeReader
        assert type(stream.writer) is FakeWriter
        assert Infos.stat['proxy']['Inverter_Cnt'] == 1
    
    assert Infos.stat['proxy']['Inverter_Cnt'] == 0
