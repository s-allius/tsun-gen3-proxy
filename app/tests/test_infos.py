# test_with_pytest.py
import pytest, json
from app.src.infos import Infos

@pytest.fixture
def ContrDataSeq(): # Get Time Request message
    msg =   b'\x00\x00\x00\x15\x00\x09\x2b\xa8\x54\x10\x52\x53\x57\x5f\x34\x30\x30\x5f\x56\x31\x2e\x30\x30\x2e\x30\x36\x00\x09\x27\xc0\x54\x06\x52\x61\x79\x6d\x6f'
    msg +=  b'\x6e\x00\x09\x2f\x90\x54\x0b\x52\x53\x57\x2d\x31\x2d\x31\x30\x30\x30\x31\x00\x09\x5a\x88\x54\x0f\x74\x2e\x72\x61\x79\x6d\x6f\x6e\x69\x6f\x74\x2e\x63\x6f\x6d\x00\x09\x5a\xec\x54'
    msg +=  b'\x1c\x6c\x6f\x67\x67\x65\x72\x2e\x74\x61\x6c\x65\x6e\x74\x2d\x6d\x6f\x6e\x69\x74\x6f\x72\x69\x6e\x67\x2e\x63\x6f\x6d\x00\x0d\x00\x20\x49\x00\x00\x00\x01\x00\x0c\x35\x00\x49\x00'
    msg +=  b'\x00\x00\x64\x00\x0c\x96\xa8\x49\x00\x00\x00\x1d\x00\x0c\x7f\x38\x49\x00\x00\x00\x01\x00\x0c\xfc\x38\x49\x00\x00\x00\x01\x00\x0c\xf8\x50\x49\x00\x00\x01\x2c\x00\x0c\x63\xe0\x49'
    msg +=  b'\x00\x00\x00\x00\x00\x0c\x67\xc8\x49\x00\x00\x00\x00\x00\x0c\x50\x58\x49\x00\x00\x00\x01\x00\x09\x5e\x70\x49\x00\x00\x13\x8d\x00\x09\x5e\xd4\x49\x00\x00\x13\x8d\x00\x09\x5b\x50'
    msg +=  b'\x49\x00\x00\x00\x02\x00\x0d\x04\x08\x49\x00\x00\x00\x00\x00\x07\xa1\x84\x49\x00\x00\x00\x01\x00\x0c\x50\x59\x49\x00\x00\x00\x4c\x00\x0d\x1f\x60\x49\x00\x00\x00\x00'
    return msg

@pytest.fixture
def InvDataSeq(): # Data indication from the controller
    msg =   b'\x00\x00\x00\x06\x00\x00\x00\x0a\x54\x08\x4d\x69\x63\x72\x6f\x69\x6e\x76\x00\x00\x00\x14\x54\x04\x54\x53\x55\x4e\x00\x00\x00\x1E\x54\x07\x56\x35\x2e\x30\x2e\x31\x31\x00\x00\x00\x28'
    msg +=  b'\x54\x10\x54\x31\x37\x45\x37\x33\x30\x37\x30\x32\x31\x44\x30\x30\x36\x41\x00\x00\x00\x32\x54\x0a\x54\x53\x4f\x4c\x2d\x4d\x53\x36\x30\x30\x00\x00\x00\x3c\x54\x05\x41\x2c\x42\x2c\x43'
    return msg


def test_parse_control(ContrDataSeq):
    i = Infos()
    for key, result in i.parse (ContrDataSeq):
        pass

    assert json.dumps(i.db) == json.dumps(
{"collector": {"Collector_Fw_Version": "RSW_400_V1.00.06", "Chip_Type": "Raymon", "Chip_Model": "RSW-1-10001", "Trace_URL": "t.raymoniot.com", "Logger_URL": "logger.talent-monitoring.com"}, "controller": {"Signal_Strength": 100, "Power_On_Time": 29, "Data_Up_Interval": 300}})        

def test_parse_inverter(InvDataSeq):
    i = Infos()
    for key, result in i.parse (InvDataSeq):
        pass

    assert json.dumps(i.db) == json.dumps(
{"inverter": {"Product_Name": "Microinv", "Manufacturer": "TSUN", "Version": "V5.0.11", "Serial_Number": "T17E7307021D006A", "Equipment_Model": "TSOL-MS600"}})

def test_parse_cont_and_invert(ContrDataSeq, InvDataSeq):
    i = Infos()
    for key, result in i.parse (ContrDataSeq):
        pass

    for key, result in i.parse (InvDataSeq):
        pass

    assert json.dumps(i.db) == json.dumps(
    {
"collector": {"Collector_Fw_Version": "RSW_400_V1.00.06", "Chip_Type": "Raymon", "Chip_Model": "RSW-1-10001", "Trace_URL": "t.raymoniot.com", "Logger_URL": "logger.talent-monitoring.com"}, "controller": {"Signal_Strength": 100, "Power_On_Time": 29, "Data_Up_Interval": 300},
"inverter": {"Product_Name": "Microinv", "Manufacturer": "TSUN", "Version": "V5.0.11", "Serial_Number": "T17E7307021D006A", "Equipment_Model": "TSOL-MS600"}})


def test_build_ha_conf1(ContrDataSeq):
    i = Infos()
    tests = 0
    for d_json, comp, id in i.ha_confs(prfx="tsun/garagendach/", snr='123'):

        if id == 'out_power_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/grid", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "out_power_123", "val_tpl": "{{value_json['Output_Power'] | float}}", "unit_of_meas": "W", "dev": {"name": "Micro Inverter", "sa": "Micro Inverter", "via_device": "controller_123", "ids": ["inverter_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'daily_gen_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Daily Generation", "stat_t": "tsun/garagendach/total", "dev_cla": "energy", "stat_cla": "total_increasing", "uniq_id": "daily_gen_123", "val_tpl": "{{value_json['Daily_Generation'] | float}}", "unit_of_meas": "kWh", "ic": "mdi:solar-power-variant", "dev": {"name": "Micro Inverter", "sa": "Micro Inverter", "via_device": "controller_123", "ids": ["inverter_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv1_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv1_123", "val_tpl": "{{ (value_json['pv1']['Power'] | float)}}", "unit_of_meas": "W", "ic": "mdi:gauge", "dev": {"name": "Module PV1", "sa": "Module PV1", "via_device": "inverter_123", "ids": ["input_pv1_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv2_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv2_123", "val_tpl": "{{ (value_json['pv2']['Power'] | float)}}", "unit_of_meas": "W", "ic": "mdi:gauge", "dev": {"name": "Module PV2", "sa": "Module PV2", "via_device": "inverter_123", "ids": ["input_pv2_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'signal_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Signal Strength", "stat_t": "tsun/garagendach/controller", "dev_cla": None, "stat_cla": "measurement", "uniq_id": "signal_123", "val_tpl": "{{value_json[\'Signal_Strength\'] | int}}", "unit_of_meas": "%", "ic": "mdi:wifi", "dev": {"name": "Controller", "sa": "Controller", "ids": ["controller_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1
    assert tests==5

def test_build_ha_conf2(ContrDataSeq, InvDataSeq):
    i = Infos()
    for key, result in i.parse (ContrDataSeq):
        pass

    for key, result in i.parse (InvDataSeq):
        pass

    tests = 0
    for d_json, comp, id in i.ha_confs(prfx="tsun/garagendach/", snr='123'):

        if id == 'out_power_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/grid", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "out_power_123", "val_tpl": "{{value_json['Output_Power'] | float}}", "unit_of_meas": "W", "dev": {"name": "Micro Inverter", "sa": "Micro Inverter", "via_device": "controller_123", "mdl": "TSOL-MS600", "mf": "TSUN", "sw": "V5.0.11", "ids": ["inverter_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'daily_gen_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Daily Generation", "stat_t": "tsun/garagendach/total", "dev_cla": "energy", "stat_cla": "total_increasing", "uniq_id": "daily_gen_123", "val_tpl": "{{value_json['Daily_Generation'] | float}}", "unit_of_meas": "kWh", "ic": "mdi:solar-power-variant", "dev": {"name": "Micro Inverter", "sa": "Micro Inverter", "via_device": "controller_123", "mdl": "TSOL-MS600", "mf": "TSUN", "sw": "V5.0.11", "ids": ["inverter_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv1_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv1_123", "val_tpl": "{{ (value_json['pv1']['Power'] | float)}}", "unit_of_meas": "W", "ic": "mdi:gauge", "dev": {"name": "Module PV1", "sa": "Module PV1", "via_device": "inverter_123", "ids": ["input_pv1_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv2_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv2_123", "val_tpl": "{{ (value_json['pv2']['Power'] | float)}}", "unit_of_meas": "W", "ic": "mdi:gauge", "dev": {"name": "Module PV2", "sa": "Module PV2", "via_device": "inverter_123", "ids": ["input_pv2_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'signal_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Signal Strength", "stat_t": "tsun/garagendach/controller", "dev_cla": None, "stat_cla": "measurement", "uniq_id": "signal_123", "val_tpl": "{{value_json[\'Signal_Strength\'] | int}}", "unit_of_meas": "%", "ic": "mdi:wifi", "dev": {"name": "Controller", "sa": "Controller", "mdl": "RSW-1-10001", "mf": "Raymon", "sw": "RSW_400_V1.00.06", "ids": ["controller_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1
    assert tests==5
