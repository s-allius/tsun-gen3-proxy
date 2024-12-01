# test_with_pytest.py
import pytest
import tomllib
from mock import patch
from config import Config

from home.create_config_toml import create_config


class FakeBuffer:
    rd = bytearray()
    wr = str()


test_buffer = FakeBuffer


class FakeFile():
    def __init__(self):
        self.buf = test_buffer

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


class FakeOptionsFile(FakeFile):
    def read(self):
        return self.buf.rd


class FakeConfigFile(FakeFile):
    def write(self, data: str):
        self.buf.wr += data


@pytest.fixture
def patch_open():

    def new_open(file: str, OpenTextMode="r"):
        if file == '/data/options.json':
            return FakeOptionsFile()
        elif file == '/home/proxy/config/config.toml':
            # write_buffer += 'bla1'.encode('utf-8')
            return FakeConfigFile()

        raise TimeoutError

    with patch('builtins.open', new_open) as conn:
        yield conn


def test_config(patch_open):
    _ = patch_open
    test_buffer.rd = """
 {
   "inverters": [
     {
       "serial": "R170000000000001",
       "node_id": "PV-Garage",
       "suggested_area": "Garage",
       "modbus_polling": false,
       "pv1_manufacturer": "man1",
       "pv1_type": "type1",
       "pv2_manufacturer": "man2",
       "pv2_type": "type2"
     },
     {
       "serial": "Y170000000000001",
       "monitor_sn": 2000000000,
       "node_id": "PV-Garage",
       "suggested_area": "Garage2",
       "modbus_polling": true,
       "client_mode_host": "InverterIP",
       "client_mode_port": 1234,
       "pv1_manufacturer": "man1",
       "pv1_type": "type1",
       "pv2_manufacturer": "man2",
       "pv2_type": "type2",
       "pv3_manufacturer": "man3",
       "pv3_type": "type3",
       "pv4_manufacturer": "man4",
       "pv4_type": "type4"
     }
   ],
   "tsun.enabled": true,
   "solarman.enabled": true,
   "inverters.allow_all": false,
   "gen3plus.at_acl.tsun.allow": [
     "AT+Z",
     "AT+UPURL",
     "AT+SUPDATE"
   ],
   "gen3plus.at_acl.mqtt.allow": [
     "AT+"
   ]
 }
 """
    create_config()
    cnf = tomllib.loads(test_buffer.wr)

    validated = Config.conf_schema.validate(cnf)
    assert validated == {
        'gen3plus': {
            'at_acl': {
                'mqtt': {'allow': ['AT+'], 'block': []},
                'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'],
                         'block': []}
            }
        },
        'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com',
                 'port': 5005},
        'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com',
                     'port': 10000},
        'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None},
        'ha': {'auto_conf_prefix': 'homeassistant',
               'discovery_prefix': 'homeassistant',
               'entity_prefix': 'tsun',
               'proxy_node_id': 'proxy',
               'proxy_unique_id': 'P170000000000001'},
        'inverters': {
            'allow_all': False,
            'R170000000000001': {'node_id': 'PV-Garage/',
                                 'modbus_polling': False,
                                 'monitor_sn': 0,
                                 'pv1': {'manufacturer': 'man1',
                                         'type': 'type1'},
                                 'pv2': {'manufacturer': 'man2',
                                         'type': 'type2'},
                                 'suggested_area': 'Garage',
                                 'sensor_list': 688},
            'Y170000000000001': {'modbus_polling': True,
                                 'monitor_sn': 2000000000,
                                 'node_id': 'PV-Garage/',
                                 'pv1': {'manufacturer': 'man1',
                                         'type': 'type1'},
                                 'pv2': {'manufacturer': 'man2',
                                         'type': 'type2'},
                                 'pv3': {'manufacturer': 'man3',
                                         'type': 'type3'},
                                 'pv4': {'manufacturer': 'man4',
                                         'type': 'type4'},
                                 'suggested_area': 'Garage2',
                                 'sensor_list': 688}
        }
    }
