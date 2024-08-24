
# test_with_pytest.py
import pytest, json, math
from app.src.infos import Register
from app.src.gen3plus.infos_g3p import InfosG3P
from app.src.gen3plus.infos_g3p import RegisterMap

@pytest.fixture
def device_data(): # 0x4110 ftype: 0x02
    msg  = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xba\xd2\x00\x00'
    msg += b'\x19\x00\x00\x00\x00\x00\x00\x00\x05\x3c\x78\x01\x64\x01\x4c\x53'
    msg += b'\x57\x35\x42\x4c\x45\x5f\x31\x37\x5f\x30\x32\x42\x30\x5f\x31\x2e'
    msg += b'\x30\x35\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x40\x2a\x8f\x4f\x51\x54\x31\x39\x32\x2e'
    msg += b'\x31\x36\x38\x2e\x38\x30\x2e\x34\x39\x00\x00\x00\x0f\x00\x01\xb0'
    msg += b'\x02\x0f\x00\xff\x56\x31\x2e\x31\x2e\x30\x30\x2e\x30\x42\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfe\xfe\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x41\x6c\x6c\x69\x75\x73\x2d\x48\x6f'
    msg += b'\x6d\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' 
    return msg

@pytest.fixture
def inverter_data():  # 0x4210 ftype: 0x01
    msg  = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\xb0\x02\xbc\xc8'
    msg += b'\x24\x32\x6c\x1f\x00\x00\xa0\x47\xe4\x33\x01\x00\x03\x08\x00\x00'
    msg += b'\x59\x31\x37\x45\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x45'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x01\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x40\x10\x08\xc8\x00\x49\x13\x8d\x00\x36\x00\x00\x02\x58\x06\x7a'
    msg += b'\x01\x61\x00\xa8\x02\x54\x01\x5a\x00\x8a\x01\xe4\x01\x5a\x00\xbd'
    msg += b'\x02\x8f\x00\x11\x00\x01\x00\x00\x00\x0b\x00\x00\x27\x98\x00\x04'
    msg += b'\x00\x00\x0c\x04\x00\x03\x00\x00\x0a\xe7\x00\x05\x00\x00\x0c\x75'
    msg += b'\x00\x00\x00\x00\x06\x16\x02\x00\x00\x00\x55\xaa\x00\x01\x00\x00'
    msg += b'\x00\x00\x00\x00\xff\xff\x07\xd0\x00\x03\x04\x00\x04\x00\x04\x00'
    msg += b'\x04\x00\x00\x01\xff\xff\x00\x01\x00\x06\x00\x68\x00\x68\x05\x00'
    msg += b'\x09\xcd\x07\xb6\x13\x9c\x13\x24\x00\x01\x07\xae\x04\x0f\x00\x41'
    msg += b'\x00\x0f\x0a\x64\x0a\x64\x00\x06\x00\x06\x09\xf6\x12\x8c\x12\x8c'
    msg += b'\x00\x10\x00\x10\x14\x52\x14\x52\x00\x10\x00\x10\x01\x51\x00\x05'
    msg += b'\x04\x00\x00\x01\x13\x9c\x0f\xa0\x00\x4e\x00\x66\x03\xe8\x04\x00'
    msg += b'\x09\xce\x07\xa8\x13\x9c\x13\x26\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x04\x00\x04\x00\x00\x00\x00\x00\xff\xff\x00\x00'
    msg += b'\x00\x00\x00\x00'
    return msg


def test_default_db():
    i = InfosG3P(client_mode=False)
    
    assert json.dumps(i.db) == json.dumps({
        "inverter": {"Manufacturer": "TSUN", "Equipment_Model": "TSOL-MSxx00", "No_Inputs": 4}, 
        "collector": {"Chip_Type": "IGEN TECH"},
        })

def test_parse_4110(device_data: bytes):
    i = InfosG3P(client_mode=False)
    i.db.clear()
    for key, update in i.parse (device_data, 0x41, 2):
        pass  # side effect is calling generator i.parse()

    assert json.dumps(i.db) == json.dumps({
        'controller': {"Data_Up_Interval": 300, "Collect_Interval": 1, "Heartbeat_Interval": 120, "Signal_Strength": 100, "IP_Address": "192.168.80.49", "Sensor_List": "02b0"},
        'collector': {"Chip_Model": "LSW5BLE_17_02B0_1.05", "Collector_Fw_Version": "V1.1.00.0B"},
        })

def test_parse_4210(inverter_data: bytes):
    i = InfosG3P(client_mode=False)
    i.db.clear()
    
    for key, update in i.parse (inverter_data, 0x42, 1):
        pass  #  side effect is calling generator i.parse()

    assert json.dumps(i.db) == json.dumps({
         "controller": {"Sensor_List": "02b0", "Power_On_Time": 2051}, 
         "inverter": {"Serial_Number": "Y17E00000000000E", "Version": "V4.0.10", "Rated_Power": 600, "Max_Designed_Power": 2000}, 
         "env": {"Inverter_Status": 1, "Inverter_Temp": 14}, 
         "grid": {"Voltage": 224.8, "Current": 0.73, "Frequency": 50.05, "Output_Power": 165.8}, 
         "input": {"pv1": {"Voltage": 35.3, "Current": 1.68, "Power": 59.6, "Daily_Generation": 0.04, "Total_Generation": 30.76}, 
                   "pv2": {"Voltage": 34.6, "Current": 1.38, "Power": 48.4, "Daily_Generation": 0.03, "Total_Generation": 27.91}, 
                   "pv3": {"Voltage": 34.6, "Current": 1.89, "Power": 65.5, "Daily_Generation": 0.05, "Total_Generation": 31.89}, 
                   "pv4": {"Voltage": 1.7, "Current": 0.01, "Power": 0.0, "Total_Generation": 15.58}}, 
         "total": {"Daily_Generation": 0.11, "Total_Generation": 101.36}
        })
    
def test_build_ha_conf1():
    i = InfosG3P(client_mode=False)
    i.static_init()                # initialize counter

    tests = 0
    for d_json, comp, node_id, id in i.ha_confs(ha_prfx="tsun/", node_id="garagendach/", snr='123'):

        if id == 'out_power_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/grid", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "out_power_123", "val_tpl": "{{value_json['Output_Power'] | float}}", "unit_of_meas": "W", "dev": {"name": "Micro Inverter", "sa": "Micro Inverter", "via_device": "controller_123", "mdl": "TSOL-MSxx00", "mf": "TSUN", "ids": ["inverter_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'daily_gen_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Daily Generation", "stat_t": "tsun/garagendach/total", "dev_cla": "energy", "stat_cla": "total_increasing", "uniq_id": "daily_gen_123", "val_tpl": "{{value_json['Daily_Generation'] | float}}", "unit_of_meas": "kWh", "ic": "mdi:solar-power-variant", "dev": {"name": "Micro Inverter", "sa": "Micro Inverter", "via_device": "controller_123", "mdl": "TSOL-MSxx00", "mf": "TSUN", "ids": ["inverter_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv1_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv1_123", "val_tpl": "{{ (value_json['pv1']['Power'] | float)}}", "unit_of_meas": "W", "dev": {"name": "Module PV1", "sa": "Module PV1", "via_device": "inverter_123", "ids": ["input_pv1_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv2_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv2_123", "val_tpl": "{{ (value_json['pv2']['Power'] | float)}}", "unit_of_meas": "W", "dev": {"name": "Module PV2", "sa": "Module PV2", "via_device": "inverter_123", "ids": ["input_pv2_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv3_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv3_123", "val_tpl": "{{ (value_json['pv3']['Power'] | float)}}", "unit_of_meas": "W", "dev": {"name": "Module PV3", "sa": "Module PV3", "via_device": "inverter_123", "ids": ["input_pv3_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv4_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv4_123", "val_tpl": "{{ (value_json['pv4']['Power'] | float)}}", "unit_of_meas": "W", "dev": {"name": "Module PV4", "sa": "Module PV4", "via_device": "inverter_123", "ids": ["input_pv4_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'signal_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Signal Strength", "stat_t": "tsun/garagendach/controller", "dev_cla": None, "stat_cla": "measurement", "uniq_id": "signal_123", "val_tpl": "{{value_json[\'Signal_Strength\'] | int}}", "unit_of_meas": "%", "ic": "mdi:wifi", "dev": {"name": "Controller", "sa": "Controller", "via_device": "proxy", "mf": "IGEN TECH", "ids": ["controller_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1
        elif id == 'inv_count_456':
            assert False

    assert tests==7

def test_build_ha_conf2():
    i = InfosG3P(client_mode=False)
    i.static_init()                # initialize counter

    tests = 0
    for d_json, comp, node_id, id in i.ha_proxy_confs(ha_prfx="tsun/", node_id = 'proxy/', snr = '456'):

        if id == 'out_power_123':
            assert False
        elif id == 'daily_gen_123':
            assert False
        elif id == 'power_pv1_123':
            assert False
        elif id == 'power_pv2_123':
            assert False
        elif id == 'power_pv3_123':
            assert False
        elif id == 'power_pv4_123':
            assert False
        elif id == 'signal_123':
            assert False
        elif id == 'inv_count_456':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Active Inverter Connections", "stat_t": "tsun/proxy/proxy", "dev_cla": None, "stat_cla": None, "uniq_id": "inv_count_456", "val_tpl": "{{value_json['Inverter_Cnt'] | int}}", "ic": "mdi:counter", "dev": {"name": "Proxy", "sa": "Proxy", "mdl": "proxy", "mf": "Stefan Allius", "sw": "unknown", "ids": ["proxy"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

    assert tests==1

def test_build_ha_conf3():
    i = InfosG3P(client_mode=True)
    i.static_init()                # initialize counter

    tests = 0
    for d_json, comp, node_id, id in i.ha_confs(ha_prfx="tsun/", node_id="garagendach/", snr='123'):

        if id == 'out_power_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/grid", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "out_power_123", "val_tpl": "{{value_json['Output_Power'] | float}}", "unit_of_meas": "W", "dev": {"name": "Micro Inverter", "sa": "Micro Inverter", "via_device": "controller_123", "mdl": "TSOL-MSxx00", "mf": "TSUN", "ids": ["inverter_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'daily_gen_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Daily Generation", "stat_t": "tsun/garagendach/total", "dev_cla": "energy", "stat_cla": "total_increasing", "uniq_id": "daily_gen_123", "val_tpl": "{{value_json['Daily_Generation'] | float}}", "unit_of_meas": "kWh", "ic": "mdi:solar-power-variant", "dev": {"name": "Micro Inverter", "sa": "Micro Inverter", "via_device": "controller_123", "mdl": "TSOL-MSxx00", "mf": "TSUN", "ids": ["inverter_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv1_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv1_123", "val_tpl": "{{ (value_json['pv1']['Power'] | float)}}", "unit_of_meas": "W", "dev": {"name": "Module PV1", "sa": "Module PV1", "via_device": "inverter_123", "ids": ["input_pv1_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv2_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv2_123", "val_tpl": "{{ (value_json['pv2']['Power'] | float)}}", "unit_of_meas": "W", "dev": {"name": "Module PV2", "sa": "Module PV2", "via_device": "inverter_123", "ids": ["input_pv2_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv3_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv3_123", "val_tpl": "{{ (value_json['pv3']['Power'] | float)}}", "unit_of_meas": "W", "dev": {"name": "Module PV3", "sa": "Module PV3", "via_device": "inverter_123", "ids": ["input_pv3_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv4_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv4_123", "val_tpl": "{{ (value_json['pv4']['Power'] | float)}}", "unit_of_meas": "W", "dev": {"name": "Module PV4", "sa": "Module PV4", "via_device": "inverter_123", "ids": ["input_pv4_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'signal_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({})
            tests +=1
        elif id == 'inv_count_456':
            assert False

    assert tests==7

def test_build_ha_conf4():
    i = InfosG3P(client_mode=True)
    i.static_init()                # initialize counter

    tests = 0
    for d_json, comp, node_id, id in i.ha_proxy_confs(ha_prfx="tsun/", node_id = 'proxy/', snr = '456'):

        if id == 'out_power_123':
            assert False
        elif id == 'daily_gen_123':
            assert False
        elif id == 'power_pv1_123':
            assert False
        elif id == 'power_pv2_123':
            assert False
        elif id == 'power_pv3_123':
            assert False
        elif id == 'power_pv4_123':
            assert False
        elif id == 'signal_123':
            assert False
        elif id == 'inv_count_456':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Active Inverter Connections", "stat_t": "tsun/proxy/proxy", "dev_cla": None, "stat_cla": None, "uniq_id": "inv_count_456", "val_tpl": "{{value_json['Inverter_Cnt'] | int}}", "ic": "mdi:counter", "dev": {"name": "Proxy", "sa": "Proxy", "mdl": "proxy", "mf": "Stefan Allius", "sw": "unknown", "ids": ["proxy"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

    assert tests==1

def test_exception_and_eval(inverter_data: bytes):

    # add eval to convert temperature from °F to °C
    RegisterMap.map[0x420100d8]['eval'] =  '(result-32)/1.8'
    # map PV1_VOLTAGE to invalid register  
    RegisterMap.map[0x420100e0]['reg'] = Register.TEST_REG2
    # set invalid maping entry for OUTPUT_POWER (string instead of dict type) 
    backup = RegisterMap.map[0x420100de]
    RegisterMap.map[0x420100de] = 'invalid_entry'

    i = InfosG3P(client_mode=False)
    # i.db.clear()
    
    for key, update in i.parse (inverter_data, 0x42, 1):
        pass  #  side effect is calling generator i.parse()
    assert math.isclose(12.2222, round (i.get_db_value(Register.INVERTER_TEMP, 0),4), rel_tol=1e-09, abs_tol=1e-09)
    del RegisterMap.map[0x420100d8]['eval'] # remove eval
    RegisterMap.map[0x420100e0]['reg'] = Register.PV1_VOLTAGE # reset mapping
    RegisterMap.map[0x420100de] = backup # reset mapping
    
    for key, update in i.parse (inverter_data, 0x42, 1):
        pass  #  side effect is calling generator i.parse()
    assert 54 == i.get_db_value(Register.INVERTER_TEMP, 0)
 