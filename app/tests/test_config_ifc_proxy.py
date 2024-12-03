# test_with_pytest.py
import tomllib
from schema import SchemaMissingKeyError
from cnf.config_ifc_proxy import ConfigIfcProxy

class CnfIfc(ConfigIfcProxy):
    def __init__(self):
        pass

def test_no_config():
    cnf_ifc = CnfIfc()

    cnf = cnf_ifc.get_config("")
    assert cnf == {}

def test_get_config():
    cnf_ifc = CnfIfc()

    cnf = cnf_ifc.get_config("app/config/default_config.toml")
    assert cnf == {
        'gen3plus': {'at_acl': {'mqtt': {'allow': ['AT+'], 'block': []}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE'], 'block': []}}},
        'tsun': {'enabled': True, 'host': 'logger.talent-monitoring.com', 'port': 5005},
        'solarman': {'enabled': True, 'host': 'iot.talent-monitoring.com', 'port': 10000},
        'mqtt': {'host': 'mqtt', 'port': 1883, 'user': '', 'passwd': ''},
        'ha': {'auto_conf_prefix': 'homeassistant', 'discovery_prefix': 'homeassistant', 'entity_prefix': 'tsun', 'proxy_node_id': 'proxy', 'proxy_unique_id': 'P170000000000001'},
        'inverters': {
            'allow_all': False, 
            'R170000000000001': {
                                 'node_id': '', 
                                 'pv1': {'manufacturer': 'Risen',
                                         'type': 'RSM40-8-395M'},
                                 'pv2': {'manufacturer': 'Risen',
                                         'type': 'RSM40-8-395M'},
                                 'modbus_polling': False,
                                 'suggested_area': ''
            }, 
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
                                 'suggested_area': ''
            }
        }
    }

