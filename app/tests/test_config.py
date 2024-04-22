# test_with_pytest.py
import tomllib
from schema import SchemaMissingKeyError
from app.src.config import Config


def test_empty_config():
    cnf = {}
    try:
        Config.conf_schema.validate(cnf)
        assert False
    except SchemaMissingKeyError:
        assert True

def test_default_config():
    with open("app/config/default_config.toml", "rb") as f:
        cnf = tomllib.load(f)

    try:
        validated = Config.conf_schema.validate(cnf)
        assert True
    except:
        assert False
    assert validated == {'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 'inverters': {'allow_all': True, 'R170000000000001': {'node_id': '', 'monitor_sn': 0, 'suggested_area': ''}, 'Y170000000000001': {'monitor_sn': 2000000000, 'node_id': '', 'suggested_area': ''}}}

def test_full_config():
    cnf = {'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 
           'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 
           'mqtt': {'host': 'mqtt', 'port': 1883, 'user': '', 'passwd': ''}, 
           'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 
           'inverters': {'allow_all': True, 
                         'R170000000000001': {'node_id': '', 'suggested_area': '', 'pv1': {'type': 'type1', 'manufacturer': 'man1'}, 'pv2': {'type': 'type2', 'manufacturer': 'man2'}, 'pv3': {'type': 'type3', 'manufacturer': 'man3'}}, 
                         'Y170000000000001': {'monitor_sn': 2000000000, 'node_id': '', 'suggested_area': ''}}}
    try:
        validated = Config.conf_schema.validate(cnf)
        assert True
    except:
        assert False
    assert validated == {'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 'inverters': {'allow_all': True, 'R170000000000001': {'node_id': '', 'monitor_sn': 0, 'pv1': {'manufacturer': 'man1','type': 'type1'},'pv2': {'manufacturer': 'man2','type': 'type2'},'pv3': {'manufacturer': 'man3','type': 'type3'}, 'suggested_area': ''}, 'Y170000000000001': {'monitor_sn': 2000000000, 'node_id': '', 'suggested_area': ''}}}

def test_mininum_config():
    cnf = {'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 
           'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 
           'mqtt': {'host': 'mqtt', 'port': 1883, 'user': '', 'passwd': ''}, 
           'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 
           'inverters': {'allow_all': True,
                         'R170000000000001': {}}
    } 

    try:
        validated = Config.conf_schema.validate(cnf)
        assert True
    except:
        assert False
    assert validated == {'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005}, 'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000}, 'mqtt': {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}, 'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'}, 'inverters': {'allow_all': True, 'R170000000000001': {'node_id': '', 'monitor_sn': 0, 'suggested_area': ''}}}