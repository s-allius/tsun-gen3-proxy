# test_with_pytest.py
import pytest
import json
from mock import patch
from schema import SchemaMissingKeyError
from cnf.config import Config, ConfigIfc
from cnf.config_read_toml import ConfigReadToml

class FakeBuffer:
    rd = str()

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
        if self.bin_mode:
            return bytearray(self.buf.rd.encode('utf-8')).copy()
        else:
            return self.buf.rd.copy()

def patch_open():
    def new_open(file: str, OpenTextMode="rb"):
        if file == "_no__file__no_":
            raise FileNotFoundError
        return FakeOptionsFile(OpenTextMode)

    with patch('builtins.open', new_open) as conn:
        yield conn

class TstConfig(ConfigIfc):

    @classmethod
    def __init__(cls, cnf):
        cls.act_config = cnf

    @classmethod
    def add_config(cls) -> dict:
        return cls.act_config


def test_empty_config():
    cnf = {}
    try:
        Config.conf_schema.validate(cnf)
        assert False
    except SchemaMissingKeyError:
        pass

@pytest.fixture
def ConfigDefault():
    return {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'},
                   'inverters': {
                       'allow_all': False,
                       'R170000000000001': {
                           'suggested_area': '', 
                           'modbus_polling': False, 
                           'monitor_sn': 0, 
                           'node_id': '', 
                           'pv1': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-395M'},
                           'pv2': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-395M'},
                           'sensor_list': 0
                       }, 
                       'Y170000000000001': {
                           'modbus_polling': True, 
                           'monitor_sn': 2000000000, 
                           'suggested_area': '', 
                           'node_id': '', 
                           'pv1': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv2': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv3': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv4': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'sensor_list': 0
                       }
                    },
                    'batteries': {
                        '4100000000000001': {
                            'modbus_polling': True,
                            'monitor_sn': 3000000000,
                            'suggested_area': '',
                            'node_id': '',
                            'pv1': {'manufacturer': 'Risen',
                                    'type': 'RSM40-8-410M'},
                            'pv2': {'manufacturer': 'Risen',
                                    'type': 'RSM40-8-410M'},
                            'sensor_list': 0,
                        }
                    }
                  }

@pytest.fixture
def ConfigComplete():
    return {
        'gen3plus': {
            'at_acl': {
                'mqtt': {'allow': ['AT+'], 'block': ['AT+SUPDATE']},
                'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'],
                         'block': ['AT+SUPDATE']}
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
                                 'node_id': 'PV-Garage2/',
                                 'pv1': {'manufacturer': 'man1',
                                         'type': 'type1'},
                                 'pv2': {'manufacturer': 'man2',
                                         'type': 'type2'},
                                 'pv3': {'manufacturer': 'man3',
                                         'type': 'type3'},
                                 'pv4': {'manufacturer': 'man4',
                                         'type': 'type4'},
                                 'suggested_area': 'Garage2',
                                 'sensor_list': 688},
            'Y170000000000002': {'modbus_polling': False,
                                 'modbus_scanning': {
                                    'bytes': 16,
                                    'start': 2048,
                                    'step': 1024
                                 },
                                 'monitor_sn': 2000000001,
                                 'node_id': 'PV-Garage3/',
                                 'suggested_area': 'Garage3',
                                 'sensor_list': 688}
        },
        'batteries': {
            '4100000000000001': {
                            'modbus_polling': True,
                            'monitor_sn': 3000000000,
                            'suggested_area': 'Garage3',
                            'node_id': 'Bat-Garage3/',
                            'pv1': {'manufacturer': 'man5',
                                    'type': 'type5'},
                            'pv2': {'manufacturer': 'man6',
                                    'type': 'type6'},
                            'sensor_list': 12326}
        }
    }

def test_default_config():
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    validated = Config.def_config
    assert validated == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'},
                         'batteries': {
                             '4100000000000001': {
                                 'modbus_polling': True,
                                 'monitor_sn': 3000000000,
                                 'node_id': '',
                                 'pv1': {'manufacturer': 'Risen',
                                         'type': 'RSM40-8-410M'},
                                 'pv2': {'manufacturer': 'Risen',
                                         'type': 'RSM40-8-410M'},
                                 'sensor_list': 0,
                                 'suggested_area': ''
                             }
                         },
                         'inverters': {
                             'allow_all': False, 
                             'R170000000000001': {
                                 'node_id': '', 
                                 'pv1': {'manufacturer': 'Risen',
                                         'type': 'RSM40-8-395M'},
                                 'pv2': {'manufacturer': 'Risen',
                                         'type': 'RSM40-8-395M'},
                                 'modbus_polling': False,
                                 'monitor_sn': 0, 
                                 'suggested_area': '', 
                                 'sensor_list': 0},
                             'Y170000000000001': {
                                 'modbus_polling': True, 
                                 'monitor_sn': 2000000000, 
                                 'node_id': '',
                                 'pv1': {'manufacturer': 'Risen',
                                         'type': 'RSM40-8-410M'},
                                 'pv2': {'manufacturer': 'Risen',
                                         'type': 'RSM40-8-410M'},
                                 'pv3': {'manufacturer': 'Risen',
                                         'type': 'RSM40-8-410M'},
                                 'pv4': {'manufacturer': 'Risen',
                                         'type': 'RSM40-8-410M'},
                                 'suggested_area': '', 
                                 'sensor_list': 0}}}

def test_full_config(ConfigComplete):
    cnf = {'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 
           'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': ['AT+SUPDATE']},
                                   'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': ['AT+SUPDATE']}}},
           'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 
           'mqtt': {'host': 'mqtt', 'port': 1883, 'user': '', 'passwd': ''}, 
           'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 
           'batteries': {
                         '4100000000000001': {'modbus_polling': True, 'monitor_sn': 3000000000, 'node_id': 'Bat-Garage3/', 'sensor_list': 0x3026, 'suggested_area': 'Garage3', 'pv1': {'type': 'type5', 'manufacturer': 'man5'}, 'pv2': {'type': 'type6', 'manufacturer': 'man6'}}
           },
           'inverters': {'allow_all': False, 
                         'R170000000000001': {'modbus_polling': False, 'node_id': 'PV-Garage/', 'sensor_list': 0x02B0, 'suggested_area': 'Garage', 'pv1': {'type': 'type1', 'manufacturer': 'man1'}, 'pv2': {'type': 'type2', 'manufacturer': 'man2'}}, 
                         'Y170000000000001': {'modbus_polling': True, 'monitor_sn': 2000000000, 'node_id': 'PV-Garage2/', 'sensor_list': 0x02B0, 'suggested_area': 'Garage2', 'pv1': {'type': 'type1', 'manufacturer': 'man1'}, 'pv2': {'type': 'type2', 'manufacturer': 'man2'}, 'pv3': {'type': 'type3', 'manufacturer': 'man3'}, 'pv4': {'type': 'type4', 'manufacturer': 'man4'}},
                         'Y170000000000002': {'modbus_polling': False, 'monitor_sn': 2000000001, 'node_id': 'PV-Garage3/', 'sensor_list': 0x02B0, 'suggested_area': 'Garage3', 'modbus_scanning': {'start': 2048, 'step': 1024, 'bytes': 16}}
           }
    }
    try:
        validated = Config.conf_schema.validate(cnf)
    except Exception:
        assert False
    assert validated == ConfigComplete

def test_read_empty(ConfigDefault):
    test_buffer.rd = ""
    
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    for _ in patch_open():
        ConfigReadToml("config/config.toml")
        err = Config.get_error()

    assert err == None
    cnf = Config.get()
    assert cnf == ConfigDefault
    
    defcnf = Config.def_config.get('solarman') 
    assert defcnf == {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}
    assert True == Config.is_default('solarman')

def test_no_file():
    Config.init(ConfigReadToml("default_config.toml"))
    err = Config.get_error()
    assert err == "Config.read: [Errno 2] No such file or directory: 'default_config.toml'"
    cnf = Config.get()
    assert cnf == {}    
    defcnf = Config.def_config.get('solarman') 
    assert defcnf == None

def test_no_file2():
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    assert Config.err == None
    ConfigReadToml("_no__file__no_")
    err = Config.get_error()
    assert err == None

def test_invalid_filename():
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    assert Config.err == None
    ConfigReadToml(None)
    err = Config.get_error()
    assert err == None

def test_read_cnf1():
    test_buffer.rd = "solarman.enabled = false"
    
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    for _ in patch_open():
        ConfigReadToml("config/config.toml")
        err = Config.get_error()

    assert err == None
    cnf = Config.get()
    assert cnf == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': False, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'},
                   'batteries': {
                       '4100000000000001': {
                           'modbus_polling': True,
                           'monitor_sn': 3000000000,
                           'node_id': '',
                           'pv1': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv2': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'sensor_list': 0,
                           'suggested_area': ''
                       }
                   },
                   'inverters': {
                       'allow_all': False,
                       'R170000000000001': {
                           'suggested_area': '', 
                           'modbus_polling': False, 
                           'monitor_sn': 0, 
                           'node_id': '', 
                           'pv1': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-395M'},
                           'pv2': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-395M'},
                           'sensor_list': 0
                       }, 
                       'Y170000000000001': {
                           'modbus_polling': True, 
                           'monitor_sn': 2000000000, 
                           'suggested_area': '', 
                           'node_id': '', 
                           'pv1': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv2': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv3': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv4': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'sensor_list': 0
                       }
                    }
                  }
    cnf = Config.get('solarman')
    assert cnf == {'enabled': False, 'host': 'iot.talent-monitoring.com', 'port': 10000}    
    defcnf = Config.def_config.get('solarman') 
    assert defcnf == {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}
    assert False == Config.is_default('solarman')
                   
def test_read_cnf2():
    test_buffer.rd = "solarman.enabled = 'FALSE'"
    
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    for _ in patch_open():
        ConfigReadToml("config/config.toml")
        err = Config.get_error()

    assert err == None
    cnf = Config.get()
    assert cnf == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'},
                   'batteries': {
                       '4100000000000001': {
                           'modbus_polling': True,
                           'monitor_sn': 3000000000,
                           'node_id': '',
                           'pv1': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv2': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'sensor_list': 0,
                           'suggested_area': ''
                       }
                   },
                   'inverters': {
                       'allow_all': False,
                       'R170000000000001': {
                           'suggested_area': '', 
                           'modbus_polling': False, 
                           'monitor_sn': 0, 
                           'node_id': '', 
                           'pv1': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-395M'},
                           'pv2': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-395M'},
                           'sensor_list': 0
                       }, 
                       'Y170000000000001': {
                           'modbus_polling': True, 
                           'monitor_sn': 2000000000, 
                           'suggested_area': '', 
                           'node_id': '', 
                           'pv1': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv2': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv3': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv4': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'sensor_list': 0
                       }
                    }
                  }
    assert True == Config.is_default('solarman')

def test_read_cnf3(ConfigDefault):
    test_buffer.rd = "solarman.port = 'FALSE'"
    
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    for _ in patch_open():
        ConfigReadToml("config/config.toml")
        err = Config.get_error()

    assert err == 'error: Key \'solarman\' error:\nKey \'port\' error:\nint(\'FALSE\') raised ValueError("invalid literal for int() with base 10: \'FALSE\'")'
    cnf = Config.get()
    assert cnf == ConfigDefault

def test_read_cnf4():
    test_buffer.rd = "solarman.port = 5000"
    
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    for _ in patch_open():
        ConfigReadToml("config/config.toml")
        err = Config.get_error()

    assert err == None
    cnf = Config.get()
    assert cnf == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 5000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'},
                   'batteries': {
                       '4100000000000001': {
                           'modbus_polling': True,
                           'monitor_sn': 3000000000,
                           'node_id': '',
                           'pv1': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv2': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'sensor_list': 0,
                           'suggested_area': ''
                       }
                   },
                   'inverters': {
                       'allow_all': False,
                       'R170000000000001': {
                           'suggested_area': '', 
                           'modbus_polling': False, 
                           'monitor_sn': 0, 
                           'node_id': '', 
                           'pv1': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-395M'},
                           'pv2': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-395M'},
                           'sensor_list': 0
                       }, 
                       'Y170000000000001': {
                           'modbus_polling': True, 
                           'monitor_sn': 2000000000, 
                           'suggested_area': '', 
                           'node_id': '', 
                           'pv1': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv2': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv3': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'pv4': {'manufacturer': 'Risen',
                                   'type': 'RSM40-8-410M'},
                           'sensor_list': 0
                       }
                    }
                  }
    assert False == Config.is_default('solarman')

def test_read_cnf5():
    test_buffer.rd = "solarman.port = 1023"
    
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    for _ in patch_open():
        ConfigReadToml("config/config.toml")
        err = Config.get_error()
    assert err != None

def test_read_cnf6():
    test_buffer.rd = "solarman.port = 65536"
    
    Config.init(ConfigReadToml("app/src/cnf/default_config.toml"))
    for _ in patch_open():
        ConfigReadToml("config/config.toml")
        err = Config.get_error()
    assert err != None
