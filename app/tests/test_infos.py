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


def test_parse_control(ContrDataSeq):
    i = Infos()
    for key, result in i.parse (ContrDataSeq):
        pass

    assert json.dumps(i.db) == json.dumps(
{"collector": {"Collector_Fw_Version": "RSW_400_V1.00.06", "Chip_Type": "Raymon", "Chip_Model": "RSW-1-10001", "Trace_URL": "t.raymoniot.com", "Logger_URL": "logger.talent-monitoring.com", "Data_Up_Interval": 300}, "env": {"Signal_Strength": 100}, "total": {"Power_On_Time": 29}})        
        
def test_build_ha_conf():
    i = Infos()
    d_json, id = next (i.ha_confs(prfx="tsun/garagendach/", snr='123'))
    assert id == 'out_power_123'
    assert  d_json == json.dumps({"name": "Actual Power", "stat_t": "tsun/garagendach/grid", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "out_power_123", "val_tpl": "{{value_json['Output_Power'] | float}}", "unit_of_meas": "W", "dev": {"name": "Microinverter", "mdl": "MS-600", "ids": ["inverter_123"], "mf": "TSUN", "sa": "", "sw": "0.01", "hw": "Hw0.01"}})

def test_build_ha_conf2():
    i = Infos()
    tests = 0
    for d_json, id in i.ha_confs(prfx="tsun/garagendach/", snr='123'):

        if id == 'out_power_123':
            assert  d_json == json.dumps({"name": "Actual Power", "stat_t": "tsun/garagendach/grid", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "out_power_123", "val_tpl": "{{value_json['Output_Power'] | float}}", "unit_of_meas": "W", "dev": {"name": "Microinverter", "mdl": "MS-600", "ids": ["inverter_123"], "mf": "TSUN", "sa": "", "sw": "0.01", "hw": "Hw0.01"}})
            tests +=1

        elif id == 'daily_gen_123':
            assert  d_json == json.dumps({"name": "Daily Generation", "stat_t": "tsun/garagendach/total", "dev_cla": "energy", "stat_cla": "total_increasing", "uniq_id": "daily_gen_123", "val_tpl": "{{value_json['Daily_Generation'] | float}}", "unit_of_meas": "kWh", "dev": {"name": "Microinverter", "mdl": "MS-600", "ids": ["inverter_123"], "mf": "TSUN", "sa": "", "sw": "0.01", "hw": "Hw0.01"}})
            tests +=1

        elif id == 'power_pv1_123':
            assert  d_json == json.dumps({"name": "Power PV1", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv1_123", "val_tpl": "{{ (value_json['pv1']['Power'] | float)}}", "unit_of_meas": "W", "dev": {"name": "Microinverter", "mdl": "MS-600", "ids": ["inverter_123"], "mf": "TSUN", "sa": "", "sw": "0.01", "hw": "Hw0.01"}})
            tests +=1

        elif id == 'total_gen_123':
            assert  d_json == json.dumps({"name": "Total Generation", "stat_t": "tsun/garagendach/total", "dev_cla": "energy", "stat_cla": "total", "uniq_id": "total_gen_123", "val_tpl": "{{value_json['Total_Generation'] | float}}", "unit_of_meas": "kWh", "icon": "mdi:solar-power", "dev": {"name": "Microinverter", "mdl": "MS-600", "ids": ["inverter_123"], "mf": "TSUN", "sa": "", "sw": "0.01", "hw": "Hw0.01"}})
            tests +=1
    assert tests==4

def test_build_ha_conf3():
    i = Infos()
    for d_json, id in i.ha_confs(prfx="tsun/garagendach/", snr='123'):
        pass
