# test_with_pytest.py
import tomllib
from schema import SchemaMissingKeyError
from cnf.config import Config, ConfigIfc

class TstConfig(ConfigIfc):

    @classmethod
    def __init__(cls, cnf):
        cls.act_config = cnf

    @classmethod
    def get_config(cls) -> dict:
        return cls.act_config


def test_empty_config():
    cnf = {}
    try:
        Config.conf_schema.validate(cnf)
        assert False
    except SchemaMissingKeyError:
        pass

def test_default_config():
    with open("app/config/default_config.toml", "rb") as f:
        cnf = tomllib.load(f)

    try:
        validated = Config.conf_schema.validate(cnf)
    except Exception:
        assert False
    assert validated == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'},
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
                                 'sensor_list': 688}, 
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
                                 'sensor_list': 688}}}

def test_full_config():
    cnf = {'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 
           'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []},
                                   'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}},
           'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 
           'mqtt': {'host': 'mqtt', 'port': 1883, 'user': '', 'passwd': ''}, 
           'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 
           'inverters': {'allow_all': True, 
                         'R170000000000001': {'modbus_polling': True, 'node_id': '', 'sensor_list': 0, 'suggested_area': '', 'pv1': {'type': 'type1', 'manufacturer': 'man1'}, 'pv2': {'type': 'type2', 'manufacturer': 'man2'}, 'pv3': {'type': 'type3', 'manufacturer': 'man3'}}, 
                         'Y170000000000001': {'modbus_polling': True, 'monitor_sn': 2000000000, 'node_id': '', 'sensor_list': 0x1511, 'suggested_area': ''}}}
    try:
        validated = Config.conf_schema.validate(cnf)
    except Exception:
        assert False
    assert validated == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 'inverters': {'allow_all': True, 'R170000000000001': {'node_id': '', 'modbus_polling': True, 'monitor_sn': 0, 'pv1': {'manufacturer': 'man1','type': 'type1'},'pv2': {'manufacturer': 'man2','type': 'type2'},'pv3': {'manufacturer': 'man3','type': 'type3'}, 'suggested_area': '', 'sensor_list': 0}, 'Y170000000000001': {'modbus_polling': True, 'monitor_sn': 2000000000, 'node_id': '', 'suggested_area': '', 'sensor_list': 5393}}}

def test_mininum_config():
    cnf = {'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 
           'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+']},
                                   'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE']}}},
           'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 
           'mqtt': {'host': 'mqtt', 'port': 1883, 'user': '', 'passwd': ''}, 
           'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 
           'inverters': {'allow_all': True,
                         'R170000000000001': {}}
    } 

    try:
        validated = Config.conf_schema.validate(cnf)
    except Exception:
        assert False
    assert validated == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 'inverters': {'allow_all': True, 'R170000000000001': {'node_id': '', 'modbus_polling': True, 'monitor_sn': 0, 'suggested_area': '', 'sensor_list': 688}}}

def test_read_empty():
    cnf = {}
    err = Config.init(TstConfig(cnf), 'app/config/')
    assert err == None
    cnf = Config.get()
    assert cnf == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'},
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
                           'sensor_list': 688
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
                           'sensor_list': 688
                       }
                    }
                  }
    
    defcnf = Config.def_config.get('solarman') 
    assert defcnf == {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}
    assert True == Config.is_default('solarman')

def test_no_file():
    cnf = {}
    err = Config.init(TstConfig(cnf), '')
    assert err == "Config.read: [Errno 2] No such file or directory: 'default_config.toml'"
    cnf = Config.get()
    assert cnf == {}    
    defcnf = Config.def_config.get('solarman') 
    assert defcnf == None

def test_read_cnf1():
    cnf = {'solarman' : {'enabled': False}}
    err = Config.init(TstConfig(cnf), 'app/config/')
    assert err == None
    cnf = Config.get()
    assert cnf == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': False, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'},
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
                           'sensor_list': 688
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
                           'sensor_list': 688
                       }
                    }
                  }
    cnf = Config.get('solarman')
    assert cnf == {'enabled': False, 'host': 'iot.talent-monitoring.com', 'port': 10000}    
    defcnf = Config.def_config.get('solarman') 
    assert defcnf == {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}
    assert False == Config.is_default('solarman')
                   
def test_read_cnf2():
    cnf = {'solarman' : {'enabled': 'FALSE'}}
    err = Config.init(TstConfig(cnf), 'app/config/')
    assert err == None
    cnf = Config.get()
    assert cnf == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'},
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
                           'sensor_list': 688
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
                           'sensor_list': 688
                       }
                    }
                  }
    assert True == Config.is_default('solarman')

def test_read_cnf3():
    cnf = {'solarman' : {'port': 'FALSE'}}
    err = Config.init(TstConfig(cnf), 'app/config/')
    assert err == 'Config.read: Key \'solarman\' error:\nKey \'port\' error:\nint(\'FALSE\') raised ValueError("invalid literal for int() with base 10: \'FALSE\'")'
    cnf = Config.get()
    assert cnf == {}

def test_read_cnf4():
    cnf = {'solarman' : {'port': 5000}}
    err = Config.init(TstConfig(cnf), 'app/config/')
    assert err == None
    cnf = Config.get()
    assert cnf == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 5000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'},
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
                           'sensor_list': 688
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
                           'sensor_list': 688
                       }
                    }
                  }
    assert False == Config.is_default('solarman')

def test_read_cnf5():
    cnf = {'solarman' : {'port': 1023}}
    err = Config.init(TstConfig(cnf), 'app/config/')
    assert err != None

def test_read_cnf6():
    cnf = {'solarman' : {'port': 65536}}
    err = Config.init(TstConfig(cnf), 'app/config/')
    assert err != None
