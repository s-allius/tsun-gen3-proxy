import logging
import json
import os
from enum import Enum
from typing import Generator


class ProxyMode(Enum):
    SERVER = 1
    CLIENT = 2


class Register(Enum):
    COLLECTOR_FW_VERSION = 1
    CHIP_TYPE = 2
    CHIP_MODEL = 3
    TRACE_URL = 4
    LOGGER_URL = 5
    PRODUCT_NAME = 20
    MANUFACTURER = 21
    VERSION = 22
    SERIAL_NUMBER = 23
    EQUIPMENT_MODEL = 24
    NO_INPUTS = 25
    MAX_DESIGNED_POWER = 26
    OUTPUT_COEFFICIENT = 27
    INVERTER_CNT = 50
    UNKNOWN_SNR = 51
    UNKNOWN_MSG = 52
    INVALID_DATA_TYPE = 53
    INTERNAL_ERROR = 54
    UNKNOWN_CTRL = 55
    OTA_START_MSG = 56
    SW_EXCEPTION = 57
    INVALID_MSG_FMT = 58
    AT_COMMAND = 59
    MODBUS_COMMAND = 60
    AT_COMMAND_BLOCKED = 61
    OUTPUT_POWER = 83
    RATED_POWER = 84
    INVERTER_TEMP = 85
    INVERTER_STATUS = 86
    PV1_VOLTAGE = 100
    PV1_CURRENT = 101
    PV1_POWER = 102
    PV1_MANUFACTURER = 103
    PV1_MODEL = 104
    PV2_VOLTAGE = 110
    PV2_CURRENT = 111
    PV2_POWER = 112
    PV2_MANUFACTURER = 113
    PV2_MODEL = 114
    PV3_VOLTAGE = 120
    PV3_CURRENT = 121
    PV3_POWER = 122
    PV3_MANUFACTURER = 123
    PV3_MODEL = 124
    PV4_VOLTAGE = 130
    PV4_CURRENT = 131
    PV4_POWER = 132
    PV4_MANUFACTURER = 133
    PV4_MODEL = 134
    PV5_VOLTAGE = 140
    PV5_CURRENT = 141
    PV5_POWER = 142
    PV5_MANUFACTURER = 143
    PV5_MODEL = 144
    PV6_VOLTAGE = 150
    PV6_CURRENT = 151
    PV6_POWER = 152
    PV6_MANUFACTURER = 153
    PV6_MODEL = 154
    PV1_DAILY_GENERATION = 200
    PV1_TOTAL_GENERATION = 201
    PV2_DAILY_GENERATION = 210
    PV2_TOTAL_GENERATION = 211
    PV3_DAILY_GENERATION = 220
    PV3_TOTAL_GENERATION = 221
    PV4_DAILY_GENERATION = 230
    PV4_TOTAL_GENERATION = 231
    PV5_DAILY_GENERATION = 240
    PV5_TOTAL_GENERATION = 241
    PV6_DAILY_GENERATION = 250
    PV6_TOTAL_GENERATION = 251
    GRID_VOLTAGE = 300
    GRID_CURRENT = 301
    GRID_FREQUENCY = 302
    DAILY_GENERATION = 303
    TOTAL_GENERATION = 304
    COMMUNICATION_TYPE = 400
    SIGNAL_STRENGTH = 401
    POWER_ON_TIME = 402
    COLLECT_INTERVAL = 403
    DATA_UP_INTERVAL = 404
    CONNECT_COUNT = 405
    HEARTBEAT_INTERVAL = 406
    IP_ADDRESS = 407
    POLLING_INTERVAL = 408
    SENSOR_LIST = 409
    EVENT_401 = 500
    EVENT_402 = 501
    EVENT_403 = 502
    EVENT_404 = 503
    EVENT_405 = 504
    EVENT_406 = 505
    EVENT_407 = 506
    EVENT_408 = 507
    EVENT_409 = 508
    EVENT_410 = 509
    EVENT_411 = 510
    EVENT_412 = 511
    EVENT_413 = 512
    EVENT_414 = 513
    EVENT_415 = 514
    EVENT_416 = 515
    TS_INPUT = 600
    TS_GRID = 601
    TS_TOTAL = 602
    VALUE_1 = 9000
    TEST_REG1 = 10000
    TEST_REG2 = 10001


class ClrAtMidnight:
    __clr_at_midnight = [Register.PV1_DAILY_GENERATION, Register.PV2_DAILY_GENERATION, Register.PV3_DAILY_GENERATION, Register.PV4_DAILY_GENERATION, Register.PV5_DAILY_GENERATION, Register.PV6_DAILY_GENERATION, Register.DAILY_GENERATION]   # noqa: E501
    db = {}

    @classmethod
    def add(cls, keys: list, prfx: str, reg: Register) -> None:
        if reg not in cls.__clr_at_midnight:
            return

        prfx += f'{keys[0]}'
        db_dict = cls.db
        if prfx not in db_dict:
            db_dict[prfx] = {}
        db_dict = db_dict[prfx]

        for key in keys[1:-1]:
            if key not in db_dict:
                db_dict[key] = {}
            db_dict = db_dict[key]
        db_dict[keys[-1]] = 0

    @classmethod
    def elm(cls) -> Generator[tuple[str, dict], None, None]:
        for reg, name in cls.db.items():
            yield reg, name
        cls.db = {}


class Infos:
    stat = {}
    app_name = os.getenv('SERVICE_NAME', 'proxy')
    version = os.getenv('VERSION', 'unknown')

    new_stat_data = {}

    @classmethod
    def static_init(cls):
        logging.debug('Initialize proxy statistics')
        # init proxy counter in the class.stat dictionary
        cls.stat['proxy'] = {}
        for key in cls.__info_defs:
            name = cls.__info_defs[key]['name']
            if name[0] == 'proxy':
                cls.stat['proxy'][name[1]] = 0

        # add values from the environment to the device definition table
        prxy = cls.__info_devs['proxy']
        prxy['sw'] = cls.version
        prxy['mdl'] = cls.app_name

    def __init__(self):
        self.db = {}
        self.tracer = logging.getLogger('data')

    __info_devs = {
        'proxy':      {'singleton': True,   'name': 'Proxy', 'mf': 'Stefan Allius'},  # noqa: E501
        'controller': {'via': 'proxy',      'name': 'Controller',     'mdl': Register.CHIP_MODEL, 'mf': Register.CHIP_TYPE, 'sw': Register.COLLECTOR_FW_VERSION},  # noqa: E501
        'inverter':   {'via': 'controller', 'name': 'Micro Inverter', 'mdl': Register.EQUIPMENT_MODEL, 'mf': Register.MANUFACTURER, 'sw': Register.VERSION},  # noqa: E501
        'input_pv1':  {'via': 'inverter',   'name': 'Module PV1', 'mdl': Register.PV1_MODEL, 'mf': Register.PV1_MANUFACTURER},  # noqa: E501
        'input_pv2':  {'via': 'inverter',   'name': 'Module PV2', 'mdl': Register.PV2_MODEL, 'mf': Register.PV2_MANUFACTURER, 'dep': {'reg': Register.NO_INPUTS, 'gte': 2}},  # noqa: E501
        'input_pv3':  {'via': 'inverter',   'name': 'Module PV3', 'mdl': Register.PV3_MODEL, 'mf': Register.PV3_MANUFACTURER, 'dep': {'reg': Register.NO_INPUTS, 'gte': 3}},  # noqa: E501
        'input_pv4':  {'via': 'inverter',   'name': 'Module PV4', 'mdl': Register.PV4_MODEL, 'mf': Register.PV4_MANUFACTURER, 'dep': {'reg': Register.NO_INPUTS, 'gte': 4}},  # noqa: E501
        'input_pv5':  {'via': 'inverter',   'name': 'Module PV5', 'mdl': Register.PV5_MODEL, 'mf': Register.PV5_MANUFACTURER, 'dep': {'reg': Register.NO_INPUTS, 'gte': 5}},  # noqa: E501
        'input_pv6':  {'via': 'inverter',   'name': 'Module PV6', 'mdl': Register.PV6_MODEL, 'mf': Register.PV6_MANUFACTURER, 'dep': {'reg': Register.NO_INPUTS, 'gte': 6}},  # noqa: E501
    }

    __comm_type_val_tpl = "{%set com_types = ['n/a','Wi-Fi', 'G4', 'G5', 'GPRS'] %}{{com_types[value_json['Communication_Type']|int(0)]|default(value_json['Communication_Type'])}}"    # noqa: E501
    __status_type_val_tpl = "{%set inv_status = ['Off-line', 'On-grid', 'Off-grid'] %}{{inv_status[value_json['Inverter_Status']|int(0)]|default(value_json['Inverter_Status'])}}"    # noqa: E501
    __rated_power_val_tpl = "{% if 'Rated_Power' in value_json and value_json['Rated_Power'] != None %}{{value_json['Rated_Power']|string() +' W'}}{% else %}{{ this.state }}{% endif %}"  # noqa: E501
    __designed_power_val_tpl = '''
{% if 'Max_Designed_Power' in value_json and
      value_json['Max_Designed_Power'] != None %}
  {% if value_json['Max_Designed_Power'] | int(0xffff) < 0x8000 %}
    {{value_json['Max_Designed_Power']|string() +' W'}}
  {% else %}
    n/a
  {% endif %}
{% else %}
  {{ this.state }}
{% endif %}
'''
    __output_coef_val_tpl = "{% if 'Output_Coefficient' in value_json and value_json['Output_Coefficient'] != None %}{{value_json['Output_Coefficient']|string() +' %'}}{% else %}{{ this.state }}{% endif %}"  # noqa: E501

    __info_defs = {
        # collector values used for device registration:
        Register.COLLECTOR_FW_VERSION:  {'name': ['collector', 'Collector_Fw_Version'],       'level': logging.INFO,  'unit': ''},  # noqa: E501
        Register.CHIP_TYPE:  {'name': ['collector', 'Chip_Type'],        'singleton': False,  'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.CHIP_MODEL: {'name': ['collector', 'Chip_Model'],       'singleton': False,  'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.TRACE_URL:  {'name': ['collector', 'Trace_URL'],        'singleton': False,  'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.LOGGER_URL: {'name': ['collector', 'Logger_URL'],       'singleton': False,  'level': logging.DEBUG, 'unit': ''},  # noqa: E501

        # inverter values used for device registration:
        Register.PRODUCT_NAME:    {'name': ['inverter', 'Product_Name'],           'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.MANUFACTURER:    {'name': ['inverter', 'Manufacturer'],           'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.VERSION:         {'name': ['inverter', 'Version'],                'level': logging.INFO,  'unit': ''},  # noqa: E501
        Register.SERIAL_NUMBER:   {'name': ['inverter', 'Serial_Number'],          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EQUIPMENT_MODEL: {'name': ['inverter', 'Equipment_Model'],        'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.NO_INPUTS:       {'name': ['inverter', 'No_Inputs'],              'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.MAX_DESIGNED_POWER: {'name': ['inverter',  'Max_Designed_Power'], 'level': logging.INFO,  'unit': 'W',    'ha': {'dev': 'inverter', 'dev_cla': None, 'stat_cla': None, 'id': 'designed_power_', 'val_tpl': __designed_power_val_tpl, 'name': 'Max Designed Power', 'icon': 'mdi:lightning-bolt', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.RATED_POWER:        {'name': ['inverter',  'Rated_Power'],        'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'inverter', 'dev_cla': None, 'stat_cla': None, 'id': 'rated_power_',    'val_tpl': __rated_power_val_tpl,    'name': 'Rated Power',        'icon': 'mdi:lightning-bolt', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.OUTPUT_COEFFICIENT: {'name': ['inverter',  'Output_Coefficient'], 'level': logging.INFO,  'unit': '%',    'ha': {'dev': 'inverter', 'dev_cla': None, 'stat_cla': None, 'id': 'output_coef_',    'val_tpl': __output_coef_val_tpl,    'name': 'Output Coefficient', 'icon': 'mdi:lightning-bolt', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV1_MANUFACTURER: {'name': ['inverter', 'PV1_Manufacturer'],      'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.PV1_MODEL:        {'name': ['inverter', 'PV1_Model'],             'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.PV2_MANUFACTURER: {'name': ['inverter', 'PV2_Manufacturer'],      'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.PV2_MODEL:        {'name': ['inverter', 'PV2_Model'],             'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.PV3_MANUFACTURER: {'name': ['inverter', 'PV3_Manufacturer'],      'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.PV3_MODEL:        {'name': ['inverter', 'PV3_Model'],             'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.PV4_MANUFACTURER: {'name': ['inverter', 'PV4_Manufacturer'],      'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.PV4_MODEL:        {'name': ['inverter', 'PV4_Model'],             'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.PV5_MANUFACTURER: {'name': ['inverter', 'PV5_Manufacturer'],      'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.PV5_MODEL:        {'name': ['inverter', 'PV5_Model'],             'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.PV6_MANUFACTURER: {'name': ['inverter', 'PV6_Manufacturer'],      'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.PV6_MODEL:        {'name': ['inverter', 'PV6_Model'],             'level': logging.DEBUG, 'unit': ''},  # noqa: E501

        # proxy:
        Register.INVERTER_CNT:       {'name': ['proxy', 'Inverter_Cnt'],       'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'inv_count_',     'fmt': '| int', 'name': 'Active Inverter Connections',    'icon': 'mdi:counter'}},  # noqa: E501
        Register.UNKNOWN_SNR:        {'name': ['proxy', 'Unknown_SNR'],        'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'unknown_snr_',   'fmt': '| int', 'name': 'Unknown Serial No',    'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.UNKNOWN_MSG:        {'name': ['proxy', 'Unknown_Msg'],        'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'unknown_msg_',   'fmt': '| int', 'name': 'Unknown Msg Type',     'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.INVALID_DATA_TYPE:  {'name': ['proxy', 'Invalid_Data_Type'],  'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'inv_data_type_', 'fmt': '| int', 'name': 'Invalid Data Type',    'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.INTERNAL_ERROR:     {'name': ['proxy', 'Internal_Error'],     'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'intern_err_',    'fmt': '| int', 'name': 'Internal Error',       'icon': 'mdi:counter', 'ent_cat': 'diagnostic', 'en': False}},  # noqa: E501
        Register.UNKNOWN_CTRL:       {'name': ['proxy', 'Unknown_Ctrl'],       'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'unknown_ctrl_',  'fmt': '| int', 'name': 'Unknown Control Type', 'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.OTA_START_MSG:      {'name': ['proxy', 'OTA_Start_Msg'],      'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'ota_start_cmd_', 'fmt': '| int', 'name': 'OTA Start Cmd',        'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.SW_EXCEPTION:       {'name': ['proxy', 'SW_Exception'],       'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'sw_exception_',  'fmt': '| int', 'name': 'Internal SW Exception', 'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.INVALID_MSG_FMT:    {'name': ['proxy', 'Invalid_Msg_Format'], 'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'inv_msg_fmt_',   'fmt': '| int', 'name': 'Invalid Message Format', 'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.AT_COMMAND:         {'name': ['proxy', 'AT_Command'],         'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'at_cmd_',        'fmt': '| int', 'name': 'AT Command',           'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.AT_COMMAND_BLOCKED: {'name': ['proxy', 'AT_Command_Blocked'], 'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'at_cmd_blocked_', 'fmt': '| int', 'name': 'AT Command Blocked',   'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.MODBUS_COMMAND:     {'name': ['proxy', 'Modbus_Command'],     'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'modbus_cmd_',    'fmt': '| int', 'name': 'Modbus Command',       'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        # 0xffffff03:  {'name':['proxy', 'Voltage'],                        'level': logging.DEBUG, 'unit': 'V',    'ha':{'dev':'proxy', 'dev_cla': 'voltage',     'stat_cla': 'measurement', 'id':'proxy_volt_',  'fmt':'| float','name': 'Grid Voltage'}},  # noqa: E501

        # events
        Register.EVENT_401:  {'name': ['events', '401_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_402:  {'name': ['events', '402_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_403:  {'name': ['events', '403_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_404:  {'name': ['events', '404_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_405:  {'name': ['events', '405_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_406:  {'name': ['events', '406_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_407:  {'name': ['events', '407_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_408:  {'name': ['events', '408_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_409:  {'name': ['events', '409_No_Utility'],                'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_410:  {'name': ['events', '410_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_411:  {'name': ['events', '411_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_412:  {'name': ['events', '412_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_413:  {'name': ['events', '413_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_414:  {'name': ['events', '414_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_415:  {'name': ['events', '415_GridFreqOverRating'],        'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EVENT_416:  {'name': ['events', '416_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501

        # grid measures:
        Register.TS_GRID:         {'name': ['grid', 'Timestamp'],                  'level': logging.INFO,  'unit': ''},  # noqa: E501
        Register.GRID_VOLTAGE:    {'name': ['grid', 'Voltage'],                    'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'inverter', 'dev_cla': 'voltage',     'stat_cla': 'measurement', 'id': 'out_volt_',  'fmt': '| float', 'name': 'Grid Voltage', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.GRID_CURRENT:    {'name': ['grid', 'Current'],                    'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'inverter', 'dev_cla': 'current',     'stat_cla': 'measurement', 'id': 'out_cur_',   'fmt': '| float', 'name': 'Grid Current', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.GRID_FREQUENCY:  {'name': ['grid', 'Frequency'],                  'level': logging.DEBUG, 'unit': 'Hz',   'ha': {'dev': 'inverter', 'dev_cla': 'frequency',   'stat_cla': 'measurement', 'id': 'out_freq_',  'fmt': '| float', 'name': 'Grid Frequency', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.OUTPUT_POWER:    {'name': ['grid', 'Output_Power'],               'level': logging.INFO,  'unit': 'W',    'ha': {'dev': 'inverter', 'dev_cla': 'power',       'stat_cla': 'measurement', 'id': 'out_power_', 'fmt': '| float', 'name': 'Power'}},  # noqa: E501
        Register.INVERTER_TEMP:   {'name': ['env',  'Inverter_Temp'],              'level': logging.DEBUG, 'unit': '°C',   'ha': {'dev': 'inverter', 'dev_cla': 'temperature', 'stat_cla': 'measurement', 'id': 'temp_',       'fmt': '| int', 'name': 'Temperature'}},  # noqa: E501
        Register.INVERTER_STATUS: {'name': ['env',  'Inverter_Status'],            'level': logging.INFO,  'unit': '',     'ha': {'dev': 'inverter', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'inv_status_', 'name': 'Inverter Status', 'val_tpl': __status_type_val_tpl,          'icon': 'mdi:power'}},  # noqa: E501

        # input measures:
        Register.TS_INPUT:     {'name': ['input', 'Timestamp'],                    'level': logging.INFO,  'unit': ''},  # noqa: E501
        Register.PV1_VOLTAGE:  {'name': ['input', 'pv1', 'Voltage'],               'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv1', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv1_',  'val_tpl': "{{ (value_json['pv1']['Voltage'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV1_CURRENT:  {'name': ['input', 'pv1', 'Current'],               'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv1', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv1_',   'val_tpl': "{{ (value_json['pv1']['Current'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV1_POWER:    {'name': ['input', 'pv1', 'Power'],                 'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv1', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv1_', 'val_tpl': "{{ (value_json['pv1']['Power'] | float)}}"}},  # noqa: E501
        Register.PV2_VOLTAGE:  {'name': ['input', 'pv2', 'Voltage'],               'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv2', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv2_',  'val_tpl': "{{ (value_json['pv2']['Voltage'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV2_CURRENT:  {'name': ['input', 'pv2', 'Current'],               'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv2', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv2_',   'val_tpl': "{{ (value_json['pv2']['Current'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV2_POWER:    {'name': ['input', 'pv2', 'Power'],                 'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv2', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv2_', 'val_tpl': "{{ (value_json['pv2']['Power'] | float)}}"}},  # noqa: E501
        Register.PV3_VOLTAGE:  {'name': ['input', 'pv3', 'Voltage'],               'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv3', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv3_',  'val_tpl': "{{ (value_json['pv3']['Voltage'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV3_CURRENT:  {'name': ['input', 'pv3', 'Current'],               'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv3', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv3_',   'val_tpl': "{{ (value_json['pv3']['Current'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV3_POWER:    {'name': ['input', 'pv3', 'Power'],                 'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv3', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv3_', 'val_tpl': "{{ (value_json['pv3']['Power'] | float)}}"}},  # noqa: E501
        Register.PV4_VOLTAGE:  {'name': ['input', 'pv4', 'Voltage'],               'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv4', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv4_',  'val_tpl': "{{ (value_json['pv4']['Voltage'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV4_CURRENT:  {'name': ['input', 'pv4', 'Current'],               'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv4', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv4_',   'val_tpl': "{{ (value_json['pv4']['Current'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV4_POWER:    {'name': ['input', 'pv4', 'Power'],                 'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv4', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv4_', 'val_tpl': "{{ (value_json['pv4']['Power'] | float)}}"}},  # noqa: E501
        Register.PV5_VOLTAGE:  {'name': ['input', 'pv5', 'Voltage'],               'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv5', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv5_',  'val_tpl': "{{ (value_json['pv5']['Voltage'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV5_CURRENT:  {'name': ['input', 'pv5', 'Current'],               'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv5', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv5_',   'val_tpl': "{{ (value_json['pv5']['Current'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV5_POWER:    {'name': ['input', 'pv5', 'Power'],                 'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv5', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv5_', 'val_tpl': "{{ (value_json['pv5']['Power'] | float)}}"}},  # noqa: E501
        Register.PV6_VOLTAGE:  {'name': ['input', 'pv6', 'Voltage'],               'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv6', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv6_',  'val_tpl': "{{ (value_json['pv6']['Voltage'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV6_CURRENT:  {'name': ['input', 'pv6', 'Current'],               'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv6', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv6_',   'val_tpl': "{{ (value_json['pv6']['Current'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV6_POWER:    {'name': ['input', 'pv6', 'Power'],                 'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv6', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv6_', 'val_tpl': "{{ (value_json['pv6']['Power'] | float)}}"}},  # noqa: E501
        Register.PV1_DAILY_GENERATION:  {'name': ['input', 'pv1', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv1', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv1_', 'name': 'Daily Generation', 'val_tpl': "{{ (value_json['pv1']['Daily_Generation'] | float)}}", 'icon': 'mdi:solar-power-variant', 'must_incr': True}},  # noqa: E501
        Register.PV1_TOTAL_GENERATION:  {'name': ['input', 'pv1', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv1', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv1_', 'name': 'Total Generation', 'val_tpl': "{{ (value_json['pv1']['Total_Generation'] | float)}}", 'icon': 'mdi:solar-power', 'must_incr': True}},  # noqa: E501
        Register.PV2_DAILY_GENERATION:  {'name': ['input', 'pv2', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv2', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv2_', 'name': 'Daily Generation', 'val_tpl': "{{ (value_json['pv2']['Daily_Generation'] | float)}}", 'icon': 'mdi:solar-power-variant', 'must_incr': True}},  # noqa: E501
        Register.PV2_TOTAL_GENERATION:  {'name': ['input', 'pv2', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv2', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv2_', 'name': 'Total Generation', 'val_tpl': "{{ (value_json['pv2']['Total_Generation'] | float)}}", 'icon': 'mdi:solar-power', 'must_incr': True}},  # noqa: E501
        Register.PV3_DAILY_GENERATION:  {'name': ['input', 'pv3', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv3', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv3_', 'name': 'Daily Generation', 'val_tpl': "{{ (value_json['pv3']['Daily_Generation'] | float)}}", 'icon': 'mdi:solar-power-variant', 'must_incr': True}},  # noqa: E501
        Register.PV3_TOTAL_GENERATION:  {'name': ['input', 'pv3', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv3', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv3_', 'name': 'Total Generation', 'val_tpl': "{{ (value_json['pv3']['Total_Generation'] | float)}}", 'icon': 'mdi:solar-power', 'must_incr': True}},  # noqa: E501
        Register.PV4_DAILY_GENERATION:  {'name': ['input', 'pv4', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv4', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv4_', 'name': 'Daily Generation', 'val_tpl': "{{ (value_json['pv4']['Daily_Generation'] | float)}}", 'icon': 'mdi:solar-power-variant', 'must_incr': True}},  # noqa: E501
        Register.PV4_TOTAL_GENERATION:  {'name': ['input', 'pv4', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv4', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv4_', 'name': 'Total Generation', 'val_tpl': "{{ (value_json['pv4']['Total_Generation'] | float)}}", 'icon': 'mdi:solar-power', 'must_incr': True}},  # noqa: E501
        Register.PV5_DAILY_GENERATION:  {'name': ['input', 'pv5', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv5', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv5_', 'name': 'Daily Generation', 'val_tpl': "{{ (value_json['pv5']['Daily_Generation'] | float)}}", 'icon': 'mdi:solar-power-variant', 'must_incr': True}},  # noqa: E501
        Register.PV5_TOTAL_GENERATION:  {'name': ['input', 'pv5', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv5', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv5_', 'name': 'Total Generation', 'val_tpl': "{{ (value_json['pv5']['Total_Generation'] | float)}}", 'icon': 'mdi:solar-power', 'must_incr': True}},  # noqa: E501
        Register.PV6_DAILY_GENERATION:  {'name': ['input', 'pv6', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv6', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv6_', 'name': 'Daily Generation', 'val_tpl': "{{ (value_json['pv6']['Daily_Generation'] | float)}}", 'icon': 'mdi:solar-power-variant', 'must_incr': True}},  # noqa: E501
        Register.PV6_TOTAL_GENERATION:  {'name': ['input', 'pv6', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv6', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv6_', 'name': 'Total Generation', 'val_tpl': "{{ (value_json['pv6']['Total_Generation'] | float)}}", 'icon': 'mdi:solar-power', 'must_incr': True}},  # noqa: E501
        # total:
        Register.TS_TOTAL:          {'name': ['total', 'Timestamp'],               'level': logging.INFO,  'unit': ''},  # noqa: E501
        Register.DAILY_GENERATION:  {'name': ['total', 'Daily_Generation'],        'level': logging.INFO,  'unit': 'kWh',  'ha': {'dev': 'inverter', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_', 'fmt': '| float', 'name': 'Daily Generation', 'icon': 'mdi:solar-power-variant', 'must_incr': True}},  # noqa: E501
        Register.TOTAL_GENERATION:  {'name': ['total', 'Total_Generation'],        'level': logging.INFO,  'unit': 'kWh',  'ha': {'dev': 'inverter', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_', 'fmt': '| float', 'name': 'Total Generation', 'icon': 'mdi:solar-power', 'must_incr': True}},  # noqa: E501

        # controller:
        Register.SIGNAL_STRENGTH:    {'name': ['controller', 'Signal_Strength'],    'level': logging.DEBUG, 'unit': '%',    'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': 'measurement', 'id': 'signal_',              'fmt': '| int',           'name': 'Signal Strength', 'icon': 'mdi:wifi'}},  # noqa: E501
        Register.POWER_ON_TIME:      {'name': ['controller', 'Power_On_Time'],      'level': logging.DEBUG, 'unit': 's',    'ha': {'dev': 'controller', 'dev_cla': 'duration', 'stat_cla': 'measurement', 'id': 'power_on_time_',       'fmt': '| int',           'name': 'Power on Time', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.COLLECT_INTERVAL:   {'name': ['controller', 'Collect_Interval'],   'level': logging.DEBUG, 'unit': 'min',  'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'data_collect_intval_', 'fmt': '| string + " min"', 'name': 'Data Collect Interval', 'icon': 'mdi:update', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.CONNECT_COUNT:      {'name': ['controller', 'Connect_Count'],      'level': logging.DEBUG, 'unit': '',     'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'connect_count_',       'fmt': '| int',           'name': 'Connect Count',    'icon': 'mdi:counter', 'comp': 'sensor', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.COMMUNICATION_TYPE: {'name': ['controller', 'Communication_Type'], 'level': logging.DEBUG, 'unit': '',     'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'comm_type_',           'name': 'Communication Type', 'val_tpl': __comm_type_val_tpl, 'comp': 'sensor', 'icon': 'mdi:wifi'}},  # noqa: E501
        Register.DATA_UP_INTERVAL:   {'name': ['controller', 'Data_Up_Interval'],   'level': logging.DEBUG, 'unit': 's',    'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'data_up_intval_', 'fmt': '| string + " s"', 'name': 'Data Up Interval', 'icon': 'mdi:update', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.HEARTBEAT_INTERVAL: {'name': ['controller', 'Heartbeat_Interval'], 'level': logging.DEBUG, 'unit': 's',    'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'heartbeat_intval_',    'fmt': '| string + " s"', 'name': 'Heartbeat Interval', 'icon': 'mdi:update', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.IP_ADDRESS:         {'name': ['controller', 'IP_Address'],         'level': logging.DEBUG, 'unit': '',     'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'ip_address_',           'fmt': '| string',        'name': 'IP Address', 'icon': 'mdi:wifi', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.POLLING_INTERVAL:   {'name': ['controller', 'Polling_Interval'],   'level': logging.DEBUG, 'unit': 's',    'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'polling_intval_', 'fmt': '| string + " s"', 'name': 'Polling Interval', 'icon': 'mdi:update', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.SENSOR_LIST:        {'name': ['controller', 'Sensor_List'],        'level': logging.INFO,  'unit': ''},  # noqa: E501
    }

    @property
    def info_devs(self) -> dict:
        return self.__info_devs

    @property
    def info_defs(self) -> dict:
        return self.__info_defs

    def dev_value(self, idx: str | int) -> str | int | float | dict | None:
        '''returns the stored device value from our database

        idx:int ==> lookup the value in the database and return it as str,
                    int or float. If the value is not available return 'None'
        idx:str ==> returns the string as a fixed value without a
                    database lookup
        '''
        if type(idx) is str:
            return idx               # return idx as a fixed value
        elif idx in self.info_defs:
            row = self.info_defs[idx]
            if 'singleton' in row and row['singleton']:
                db_dict = self.stat
            else:
                db_dict = self.db

            keys = row['name']

            for key in keys:
                if key not in db_dict:
                    return None      # value not found in the database
                db_dict = db_dict[key]
            return db_dict              # value of the reqeusted entry

        return None                  # unknwon idx, not in info_defs

    def inc_counter(self, counter: str) -> None:
        '''inc proxy statistic counter'''
        db_dict = self.stat['proxy']
        db_dict[counter] += 1

    def dec_counter(self, counter: str) -> None:
        '''dec proxy statistic counter'''
        db_dict = self.stat['proxy']
        db_dict[counter] -= 1

    def ha_proxy_confs(self, ha_prfx: str, node_id: str, snr: str) \
            -> Generator[tuple[str, str, str, str], None, None]:
        '''Generator function yields json register struct for home-assistant
        auto configuration and the unique entity string, for all proxy
        registers

        arguments:
        ha_prfx:str  ==> MQTT prefix for the home assistant 'stat_t string
        node_id:str  ==> node id of the inverter, used to build unique entity
        snr:str      ==> serial number of the inverter, used to build unique
                         entity strings
        '''
        # iterate over RegisterMap.map and get the register values for entries
        # with Singleton=True, which means that this is a proxy register
        for reg in self.info_defs.keys():
            res = self.ha_conf(reg, ha_prfx, node_id, snr, True)  # noqa: E501
            if res:
                yield res

    def ha_conf(self, key, ha_prfx, node_id, snr,  singleton: bool,
                sug_area: str = '') -> tuple[str, str, str, str] | None:
        '''Method to build json register struct for home-assistant
        auto configuration and the unique entity string, for all proxy
        registers

        arguments:
        key          ==> index of info_defs dict which reference the topic
        ha_prfx:str  ==> MQTT prefix for the home assistant 'stat_t string
        node_id:str  ==> node id of the inverter, used to build unique entity
        snr:str      ==> serial number of the inverter, used to build unique
                         entity strings
        singleton    ==> bool to allow/disaalow proxy topics which are common
                         for all invters
        sug_area     ==> area name for home assistant
        '''
        if key not in self.info_defs:
            return None
        row = self.info_defs[key]

        if 'singleton' in row:
            if singleton != row['singleton']:
                return None
        elif singleton:
            return None
        prfx = ha_prfx + node_id

        # check if we have details for home assistant
        if 'ha' in row:
            ha = row['ha']
            if 'comp' in ha:
                component = ha['comp']
            else:
                component = 'sensor'
            attr = {}
            if 'name' in ha:
                attr['name'] = ha['name']
            else:
                attr['name'] = row['name'][-1]
            attr['stat_t'] = prfx + row['name'][0]
            attr['dev_cla'] = ha['dev_cla']
            attr['stat_cla'] = ha['stat_cla']
            attr['uniq_id'] = ha['id']+snr
            if 'val_tpl' in ha:
                attr['val_tpl'] = ha['val_tpl']
            elif 'fmt' in ha:
                attr['val_tpl'] = '{{value_json' + f"['{row['name'][-1]}'] {ha['fmt']}" + '}}'       # eg.   'val_tpl': "{{ value_json['Output_Power']|float }} # noqa: E501
            else:
                self.inc_counter('Internal_Error')
                logging.error(f"Infos.info_defs: the row for {key} do"
                              " not have a 'val_tpl' nor a 'fmt' value")
            # add unit_of_meas only, if status_class isn't none. If
            # status_cla is None we want a number format and not line
            # graph in home assistant. A unit will change the number
            # format to a line graph
            if 'unit' in row and attr['stat_cla'] is not None:
                attr['unit_of_meas'] = row['unit']  # 'unit_of_meas'
            if 'icon' in ha:
                attr['ic'] = ha['icon']             # icon for the entity
            if 'nat_prc' in ha:  # pragma: no cover
                attr['sug_dsp_prc'] = ha['nat_prc']  # precison of floats
            if 'ent_cat' in ha:
                attr['ent_cat'] = ha['ent_cat']     # diagnostic, config
            # enabled_by_default is deactivated, since it avoid the via
            # setup of the devices. It seems, that there is a bug in home
            # assistant. tested with 'Home Assistant 2023.10.4'
            # if 'en' in ha:                       # enabled_by_default
            #    attr['en'] = ha['en']
            if 'dev' in ha:
                device = self.info_devs[ha['dev']]
                if 'dep' in device and self.ignore_this_device(device['dep']):  # noqa: E501
                    return None
                dev = {}
                # the same name for 'name' and 'suggested area', so we get
                # dedicated devices in home assistant with short value
                # name and headline
                if (sug_area == '' or
                        ('singleton' in device and device['singleton'])):
                    dev['name'] = device['name']
                    dev['sa'] = device['name']
                else:
                    dev['name'] = device['name']+' - '+sug_area
                    dev['sa'] = device['name']+' - '+sug_area
                if 'via' in device:  # add the link to the parent device
                    via = device['via']
                    if via in self.info_devs:
                        via_dev = self.info_devs[via]
                        if 'singleton' in via_dev and via_dev['singleton']:
                            dev['via_device'] = via
                        else:
                            dev['via_device'] = f"{via}_{snr}"
                    else:
                        self.inc_counter('Internal_Error')
                        logging.error(f"Infos.info_defs: the row for "
                                      f"{key} has an invalid via value: "
                                      f"{via}")
                for key in ('mdl', 'mf', 'sw', 'hw'):      # add optional
                    # values fpr 'modell', 'manufacturer', 'sw version' and
                    # 'hw version'
                    if key in device:
                        data = self.dev_value(device[key])
                        if data is not None:
                            dev[key] = data
                if 'singleton' in device and device['singleton']:
                    dev['ids'] = [f"{ha['dev']}"]
                else:
                    dev['ids'] = [f"{ha['dev']}_{snr}"]
                attr['dev'] = dev
                origin = {}
                origin['name'] = self.app_name
                origin['sw'] = self.version
                attr['o'] = origin
            else:
                self.inc_counter('Internal_Error')
                logging.error(f"Infos.info_defs: the row for {key} "
                              "missing 'dev' value for ha register")
            return json.dumps(attr), component, node_id, attr['uniq_id']
        return None

    def ha_remove(self, key, node_id, snr) -> tuple[str, str, str, str] | None:
        '''Method to build json unregister struct for home-assistant
        to remove topics per auto configuration. Only for inverer topics.

        arguments:
        key          ==> index of info_defs dict which reference the topic
        node_id:str  ==> node id of the inverter, used to build unique entity
        snr:str      ==> serial number of the inverter, used to build unique
                         entity strings

        hint:
        the returned tuple must have the same format as self.ha_conf()
        '''
        if key not in self.info_defs:
            return None
        row = self.info_defs[key]

        if 'singleton' in row and row['singleton']:
            return None

        # check if we have details for home assistant
        if 'ha' in row:
            ha = row['ha']
            if 'comp' in ha:
                component = ha['comp']
            else:
                component = 'sensor'
            attr = {}
            uniq_id = ha['id']+snr

            return json.dumps(attr), component, node_id, uniq_id
        return None

    def _key_obj(self, id: Register) -> tuple:
        d = self.info_defs.get(id, {'name': None, 'level': logging.DEBUG,
                                    'unit': ''})
        if 'ha' in d and 'must_incr' in d['ha']:
            must_incr = d['ha']['must_incr']
        else:
            must_incr = False

        return d['name'], d['level'], d['unit'], must_incr

    def update_db(self, keys: list, must_incr: bool, result):
        name = ''
        db_dict = self.db
        for key in keys[:-1]:
            if key not in db_dict:
                db_dict[key] = {}
            db_dict = db_dict[key]
            name += key + '.'
        if keys[-1] not in db_dict:
            update = (not must_incr or result > 0)
        else:
            if must_incr:
                update = db_dict[keys[-1]] < result
            else:
                update = db_dict[keys[-1]] != result
        if update:
            db_dict[keys[-1]] = result
        name += keys[-1]
        return name, update

    def set_db_def_value(self, id: Register, value) -> None:
        '''set default value'''
        row = self.info_defs[id]
        if isinstance(row, dict):
            keys = row['name']
            self.update_db(keys, False, value)

    def reg_clr_at_midnight(self, prfx: str,
                            check_dependencies: bool = True) -> None:
        '''register all registers for the 'ClrAtMidnight' class and
        check if device of every register is available otherwise ignore
        the register.

        prfx:str ==> prefix for the home assistant 'stat_t string''
        '''
        for id, row in self.info_defs.items():
            if check_dependencies and 'ha' in row:
                ha = row['ha']
                if 'dev' in ha:
                    device = self.info_devs[ha['dev']]
                    if 'dep' in device and self.ignore_this_device(device['dep']):  # noqa: E501
                        continue

            keys = row['name']
            ClrAtMidnight.add(keys, prfx, id)

    def get_db_value(self, id: Register, not_found_result: any = None):
        '''get database value'''
        row = self.info_defs[id]
        if isinstance(row, dict):
            keys = row['name']
            elm = self.db
            for key in keys:
                if key not in elm:
                    return not_found_result
                elm = elm[key]
            return elm
        return not_found_result

    def ignore_this_device(self, dep: dict) -> bool:
        '''Checks the equation in the dep(endency) dict

            returns 'False' only if the equation is valid;
                    'True'  in any other case'''
        if 'reg' in dep:
            value = self.dev_value(dep['reg'])
            if not value:
                return True

            if 'gte' in dep:
                return value < dep['gte']
            elif 'less_eq' in dep:
                return value > dep['less_eq']
        return True

    def set_pv_module_details(self, inv: dict) -> None:
        pvs = {'pv1': {'manufacturer': Register.PV1_MANUFACTURER, 'model': Register.PV1_MODEL},  # noqa: E501
               'pv2': {'manufacturer': Register.PV2_MANUFACTURER, 'model': Register.PV2_MODEL},  # noqa: E501
               'pv3': {'manufacturer': Register.PV3_MANUFACTURER, 'model': Register.PV3_MODEL},  # noqa: E501
               'pv4': {'manufacturer': Register.PV4_MANUFACTURER, 'model': Register.PV4_MODEL},  # noqa: E501
               'pv5': {'manufacturer': Register.PV5_MANUFACTURER, 'model': Register.PV5_MODEL},  # noqa: E501
               'pv6': {'manufacturer': Register.PV6_MANUFACTURER, 'model': Register.PV6_MODEL}  # noqa: E501
               }

        for key, reg in pvs.items():
            if key in inv:
                if 'manufacturer' in inv[key]:
                    self.set_db_def_value(reg['manufacturer'],
                                          inv[key]['manufacturer'])
                if 'type' in inv[key]:
                    self.set_db_def_value(reg['model'], inv[key]['type'])
