# test_with_pytest.py
import pytest
from mock import patch
from cnf.config import Config
from cnf.config_read_json import ConfigReadJson
from cnf.config_read_toml import ConfigReadToml

from test_config import ConfigDefault, ConfigComplete


class CnfIfc(ConfigReadJson):
    def __init__(self):
        pass


class FakeBuffer:
    rd = str()
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
    def __init__(self, OpenTextMode):
        super().__init__()
        self.bin_mode = 'b' in OpenTextMode

    def read(self):
        print(f"Fake.read: bmode:{self.bin_mode}")
        if self.bin_mode:
            return bytearray(self.buf.rd.encode('utf-8')).copy()
        else:
            print(f"Fake.read: str:{self.buf.rd}")
            return self.buf.rd

def patch_open():
    def new_open(file: str, OpenTextMode="r"):
        if file == "_no__file__no_":
            raise FileNotFoundError
        return FakeOptionsFile(OpenTextMode)

    with patch('builtins.open', new_open) as conn:
        yield conn

@pytest.fixture
def ConfigTomlEmpty():
    return {
        'mqtt': {'host': 'mqtt', 'port': 1883, 'user': '', 'passwd': ''},
        'ha': {'auto_conf_prefix': 'homeassistant',
               'discovery_prefix': 'homeassistant',
               'entity_prefix': 'tsun',
               'proxy_node_id': 'proxy',
               'proxy_unique_id': 'P170000000000001'},
        'solarman': {
            'enabled': True,
            'host': 'iot.talent-monitoring.com',
            'port': 10000,
        },
        'tsun': {
            'enabled': True,
            'host': 'logger.talent-monitoring.com',
            'port': 5005,
        },
        'inverters': {
            'allow_all': False
        },
        'gen3plus': {'at_acl': {'tsun': {'allow': [], 'block': []},
                                'mqtt': {'allow': [], 'block': []}}},
    }


def test_no_config(ConfigDefault):
    test_buffer.rd = ""  # empty buffer, no json
    
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    for _ in patch_open():
        ConfigReadJson()
        err = Config.get_error()

    assert err == 'error: Expecting value: line 1 column 1 (char 0)'
    cnf = Config.get()
    assert cnf == ConfigDefault

def test_no_file(ConfigDefault):
    test_buffer.rd = ""  # empty buffer, no json
    
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    for _ in patch_open():
        ConfigReadJson("_no__file__no_")
        err = Config.get_error()

    assert err == None
    cnf = Config.get()
    assert cnf == ConfigDefault

def test_invalid_filename(ConfigDefault):
    test_buffer.rd = ""  # empty buffer, no json
    
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    for _ in patch_open():
        ConfigReadJson(None)
        err = Config.get_error()

    assert err == None
    cnf = Config.get()
    assert cnf == ConfigDefault

def test_cnv1():
    """test dotted key converting"""
    tst = {
   "gen3plus.at_acl.mqtt.block": [
      "AT+SUPDATE",
      "AT+"
   ]
}

    cnf = ConfigReadJson()
    obj = cnf.convert_to_obj(tst)
    assert obj == {
        'gen3plus': {
            'at_acl': {
                'mqtt': {
                    'block': [
                        'AT+SUPDATE',
                        "AT+"
                    ],
                },
            },
        },
    }

def test_cnv2():
    """test a valid list with serials in inverters"""
    tst = {
   "inverters": [
     {
       "serial": "R170000000000001",
     },
     {
       "serial": "Y170000000000001",
     }
   ],
}

    cnf = ConfigReadJson()
    obj = cnf.convert_to_obj(tst)
    assert obj == {
        'inverters': {
            'R170000000000001': {},
            'Y170000000000001': {}
        },
    }

def test_cnv3():
    """test the combination of a list and a scalar in inverters"""
    tst = {
   "inverters": [
     {
       "serial": "R170000000000001",
     },
     {
       "serial": "Y170000000000001",
     }
   ],
   "inverters.allow_all": False,
}

    cnf = ConfigReadJson()
    obj = cnf.convert_to_obj(tst)
    assert obj == {
        'inverters': {
            'R170000000000001': {},
            'Y170000000000001': {},
            'allow_all': False,
        },
    }

def test_cnv4():
    tst = {
   "inverters": [
     {
       "serial": "R170000000000001",
       "node_id": "PV-Garage/",
       "suggested_area": "Garage",
       "modbus_polling": False,
       "pv1.manufacturer": "man1",
       "pv1.type": "type1",
       "pv2.manufacturer": "man2",
       "pv2.type": "type2",
       "sensor_list": 688
     },
     {
       "serial": "Y170000000000001",
       "monitor_sn": 2000000000,
       "node_id": "PV-Garage2/",
       "suggested_area": "Garage2",
       "modbus_polling": True,
       "client_mode.host": "InverterIP",
       "client_mode.port": 1234,
       "client_mode.forward": True,
       "pv1.manufacturer": "man1",
       "pv1.type": "type1",
       "pv2.manufacturer": "man2",
       "pv2.type": "type2",
       "pv3.manufacturer": "man3",
       "pv3.type": "type3",
       "pv4.manufacturer": "man4",
       "pv4.type": "type4",
       "sensor_list": 688
     }
   ],
   "tsun.enabled": True,
   "solarman.enabled": True,
   "inverters.allow_all": False,
   "gen3plus.at_acl.tsun.allow": [
     "AT+Z",
     "AT+UPURL",
     "AT+SUPDATE"
   ],
   "gen3plus.at_acl.tsun.block": [
     "AT+SUPDATE"
   ],
   "gen3plus.at_acl.mqtt.allow": [
     "AT+"
   ],
   "gen3plus.at_acl.mqtt.block": [
      "AT+SUPDATE"
   ]
}

    cnf = ConfigReadJson()
    obj = cnf.convert_to_obj(tst)
    assert obj == {
        'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': ['AT+SUPDATE']},
                                 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'],
                                          'block': ['AT+SUPDATE']}}},
        'inverters': {'R170000000000001': {'modbus_polling': False,
                                           'node_id': 'PV-Garage/',
                                           'pv1': {
                                               'manufacturer': 'man1',
                                                'type': 'type1'},
                                           'pv2': {
                                               'manufacturer': 'man2',
                                                'type': 'type2'},
                                           'sensor_list': 688,
                                           'suggested_area': 'Garage'},
                      'Y170000000000001': {'client_mode': {
                                                'host': 'InverterIP',
                                                'port': 1234,
                                                'forward': True},
                                           'modbus_polling': True,
                                           'monitor_sn': 2000000000,
                                           'node_id': 'PV-Garage2/',
                                           'pv1': {
                                                'manufacturer': 'man1',
                                                'type': 'type1'},
                                           'pv2': {
                                                'manufacturer': 'man2',
                                                'type': 'type2'},
                                           'pv3': {
                                                'manufacturer': 'man3',
                                                'type': 'type3'},
                                           'pv4': {
                                                'manufacturer': 'man4',
                                                'type': 'type4'},
                                           'sensor_list': 688,
                                           'suggested_area': 'Garage2'},
                      'allow_all': False},
        'solarman': {'enabled': True},
        'tsun': {'enabled': True}
    }

def test_cnv5():
    """test a invalid list with missing serials"""
    tst = {
   "inverters": [
     {
       "node_id": "PV-Garage1/",
     },
     {
       "serial": "Y170000000000001",
       "node_id": "PV-Garage2/",
     }
   ],
}
    cnf = ConfigReadJson()
    obj = cnf.convert_to_obj(tst)
    assert obj == {
        'inverters': {
            'Y170000000000001': {'node_id': 'PV-Garage2/'}
        },
    }

def test_cnv6():
    """test overwritting a value in inverters"""
    tst = {
       "inverters": [{
            "serial": "Y170000000000001",
            "node_id": "PV-Garage2/",
        }],
    }
    tst2 = {
       "inverters": [{
            "serial": "Y170000000000001",
            "node_id": "PV-Garden/",
        }],
    }
    cnf = ConfigReadJson()
    conf = {}
    for key, val in tst.items():
        cnf.convert_inv_arr(conf, key, val)

    assert conf == {
        'inverters': {
            'Y170000000000001': {'node_id': 'PV-Garage2/'}
        },
    }

    for key, val in tst2.items():
        cnf.convert_inv_arr(conf, key, val)

    assert conf == {
        'inverters': {
            'Y170000000000001': {'node_id': 'PV-Garden/'}
        },
    }

def test_empty_config(ConfigDefault):
    test_buffer.rd = "{}"  # empty json
    
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    for _ in patch_open():
        ConfigReadJson()
        err = Config.get_error()

    assert err == None
    cnf = Config.get()
    assert cnf == ConfigDefault


def test_full_config(ConfigComplete):
    test_buffer.rd = """
{
   "inverters": [
     {
       "serial": "R170000000000001",
       "node_id": "PV-Garage/",
       "suggested_area": "Garage",
       "modbus_polling": false,
       "pv1.manufacturer": "man1",
       "pv1.type": "type1",
       "pv2.manufacturer": "man2",
       "pv2.type": "type2",
       "sensor_list": 688
     },
     {
       "serial": "Y170000000000001",
       "monitor_sn": 2000000000,
       "node_id": "PV-Garage2/",
       "suggested_area": "Garage2",
       "modbus_polling": true,
       "pv1.manufacturer": "man1",
       "pv1.type": "type1",
       "pv2.manufacturer": "man2",
       "pv2.type": "type2",
       "pv3.manufacturer": "man3",
       "pv3.type": "type3",
       "pv4.manufacturer": "man4",
       "pv4.type": "type4",
       "sensor_list": 688
     }
   ],
   "batteries": [
     {
       "serial": "4100000000000001",
       "modbus_polling": true,
       "monitor_sn": 3000000000,
       "node_id": "Bat-Garage3",
       "suggested_area": "Garage3",
       "pv1.manufacturer": "man5",
       "pv1.type": "type5",
       "pv2.manufacturer": "man6",
       "pv2.type": "type6",
       "sensor_list": 12326
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
   "gen3plus.at_acl.tsun.block": [
     "AT+SUPDATE"
   ],
   "gen3plus.at_acl.mqtt.allow": [
     "AT+"
   ],
   "gen3plus.at_acl.mqtt.block": [
      "AT+SUPDATE"
   ]
}
"""
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    for _ in patch_open():
        ConfigReadJson()
        err = Config.get_error()

    assert err == None
    cnf = Config.get()
    assert cnf == ConfigComplete
