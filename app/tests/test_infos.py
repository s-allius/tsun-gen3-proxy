# test_with_pytest.py
import pytest
import json, math
import logging
from app.src.infos import Register, ClrAtMidnight
from app.src.infos import Infos

def test_statistic_counter():
    i = Infos()
    val = i.dev_value("Test-String")
    assert val == "Test-String"

    val = i.dev_value(0xffffffff)  # invalid addr
    assert val == None
    
    val = i.dev_value(Register.INVERTER_CNT)  # valid addr but not initiliazed
    assert val == None or val == 0

    i.static_init()                # initialize counter
    assert json.dumps(i.stat) == json.dumps({"proxy": {"Inverter_Cnt": 0, "Unknown_SNR": 0, "Unknown_Msg": 0, "Invalid_Data_Type": 0, "Internal_Error": 0,"Unknown_Ctrl": 0, "OTA_Start_Msg": 0, "SW_Exception": 0, "Invalid_Msg_Format": 0, "AT_Command": 0, "AT_Command_Blocked": 0, "Modbus_Command": 0}})
                                            
    val = i.dev_value(Register.INVERTER_CNT)  # valid and initiliazed addr
    assert val == 0

    i.inc_counter('Inverter_Cnt')
    assert json.dumps(i.stat) == json.dumps({"proxy": {"Inverter_Cnt": 1, "Unknown_SNR": 0, "Unknown_Msg": 0, "Invalid_Data_Type": 0, "Internal_Error": 0,"Unknown_Ctrl": 0, "OTA_Start_Msg": 0, "SW_Exception": 0, "Invalid_Msg_Format": 0, "AT_Command": 0, "AT_Command_Blocked": 0, "Modbus_Command": 0}})
    val = i.dev_value(Register.INVERTER_CNT)
    assert val == 1

    i.dec_counter('Inverter_Cnt')
    val = i.dev_value(Register.INVERTER_CNT)
    assert val == 0

def test_dep_rules():
    i = Infos()
    i.static_init()                # initialize counter

    res = i.ignore_this_device({})
    assert res == True

    res = i.ignore_this_device({'reg':0xffffffff})
    assert res == True

    i.inc_counter('Inverter_Cnt')    # is 1
    val = i.dev_value(Register.INVERTER_CNT)
    assert val == 1
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT})
    assert res == True
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT, 'less_eq': 2})
    assert res == False
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT, 'gte': 2})
    assert res == True

    i.inc_counter('Inverter_Cnt')   # is 2
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT, 'less_eq': 2})
    assert res == False
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT, 'gte': 2})
    assert res == False

    i.inc_counter('Inverter_Cnt')   # is 3
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT, 'less_eq': 2})
    assert res == True
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT, 'gte': 2})
    assert res == False

def test_table_definition():
    i = Infos()
    i.static_init()                # initialize counter

    val = i.dev_value(Register.INTERNAL_ERROR)  # check internal error counter
    assert val == 0

    # for d_json, comp, node_id, id in i.ha_confs(ha_prfx="tsun/", node_id="garagendach/", snr='123', sug_area = 'roof'):
    #    pass
    for reg in Register:
        i.ha_conf(reg, ha_prfx="tsun/", node_id="garagendach/", snr='123', singleton=False, sug_area = 'roof')  # noqa: E501


    for d_json, comp, node_id, id in i.ha_proxy_confs(ha_prfx="tsun/", node_id = 'proxy/', snr = '456'):
        pass  # sideeffect is calling generator i.ha_proxy_confs()

    val = i.dev_value(Register.INTERNAL_ERROR)  # check internal error counter
    assert val == 0

    # test missing 'fmt' value
    i.info_defs[Register.TEST_REG1] =  {'name':['proxy', 'Internal_Test1'],  'singleton': True, 'ha':{'dev':'proxy', 'dev_cla': None,       'stat_cla': None, 'id':'intern_test1_'}}

    tests = 0
    for d_json, comp, node_id, id in i.ha_proxy_confs(ha_prfx="tsun/", node_id = 'proxy/', snr = '456'):
        if id == 'intern_test1_456':
            tests +=1

    assert tests == 1

    val = i.dev_value(Register.INTERNAL_ERROR)  # check internal error counter
    assert val == 1

    # test missing 'dev' value
    i.info_defs[Register.TEST_REG1] =  {'name':['proxy', 'Internal_Test2'],  'singleton': True, 'ha':{'dev_cla': None,       'stat_cla': None, 'id':'intern_test2_',  'fmt':'| int'}}
    tests = 0
    for d_json, comp, node_id, id in i.ha_proxy_confs(ha_prfx="tsun/", node_id = 'proxy/', snr = '456'):
        if id == 'intern_test2_456':
            tests +=1

    assert tests == 1

    val = i.dev_value(Register.INTERNAL_ERROR)  # check internal error counter
    assert val == 2



    # test invalid 'via' value
    i.info_devs['test_dev'] = {'via':'xyz',   'name':'Module PV1'}

    i.info_defs[Register.TEST_REG1] =  {'name':['proxy', 'Internal_Test2'],  'singleton': True, 'ha':{'dev':'test_dev', 'dev_cla': None,       'stat_cla': None, 'id':'intern_test2_',  'fmt':'| int'}}
    tests = 0
    for d_json, comp, node_id, id in i.ha_proxy_confs(ha_prfx="tsun/", node_id = 'proxy/', snr = '456'):
        if id == 'intern_test2_456':
            tests +=1

    assert tests == 1

    val = i.dev_value(Register.INTERNAL_ERROR)  # check internal error counter
    assert val == 3

def test_table_remove():
    i = Infos()
    i.static_init()                # initialize counter

    val = i.dev_value(Register.INTERNAL_ERROR)  # check internal error counter
    assert val == 0

    # for d_json, comp, node_id, id in i.ha_confs(ha_prfx="tsun/", node_id="garagendach/", snr='123', sug_area = 'roof'):
    #    pass
    test = 0
    for reg in Register:
        res = i.ha_remove(reg, node_id="garagendach/", snr='123')  # noqa: E501
        if reg == Register.INVERTER_STATUS:
            test += 1
            assert res == ('{}', 'sensor', 'garagendach/', 'inv_status_123')
        elif reg == Register.COLLECT_INTERVAL:
            test += 1
            assert res == ('{}', 'sensor', 'garagendach/', 'data_collect_intval_123')

    assert test == 2
    val = i.dev_value(Register.INTERNAL_ERROR)  # check internal error counter
    assert val == 0


def test_clr_at_midnight():
    i = Infos()
    i.static_init()                # initialize counter
    i.set_db_def_value(Register.NO_INPUTS, 2)
    val = i.dev_value(Register.NO_INPUTS)  # valid addr but not initiliazed     
    assert val == 2
    i.info_defs[Register.TEST_REG1] = {  # add a entry with incomplete ha definition 
        'name': ['test', 'grp', 'REG_1'], 'ha': {'dev_cla': None }
        }
    i.reg_clr_at_midnight('tsun/inv_1/')
    # tsun/inv_2/input
    assert json.dumps(ClrAtMidnight.db['tsun/inv_1/total']) == json.dumps({'Daily_Generation': 0})
    assert json.dumps(ClrAtMidnight.db['tsun/inv_1/input']) == json.dumps({"pv1": {"Daily_Generation": 0}, "pv2": {"Daily_Generation": 0}})

    i.reg_clr_at_midnight('tsun/inv_1/')
    assert json.dumps(ClrAtMidnight.db['tsun/inv_1/total']) == json.dumps({'Daily_Generation': 0})
    assert json.dumps(ClrAtMidnight.db['tsun/inv_1/input']) == json.dumps({"pv1": {"Daily_Generation": 0}, "pv2": {"Daily_Generation": 0}})

    test = 0
    for key, data in ClrAtMidnight.elm():
        if key == 'tsun/inv_1/total':
            assert json.dumps(data) == json.dumps({'Daily_Generation': 0})
            test += 1
        elif key == 'tsun/inv_1/input':
            assert json.dumps(data) == json.dumps({"pv1": {"Daily_Generation": 0}, "pv2": {"Daily_Generation": 0}})
            test += 1
    assert test == 2
    assert json.dumps(ClrAtMidnight.db) == json.dumps({})

    i.reg_clr_at_midnight('tsun/inv_1/')

def test_pv_module_config():
    i = Infos()
    # i.set_db_def_value(Register.NO_INPUTS, 2)

    dt = {
        'pv1':{'manufacturer':'TSUN1','type': 'Module 100W'},
        'pv2':{'manufacturer':'TSUN2'},
        'pv3':{'manufacturer':'TSUN3','type': 'Module 300W'},
        'pv4':{'type': 'Module 400W'},
        'pv5':{},
                 }
    i.set_pv_module_details(dt)
    assert 'TSUN1' == i.dev_value(Register.PV1_MANUFACTURER)
    assert 'TSUN2' == i.dev_value(Register.PV2_MANUFACTURER)
    assert 'TSUN3' == i.dev_value(Register.PV3_MANUFACTURER)
    assert None == i.dev_value(Register.PV4_MANUFACTURER)
    assert None == i.dev_value(Register.PV5_MANUFACTURER)
    assert 'Module 100W' == i.dev_value(Register.PV1_MODEL)
    assert  None == i.dev_value(Register.PV2_MODEL)
    assert 'Module 300W' == i.dev_value(Register.PV3_MODEL)
    assert 'Module 400W' == i.dev_value(Register.PV4_MODEL)
    assert  None == i.dev_value(Register.PV5_MODEL)

def test_broken_info_defs():
    i = Infos()
    val = i.get_db_value(Register.NO_INPUTS, 666)
    assert val == 666
    i.info_defs[Register.TEST_REG1] = 'test'  # add a string instead of a dict 
    val = i.get_db_value(Register.TEST_REG1, 666)
    assert val == 666
    i.set_db_def_value(Register.TEST_REG1, 2)
    del i.info_defs[Register.TEST_REG1]       # delete the broken entry 

def test_get_value():
    i = Infos()
    assert None == i.get_db_value(Register.PV1_VOLTAGE, None)
    assert None == i.get_db_value(Register.PV2_VOLTAGE, None)

    i.set_db_def_value(Register.PV1_VOLTAGE, 30) 
    assert 30 == i.get_db_value(Register.PV1_VOLTAGE, None)
    assert None == i.get_db_value(Register.PV2_VOLTAGE, None)

    i.set_db_def_value(Register.PV2_VOLTAGE, 30.3) 
    assert 30 == i.get_db_value(Register.PV1_VOLTAGE, None)
    assert math.isclose(30.3,i.get_db_value(Register.PV2_VOLTAGE, None), rel_tol=1e-09, abs_tol=1e-09)

def test_update_value():
    i = Infos()
    assert None == i.get_db_value(Register.PV1_VOLTAGE, None)

    keys = i.info_defs[Register.PV1_VOLTAGE]['name']
    _, update = i.update_db(keys, True, 30) 
    assert update == True
    assert 30 == i.get_db_value(Register.PV1_VOLTAGE, None)

    keys = i.info_defs[Register.PV1_VOLTAGE]['name']
    _, update = i.update_db(keys, True, 30) 
    assert update == False
    assert 30 == i.get_db_value(Register.PV1_VOLTAGE, None)

    keys = i.info_defs[Register.PV1_VOLTAGE]['name']
    _, update = i.update_db(keys, False, 29) 
    assert update == True
    assert 29 == i.get_db_value(Register.PV1_VOLTAGE, None)

def test_key_obj():
    i = Infos()
    keys, level, unit, must_incr = i._key_obj(Register.PV1_VOLTAGE)
    assert keys == ['input', 'pv1', 'Voltage']
    assert level == logging.DEBUG
    assert unit == 'V'
    assert must_incr == False

    keys, level, unit, must_incr = i._key_obj(Register.PV1_DAILY_GENERATION)
    assert keys == ['input', 'pv1', 'Daily_Generation'] 
    assert level == logging.DEBUG
    assert unit == 'kWh'
    assert must_incr == True
