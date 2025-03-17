
# test_with_pytest.py
import pytest, json, math, random
from infos import Register
from gen3plus.infos_g3p import InfosG3P
from gen3plus.infos_g3p import RegisterMap

@pytest.fixture(scope="session")
def str_test_ip():
    ip =  ".".join(str(random.randint(1, 254)) for _ in range(4))
    print(f'random_ip: {ip}')
    return ip

@pytest.fixture(scope="session")
def bytes_test_ip(str_test_ip):
    ip =  bytes(str.encode(str_test_ip))
    l = len(ip)
    if l < 16:
        ip = ip + bytearray(16-l)
    print(f'random_ip: {ip}')
    return ip

@pytest.fixture
def device_data(bytes_test_ip): # 0x4110 ftype: 0x02
    msg  = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xba\xd2\x00\x00'
    msg += b'\x19\x00\x00\x00\x00\x00\x00\x00\x05\x3c\x78\x01\x64\x01\x4c\x53'
    msg += b'\x57\x35\x42\x4c\x45\x5f\x31\x37\x5f\x30\x32\x42\x30\x5f\x31\x2e'
    msg += b'\x30\x35\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x40\x2a\x8f\x4f\x51\x54' + bytes_test_ip
    msg += b'\x0f\x00\x01\xb0'
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

@pytest.fixture
def batterie_data():  # 0x4210 ftype: 0x01
    msg  = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x26\x30\xc7\xde'
    msg += b'\x2d\x32\x28\x00\x00\x00\x84\x17\x79\x35\x01\x00\x4c\x12\x00\x00'
    msg += b'\x34\x31\x30\x31\x32\x34\x30\x37\x30\x31\x34\x39\x30\x33\x31\x34'
    msg += b'\x0d\x3a\x00\x70\x0d\x2c\x00\x00\x00\x00\x08\x20\x00\x00\x00\x00'
    msg += b'\x14\x0e\xff\xfe\x03\xe8\x0c\x89\x0c\x89\x0c\x89\x0c\x8a\x0c\x89'
    msg += b'\x0c\x89\x0c\x8a\x0c\x89\x0c\x89\x0c\x8a\x0c\x8a\x0c\x89\x0c\x89'
    msg += b'\x0c\x89\x0c\x89\x0c\x88\x00\x0f\x00\x0f\x00\x0f\x00\x0e\x00\x00'
    msg += b'\x00\x00\x00\x0f\x00\x00\x02\x05\x02\x01'
    return msg

@pytest.fixture
def batterie_data2():  # 0x4210 ftype: 0x01
    msg  = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x26\x30\xc7\xde'
    msg += b'\x2d\x32\x28\x00\x00\x00\x84\x17\x79\x35\x01\x00\x4c\x12\x00\x00'
    msg += b'\x34\x31\x30\x31\x32\x34\x30\x37\x30\x31\x34\x39\x30\x33\x31\x34'
    msg += b'\x0d\x3a\x00\x70\x0d\x2c\x00\x00\x00\x00\x08\x20\x00\x00\x00\x00'
    msg += b'\x14\x0e\xff\xfe\x03\xe8\x0c\x89\x0c\x89\x0c\x89\x0c\x8a\x0c\x89'
    msg += b'\x0c\x89\x0c\x8a\x0c\x89\x0c\x89\x0c\x8a\x0c\x8a\x0c\x89\x0c\x89'
    msg += b'\x0c\x89\x0c\x89\x0c\x88\x00\x0f\x00\x0f\x00\x0f\x00\x0e'
    return msg

def test_default_db():
    i = InfosG3P(client_mode=False)
    
    assert json.dumps(i.db) == json.dumps({
        "inverter": {"Manufacturer": "TSUN", "Equipment_Model": "TSOL-MSxx00", "No_Inputs": 4}, 
        "collector": {"Chip_Type": "IGEN TECH"},
        })

def test_parse_4110(str_test_ip, device_data: bytes):
    i = InfosG3P(client_mode=False)
    i.db.clear()
    for key, update in i.parse (device_data, 0x41, 2):
        pass  # side effect is calling generator i.parse()

    assert json.dumps(i.db) == json.dumps({
        'controller': {"Data_Up_Interval": 300, "Collect_Interval": 1, "Heartbeat_Interval": 120, "Signal_Strength": 100, "IP_Address": str_test_ip, "Sensor_List": "02b0", "WiFi_SSID": "Allius-Home"},
        'collector': {"Chip_Model": "LSW5BLE_17_02B0_1.05", "MAC-Addr": "40:2a:8f:4f:51:54", "Collector_Fw_Version": "V1.1.00.0B"},
        })

def test_build_4110(str_test_ip, device_data: bytes):
    i = InfosG3P(client_mode=False)
    i.db.clear()
    for key, update in i.parse (device_data, 0x41, 2):
        pass  # side effect is calling generator i.parse()

    build_msg = i.build(len(device_data), 0x41, 2)
    for i in range(11, 20):
        build_msg[i] = device_data[i]
    assert device_data == build_msg    

def test_parse_4210_02b0(inverter_data: bytes):
    i = InfosG3P(client_mode=False)
    i.db.clear()
    
    for key, update in i.parse (inverter_data, 0x42, 1, 0x02b0):
        pass  #  side effect is calling generator i.parse()

    assert json.dumps(i.db) == json.dumps({
         "controller": {"Sensor_List": "02b0", "Power_On_Time": 2051}, 
         "inverter": {"Serial_Number": "Y17E00000000000E", "Version": "V4.0.10", "Rated_Power": 600, "BOOT_STATUS": 0, "DSP_STATUS": 21930, "Work_Mode": 0, "Max_Designed_Power": 2000, "Input_Coefficient": 100.0, "Output_Coefficient": 100.0}, 
         "env": {"Inverter_Status": 1, "Detect_Status_1": 2, "Detect_Status_2": 0, "Inverter_Temp": 14}, 
         "events": {"Inverter_Alarm": 0, "Inverter_Fault": 0, "Inverter_Bitfield_1": 0, "Inverter_bitfield_2": 0},
         "grid": {"Voltage": 224.8, "Current": 0.73, "Frequency": 50.05, "Output_Power": 165.8}, 
         "input": {"pv1": {"Voltage": 35.3, "Current": 1.68, "Power": 59.6, "Daily_Generation": 0.04, "Total_Generation": 30.76}, 
                   "pv2": {"Voltage": 34.6, "Current": 1.38, "Power": 48.4, "Daily_Generation": 0.03, "Total_Generation": 27.91}, 
                   "pv3": {"Voltage": 34.6, "Current": 1.89, "Power": 65.5, "Daily_Generation": 0.05, "Total_Generation": 31.89}, 
                   "pv4": {"Voltage": 1.7, "Current": 0.01, "Power": 0.0, "Total_Generation": 15.58}}, 
         "total": {"Daily_Generation": 0.11, "Total_Generation": 101.36},
         "inv_unknown": {"Unknown_1": 512},
         "other": {"Output_Shutdown": 65535, "Rated_Level": 3, "Grid_Volt_Cal_Coef": 1024, "Prod_Compliance_Type": 6}
        })

def test_parse_4210_3026(batterie_data: bytes):
    i = InfosG3P(client_mode=False)
    i.db.clear()
    
    for key, update in i.parse (batterie_data, 0x42, 1, 0x3026):
        pass  #  side effect is calling generator i.parse()

    assert json.dumps(i.db) == json.dumps({
         "controller": {"Sensor_List": "3026", "Power_On_Time": 4684},
         "inverter": {"Serial_Number": "4101240701490314"}, 
         "batterie": {"pv1": {"Voltage": 33.86, "Current": 1.12}, 
                      "pv2": {"Voltage": 33.72, "Current": 0.0}, 
                      "Reg_38": 0, "Total_Generation": 20.8, "Status_1": 0, "Status_2": 0, 
                      "Voltage": 51.34, "Current": -0.02, "SOC": 10.0, 
                      "Temp_1": 15, "Temp_2": 15, "Temp_3": 15,
                      "out": {"Voltage": 0.14, "Current": 0.0, "Out_Status": 0, "Power": 0.0},
                      "Controller_Temp": 15, "Reg_74": 0, "Reg_76": 517, "Reg_78": 513,
                      "PV_Power": 37.9232, "Power": -1.0268000000000002},
        })

def test_parse_4210_3026_incomplete(batterie_data2: bytes):
    i = InfosG3P(client_mode=False)
    i.db.clear()
    
    for key, update in i.parse (batterie_data2, 0x42, 1, 0x3026):
        pass  #  side effect is calling generator i.parse()

    assert json.dumps(i.db) == json.dumps({
         "controller": {"Sensor_List": "3026", "Power_On_Time": 4684},
         "inverter": {"Serial_Number": "4101240701490314"}, 
         "batterie": {"pv1": {"Voltage": 33.86, "Current": 1.12}, 
                      "pv2": {"Voltage": 33.72, "Current": 0.0}, 
                      "Reg_38": 0, "Total_Generation": 20.8, "Status_1": 0, "Status_2": 0, 
                      "Voltage": 51.34, "Current": -0.02, "SOC": 10.0,
                      "Temp_1": 15, "Temp_2": 15,  "Temp_3": 15,
                      "out": {"Voltage": 0.14, "Current": None, "Out_Status": None, "Power": None},
                      "Controller_Temp": None, "Reg_74": None, "Reg_76": None, "Reg_78": None,
                      "PV_Power": 37.9232, "Power": -1.0268000000000002},
        })

def test_build_4210(inverter_data: bytes):
    i = InfosG3P(client_mode=False)
    i.db.clear()
    
    for key, update in i.parse (inverter_data, 0x42, 1, 0x02b0):
        pass  #  side effect is calling generator i.parse()

    build_msg = i.build(len(inverter_data), 0x42, 1, 0x02b0)
    for i in range(11, 31):
        build_msg[i] = inverter_data[i]
    assert inverter_data == build_msg    

def test_build_ha_conf1():
    i = InfosG3P(client_mode=False)
    i.static_init()                # initialize counter
    i.set_db_def_value(Register.SENSOR_LIST, "02b0")

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
    i.set_db_def_value(Register.SENSOR_LIST, "02b0")

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

def test_build_ha_conf5():
    i = InfosG3P(client_mode=True)
    i.static_init()                # initialize counter
    i.set_db_def_value(Register.SENSOR_LIST, "3026")

    tests = 0
    for d_json, comp, node_id, id in i.ha_confs(ha_prfx="tsun/", node_id="garagendach/", snr='123'):

        if id == 'out_power_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Out Power", "stat_t": "tsun/garagendach/batterie", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "out_power_123", "val_tpl": "{{ (value_json['out']['Power'] | int)}}", "unit_of_meas": "W", "dev": {"name": "Batterie", "sa": "Batterie", "via_device": "controller_123", "mdl": "TSOL-MSxx00", "mf": "TSUN", "ids": ["batterie_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1
        elif id == 'daily_gen_123':
            assert False
        elif id == 'volt_pv1_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Voltage", "stat_t": "tsun/garagendach/batterie", "dev_cla": "voltage", "stat_cla": "measurement", "uniq_id": "volt_pv1_123", "val_tpl": "{{ (value_json['pv1']['Voltage'] | float)}}", "unit_of_meas": "V", "ic": "mdi:gauge", "ent_cat": "diagnostic", "dev": {"name": "Module PV1", "sa": "Module PV1", "via_device": "batterie_123", "ids": ["bat_inp_pv1_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1
        elif id == 'volt_pv2_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Voltage", "stat_t": "tsun/garagendach/batterie", "dev_cla": "voltage", "stat_cla": "measurement", "uniq_id": "volt_pv2_123", "val_tpl": "{{ (value_json['pv2']['Voltage'] | float)}}", "unit_of_meas": "V", "ic": "mdi:gauge", "ent_cat": "diagnostic", "dev": {"name": "Module PV2", "sa": "Module PV2", "via_device": "batterie_123", "ids": ["bat_inp_pv2_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1
        elif id == 'signal_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({})
            tests +=1
        elif id == 'inv_count_456':
            assert False
        else:
            print(id)

    assert tests==4

def test_exception_and_calc(inverter_data: bytes):

    # patch table to convert temperature from °F to °C
    ofs = RegisterMap.map_02b0[0x420100d8]['offset']
    RegisterMap.map_02b0[0x420100d8]['quotient'] =  1.8
    RegisterMap.map_02b0[0x420100d8]['offset'] =  -32/1.8
    # map PV1_VOLTAGE to invalid register  
    RegisterMap.map_02b0[0x420100e0]['reg'] = Register.TEST_REG2
    # set invalid maping entry for OUTPUT_POWER (string instead of dict type) 
    backup = RegisterMap.map_02b0[0x420100de]
    RegisterMap.map_02b0[0x420100de] = 'invalid_entry'

    i = InfosG3P(client_mode=False)
    i.db.clear()
    
    for key, update in i.parse (inverter_data, 0x42, 1, 0x02b0):
        pass  #  side effect is calling generator i.parse()
    assert math.isclose(12.2222, round (i.get_db_value(Register.INVERTER_TEMP, 0),4), rel_tol=1e-09, abs_tol=1e-09)
    
    build_msg = i.build(len(inverter_data), 0x42, 1, 0x02b0)
    assert build_msg[32:0xde] == inverter_data[32:0xde]
    assert build_msg[0xde:0xe2] == b'\x00\x00\x00\x00'
    assert build_msg[0xe2:-1] == inverter_data[0xe2:-1]


    # remove a table entry and test parsing and building
    del RegisterMap.map_02b0[0x420100d8]['quotient']
    del RegisterMap.map_02b0[0x420100d8]['offset']

    i.db.clear()
    
    for key, update in i.parse (inverter_data, 0x42, 1, 0x02b0):
        pass  #  side effect is calling generator i.parse()
    assert 54 == i.get_db_value(Register.INVERTER_TEMP, 0)

    build_msg = i.build(len(inverter_data), 0x42, 1, 0x02b0)
    assert build_msg[32:0xd8] == inverter_data[32:0xd8]
    assert build_msg[0xd8:0xe2] == b'\x006\x00\x00\x02X\x00\x00\x00\x00'
    assert build_msg[0xe2:-1] == inverter_data[0xe2:-1]

    # test restore table 
    RegisterMap.map_02b0[0x420100d8]['offset'] = ofs
    RegisterMap.map_02b0[0x420100e0]['reg'] = Register.PV1_VOLTAGE # reset mapping
    RegisterMap.map_02b0[0x420100de] = backup # reset mapping

    # test orginial table 
    i.db.clear()    
    for key, update in i.parse (inverter_data, 0x42, 1, 0x02b0):
        pass  #  side effect is calling generator i.parse()
    assert 14 == i.get_db_value(Register.INVERTER_TEMP, 0)

    build_msg = i.build(len(inverter_data), 0x42, 1, 0x02b0)
    assert build_msg[32:-1] == inverter_data[32:-1]
