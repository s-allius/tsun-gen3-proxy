# test_with_pytest.py
import tomllib
from schema import SchemaMissingKeyError
from app.src.config import Config

class TstConfig(Config):

    @classmethod
    def set(cls, cnf):
        cls.config = cnf

    @classmethod
    def _read_config_file(cls) -> dict:
        return cls.config


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
    except:
        assert False
    assert validated == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 'inverters': {'allow_all': True, 'R170000000000001': {'node_id': '', 'modbus_polling': True, 'monitor_sn': 0, 'suggested_area': ''}, 'Y170000000000001': {'modbus_polling': True, 'monitor_sn': 2000000000, 'node_id': '', 'suggested_area': ''}}}

def test_full_config():
    cnf = {'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 
           'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []},
                                   'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}},
           'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 
           'mqtt': {'host': 'mqtt', 'port': 1883, 'user': '', 'passwd': ''}, 
           'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 
           'inverters': {'allow_all': True, 
                         'R170000000000001': {'modbus_polling': True, 'node_id': '', 'suggested_area': '', 'pv1': {'type': 'type1', 'manufacturer': 'man1'}, 'pv2': {'type': 'type2', 'manufacturer': 'man2'}, 'pv3': {'type': 'type3', 'manufacturer': 'man3'}}, 
                         'Y170000000000001': {'modbus_polling': True, 'monitor_sn': 2000000000, 'node_id': '', 'suggested_area': ''}}}
    try:
        validated = Config.conf_schema.validate(cnf)
    except:
        assert False
    assert validated == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 'inverters': {'allow_all': True, 'R170000000000001': {'node_id': '', 'modbus_polling': True, 'monitor_sn': 0, 'pv1': {'manufacturer': 'man1','type': 'type1'},'pv2': {'manufacturer': 'man2','type': 'type2'},'pv3': {'manufacturer': 'man3','type': 'type3'}, 'suggested_area': ''}, 'Y170000000000001': {'modbus_polling': True, 'monitor_sn': 2000000000, 'node_id': '', 'suggested_area': ''}}}

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
    except:
        assert False
    assert validated == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 'inverters': {'allow_all': True, 'R170000000000001': {'node_id': '', 'modbus_polling': True, 'monitor_sn': 0, 'suggested_area': ''}}}

def test_read_empty():
    cnf = {}
    TstConfig.set(cnf)
    err = TstConfig.read('app/config/')
    assert err == None
    cnf = TstConfig.get()
    assert cnf == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 'inverters': {'allow_all': True, 'R170000000000001': {'suggested_area': '', 'modbus_polling': True, 'monitor_sn': 0, 'node_id': ''}, 'Y170000000000001': {'modbus_polling': True, 'monitor_sn': 2000000000, 'suggested_area': '', 'node_id': ''}}}
    
    defcnf = TstConfig.def_config.get('solarman') 
    assert defcnf == {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}
    assert True == TstConfig.is_default('solarman')

def test_no_file():
    cnf = {}
    TstConfig.set(cnf)
    err = TstConfig.read('')
    assert err == "Config.read: [Errno 2] No such file or directory: 'default_config.toml'"
    cnf = TstConfig.get()
    assert cnf == {}    
    defcnf = TstConfig.def_config.get('solarman') 
    assert defcnf == None

def test_read_cnf1():
    cnf = {'solarman' : {'enabled': False}}
    TstConfig.set(cnf)
    err = TstConfig.read('app/config/')
    assert err == None
    cnf = TstConfig.get()
    assert cnf == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': False, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 'inverters': {'allow_all': True, 'R170000000000001': {'suggested_area': '', 'modbus_polling': True, 'monitor_sn': 0, 'node_id': ''}, 'Y170000000000001': {'modbus_polling': True, 'monitor_sn': 2000000000, 'suggested_area': '', 'node_id': ''}}}
    cnf = TstConfig.get('solarman')
    assert cnf == {'enabled': False, 'host': 'iot.talent-monitoring.com', 'port': 10000}    
    defcnf = TstConfig.def_config.get('solarman') 
    assert defcnf == {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}
    assert False == TstConfig.is_default('solarman')
                   
def test_read_cnf2():
    cnf = {'solarman' : {'enabled': 'FALSE'}}
    TstConfig.set(cnf)
    err = TstConfig.read('app/config/')
    assert err == None
    cnf = TstConfig.get()
    assert cnf == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 'inverters': {'allow_all': True, 'R170000000000001': {'suggested_area': '', 'modbus_polling': True, 'monitor_sn': 0, 'node_id': ''}, 'Y170000000000001': {'modbus_polling': True, 'monitor_sn': 2000000000, 'suggested_area': '', 'node_id': ''}}}
    assert True == TstConfig.is_default('solarman')

def test_read_cnf3():
    cnf = {'solarman' : {'port': 'FALSE'}}
    TstConfig.set(cnf)
    err = TstConfig.read('app/config/')
    assert err == 'Config.read: Key \'solarman\' error:\nKey \'port\' error:\nint(\'FALSE\') raised ValueError("invalid literal for int() with base 10: \'FALSE\'")'
    cnf = TstConfig.get()
    assert cnf == {'solarman': {'port': 'FALSE'}}

def test_read_cnf4():
    cnf = {'solarman' : {'port': 5000}}
    TstConfig.set(cnf)
    err = TstConfig.read('app/config/')
    assert err == None
    cnf = TstConfig.get()
    assert cnf == {'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}}, 'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 5000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 'inverters': {'allow_all': True, 'R170000000000001': {'suggested_area': '', 'modbus_polling': True, 'monitor_sn': 0, 'node_id': ''}, 'Y170000000000001': {'modbus_polling': True, 'monitor_sn': 2000000000, 'suggested_area': '', 'node_id': ''}}}
    assert False == TstConfig.is_default('solarman')

def test_read_cnf5():
    cnf = {'solarman' : {'port': 1023}}
    TstConfig.set(cnf)
    err = TstConfig.read('app/config/')
    assert err != None

def test_read_cnf6():
    cnf = {'solarman' : {'port': 65536}}
    TstConfig.set(cnf)
    err = TstConfig.read('app/config/')
    assert err != None
