import logging
import json
import struct
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
    MAC_ADDR = 6
    COLLECTOR_SNR = 7
    PRODUCT_NAME = 20
    MANUFACTURER = 21
    VERSION = 22
    SERIAL_NUMBER = 23
    EQUIPMENT_MODEL = 24
    NO_INPUTS = 25
    MAX_DESIGNED_POWER = 26
    RATED_LEVEL = 27
    INPUT_COEFFICIENT = 28
    GRID_VOLT_CAL_COEF = 29
    OUTPUT_COEFFICIENT = 30
    PROD_COMPL_TYPE = 31
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
    CLOUD_CONN_CNT = 62
    OUTPUT_POWER = 83
    RATED_POWER = 84
    INVERTER_TEMP = 85
    INVERTER_STATUS = 86
    DETECT_STATUS_1 = 87
    DETECT_STATUS_2 = 88
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
    INV_UNKNOWN_1 = 252
    BOOT_STATUS = 253
    DSP_STATUS = 254
    WORK_MODE = 255
    OUTPUT_SHUTDOWN = 256

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
    SSID = 410
    EVENT_ALARM = 500
    EVENT_FAULT = 501
    EVENT_BF1 = 502
    EVENT_BF2 = 503
    TS_INPUT = 600
    TS_GRID = 601
    TS_TOTAL = 602
    BATT_PV1_VOLT = 1000
    BATT_PV1_CUR = 1001
    BATT_PV2_VOLT = 1002
    BATT_PV2_CUR = 1003
    BATT_38 = 1004
    BATT_TOTAL_GEN = 1005
    BATT_STATUS_1 = 1006
    BATT_STATUS_2 = 1007
    BATT_VOLT = 1010
    BATT_CUR = 1011
    BATT_SOC = 1012
    BATT_CELL1_VOLT = 1013
    BATT_CELL2_VOLT = 1014
    BATT_CELL3_VOLT = 1015
    BATT_CELL4_VOLT = 1016
    BATT_CELL5_VOLT = 1017
    BATT_CELL6_VOLT = 1018
    BATT_CELL7_VOLT = 1019
    BATT_CELL8_VOLT = 1020
    BATT_CELL9_VOLT = 1021
    BATT_CELL10_VOLT = 1022
    BATT_CELL11_VOLT = 1023
    BATT_CELL12_VOLT = 1024
    BATT_CELL13_VOLT = 1025
    BATT_CELL14_VOLT = 1026
    BATT_CELL15_VOLT = 1027
    BATT_CELL16_VOLT = 1028
    BATT_TEMP_1 = 1029
    BATT_TEMP_2 = 1030
    BATT_TEMP_3 = 1031
    BATT_OUT_VOLT = 1032
    BATT_OUT_CUR = 1033
    BATT_OUT_STATUS = 1034
    BATT_TEMP_4 = 1035
    BATT_74 = 1036
    BATT_76 = 1037
    BATT_78 = 1038
    BATT_PV_PWR = 1040
    BATT_PWR = 1041
    BATT_OUT_PWR = 1042

    TEST_VAL_0 = 2000
    TEST_VAL_1 = 2001
    TEST_VAL_2 = 2002
    TEST_VAL_3 = 2003
    TEST_VAL_4 = 2004
    TEST_VAL_5 = 2005
    TEST_VAL_6 = 2006
    TEST_VAL_7 = 2007
    TEST_VAL_8 = 2008
    TEST_VAL_9 = 2009
    TEST_VAL_10 = 2010
    TEST_VAL_11 = 2011
    TEST_VAL_12 = 2012
    TEST_VAL_13 = 2013
    TEST_VAL_14 = 2014
    TEST_VAL_15 = 2015
    TEST_VAL_16 = 2016
    TEST_VAL_17 = 2017
    TEST_VAL_18 = 2018
    TEST_VAL_19 = 2019
    TEST_VAL_20 = 2020
    TEST_VAL_21 = 2021
    TEST_VAL_22 = 2022
    TEST_VAL_23 = 2023
    TEST_VAL_24 = 2024
    TEST_VAL_25 = 2025
    TEST_VAL_26 = 2026
    TEST_VAL_27 = 2027
    TEST_VAL_28 = 2028
    TEST_VAL_29 = 2029
    TEST_VAL_30 = 2030
    TEST_VAL_31 = 2031
    TEST_VAL_32 = 2032

    TEST_IVAL_1 = 2041
    TEST_IVAL_2 = 2042
    TEST_IVAL_3 = 2043
    TEST_IVAL_4 = 2044
    TEST_IVAL_5 = 2045
    TEST_IVAL_6 = 2046
    TEST_IVAL_7 = 2047
    TEST_IVAL_8 = 2048
    TEST_IVAL_9 = 2049
    TEST_IVAL_10 = 2050
    TEST_IVAL_11 = 2051
    TEST_IVAL_12 = 2052

    VALUE_1 = 9000
    TEST_REG1 = 10000
    TEST_REG2 = 10001


class Fmt:
    @staticmethod
    def get_value(buf: bytes, idx: int, row: dict):
        '''Get a value from buf and interpret as in row defined'''
        fmt = row['fmt']
        try:
            res = struct.unpack_from(fmt, buf, idx)
        except Exception:
            return None
        result = res[0]
        if isinstance(result, (bytearray, bytes)):
            result = result.decode().split('\x00')[0]
        if 'func' in row:
            result = row['func'](res)
        if 'ratio' in row:
            result = round(result * row['ratio'], 2)
        if 'quotient' in row:
            result = round(result/row['quotient'])
        if 'offset' in row:
            result = result + row['offset']
        return result

    @staticmethod
    def hex4(val: tuple | str, reverse=False) -> str | int:
        if not reverse:
            return f'{val[0]:04x}'
        else:
            return int(val, 16)

    @staticmethod
    def mac(val: tuple | str, reverse=False) -> str | tuple:
        if not reverse:
            return "%02x:%02x:%02x:%02x:%02x:%02x" % val
        else:
            return (
                int(val[0:2], 16), int(val[3:5], 16),
                int(val[6:8], 16), int(val[9:11], 16),
                int(val[12:14], 16), int(val[15:], 16))

    @staticmethod
    def version(val: tuple | str, reverse=False) -> str | int:
        if not reverse:
            x = val[0]
            return f'V{(x >> 12)}.{(x >> 8) & 0xf}' \
                f'.{(x >> 4) & 0xf}{x & 0xf:1X}'
        else:
            arr = val[1:].split('.')
            return int(arr[0], 10) << 12 | \
                int(arr[1], 10) << 8 | \
                int(arr[2][:-1], 10) << 4 | \
                int(arr[2][-1:], 16)

    @staticmethod
    def set_value(buf: bytearray, idx: int, row: dict, val):
        '''Get a value from buf and interpret as in row defined'''
        fmt = row['fmt']
        if 'offset' in row:
            val = val - row['offset']
        if 'quotient' in row:
            val = round(val * row['quotient'])
        if 'ratio' in row:
            val = round(val / row['ratio'])
        if 'func' in row:
            val = row['func'](val, reverse=True)
        if isinstance(val, str):
            val = bytes(val, 'UTF8')

        if isinstance(val, tuple):
            struct.pack_into(fmt, buf, idx, *val)
        else:
            struct.pack_into(fmt, buf, idx, val)


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
    __slots__ = ('db', 'tracer', )

    LIGHTNING = 'mdi:lightning-bolt'
    COUNTER = 'mdi:counter'
    GAUGE = 'mdi:gauge'
    POWER = 'mdi:power'
    SOLAR_POWER_VAR = 'mdi:solar-power-variant'
    SOLAR_POWER = 'mdi:solar-power'
    WIFI = 'mdi:wifi'
    UPDATE = 'mdi:update'
    DAILY_GEN = 'Daily Generation'
    TOTAL_GEN = 'Total Generation'
    FMT_INT = '| int'
    FMT_FLOAT = '| float'
    FMT_STRING_SEC = '| string + " s"'
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
        'controller': {'via': 'proxy',      'name': 'Controller',     'mdl': Register.CHIP_MODEL, 'mf': Register.CHIP_TYPE, 'sw': Register.COLLECTOR_FW_VERSION, 'mac': Register.MAC_ADDR, 'sn': Register.COLLECTOR_SNR},  # noqa: E501

        'inverter':   {'via': 'controller', 'name': 'Micro Inverter', 'mdl': Register.EQUIPMENT_MODEL, 'mf': Register.MANUFACTURER, 'sw': Register.VERSION, 'sn': Register.SERIAL_NUMBER},  # noqa: E501
        'input_pv1':  {'via': 'inverter',   'name': 'Module PV1', 'mdl': Register.PV1_MODEL, 'mf': Register.PV1_MANUFACTURER},  # noqa: E501
        'input_pv2':  {'via': 'inverter',   'name': 'Module PV2', 'mdl': Register.PV2_MODEL, 'mf': Register.PV2_MANUFACTURER, 'dep': {'reg': Register.NO_INPUTS, 'gte': 2}},  # noqa: E501
        'input_pv3':  {'via': 'inverter',   'name': 'Module PV3', 'mdl': Register.PV3_MODEL, 'mf': Register.PV3_MANUFACTURER, 'dep': {'reg': Register.NO_INPUTS, 'gte': 3}},  # noqa: E501
        'input_pv4':  {'via': 'inverter',   'name': 'Module PV4', 'mdl': Register.PV4_MODEL, 'mf': Register.PV4_MANUFACTURER, 'dep': {'reg': Register.NO_INPUTS, 'gte': 4}},  # noqa: E501
        'input_pv5':  {'via': 'inverter',   'name': 'Module PV5', 'mdl': Register.PV5_MODEL, 'mf': Register.PV5_MANUFACTURER, 'dep': {'reg': Register.NO_INPUTS, 'gte': 5}},  # noqa: E501
        'input_pv6':  {'via': 'inverter',   'name': 'Module PV6', 'mdl': Register.PV6_MODEL, 'mf': Register.PV6_MANUFACTURER, 'dep': {'reg': Register.NO_INPUTS, 'gte': 6}},  # noqa: E501

        'batterie':   {'via': 'controller', 'name': 'Batterie', 'mdl': Register.EQUIPMENT_MODEL, 'mf': Register.MANUFACTURER, 'sw': Register.VERSION, 'sn': Register.SERIAL_NUMBER},  # noqa: E501
        'bat_inp_pv1': {'via': 'batterie',  'name': 'Module PV1', 'mdl': Register.PV1_MODEL, 'mf': Register.PV1_MANUFACTURER},  # noqa: E501
        'bat_inp_pv2': {'via': 'batterie',  'name': 'Module PV2', 'mdl': Register.PV2_MODEL, 'mf': Register.PV2_MANUFACTURER},  # noqa: E501
    }

    __comm_type_val_tpl = "{%set com_types = ['n/a','Wi-Fi', 'G4', 'G5', 'GPRS'] %}{{com_types[value_json['Communication_Type']|int(0)]|default(value_json['Communication_Type'])}}"    # noqa: E501
    __work_mode_val_tpl = "{%set mode = ['Normal-Mode', 'Aging-Mode', 'ATE-Mode', 'Shielding GFDI', 'DTU-Mode'] %}{{mode[value_json['Work_Mode']|int(0)]|default(value_json['Work_Mode'])}}"    # noqa: E501
    __status_type_val_tpl = "{%set inv_status = ['Off-line', 'On-grid', 'Off-grid'] %}{{inv_status[value_json['Inverter_Status']|int(0)]|default(value_json['Inverter_Status'])}}"    # noqa: E501
    __mppt1_status_type_val_tpl = "{%set mppt_status = ['Locked', 'Off', 'On'] %}{{mppt_status[value_json['Status_1']|int(0)]|default(value_json['Status_1'])}}"    # noqa: E501
    __mppt2_status_type_val_tpl = "{%set mppt_status = ['Locked', 'Off', 'On'] %}{{mppt_status[value_json['Status_2']|int(0)]|default(value_json['Status_2'])}}"    # noqa: E501
    __out_status_type_val_tpl = "{%set out_status = ['Off', 'On'] %}{{out_status[value_json['out']['Out_Status']|int(0)]|default(value_json['out']['Out_Status'])}}"    # noqa: E501
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
    __inv_alarm_val_tpl = '''
{% if 'Inverter_Alarm' in value_json and
      value_json['Inverter_Alarm'] != None %}
  {% set val_int = value_json['Inverter_Alarm'] | int %}
  {% if val_int == 0 %}
    {% set result = 'noAlarm'%}
  {%else%}
    {% set result = '' %}
    {% if val_int | bitwise_and(1)%}
        {% set result = result + 'HBridgeFault, '%}
    {% endif %}
    {% if val_int | bitwise_and(2)%}
        {% set result = result + 'DriVoltageFault, '%}
    {% endif %}
    {% if val_int | bitwise_and(3)%}
        {% set result = result + 'GFDI-Fault, '%}
    {% endif %}
    {% if val_int | bitwise_and(4)%}
        {% set result = result + 'OverTemp, '%}
    {% endif %}
    {% if val_int | bitwise_and(5)%}
        {% set result = result + 'CommLose, '%}
    {% endif %}
    {% if val_int | bitwise_and(6)%}
        {% set result = result + 'Bit6, '%}
    {% endif %}
    {% if val_int | bitwise_and(7)%}
        {% set result = result + 'Bit7, '%}
    {% endif %}
    {% if val_int | bitwise_and(8)%}
        {% set result = result + 'EEPROM-Fault, '%}
    {% endif %}
    {% if val_int | bitwise_and(9)%}
        {% set result = result + 'NoUtility, '%}
    {% endif %}
    {% if val_int | bitwise_and(10)%}
        {% set result = result + 'VG_Offset, '%}
    {% endif %}
    {% if val_int | bitwise_and(11)%}
        {% set result = result + 'Relais_Open, '%}
    {% endif %}
    {% if val_int | bitwise_and(12)%}
        {% set result = result + 'Relais_Short, '%}
    {% endif %}
    {% if val_int | bitwise_and(13)%}
        {% set result = result + 'GridVoltOverRating, '%}
    {% endif %}
    {% if val_int | bitwise_and(14)%}
        {% set result = result + 'GridVoltUnderRating, '%}
    {% endif %}
    {% if val_int | bitwise_and(15)%}
        {% set result = result + 'GridFreqOverRating, '%}
    {% endif %}
    {% if val_int | bitwise_and(16)%}
        {% set result = result + 'GridFreqUnderRating, '%}
    {% endif %}
  {% endif %}
  {{ result }}
{% else %}
  {{ this.state }}
{% endif %}
'''
    __inv_fault_val_tpl = '''
{% if 'Inverter_Fault' in value_json and
      value_json['Inverter_Fault'] != None %}
  {% set val_int = value_json['Inverter_Fault'] | int %}
  {% if val_int == 0 %}
    {% set result = 'noFault'%}
  {%else%}
    {% set result = '' %}
    {% if val_int | bitwise_and(1)%}
        {% set result = result + 'PVOV-Fault (PV OverVolt), '%}
    {% endif %}
    {% if val_int | bitwise_and(2)%}
        {% set result = result + 'PVLV-Fault (PV LowVolt), '%}
    {% endif %}
    {% if val_int | bitwise_and(3)%}
        {% set result = result + 'PV OI-Fault (PV OverCurrent), '%}
    {% endif %}
    {% if val_int | bitwise_and(4)%}
        {% set result = result + 'PV OFV-Fault, '%}
    {% endif %}
    {% if val_int | bitwise_and(5)%}
        {% set result = result + 'DC ShortCircuitFault, '%}
    {% endif %}
    {% if val_int | bitwise_and(6)%}{% set result = result + 'Bit6, '%}
    {% endif %}
    {% if val_int | bitwise_and(7)%}{% set result = result + 'Bit7, '%}
    {% endif %}
    {% if val_int | bitwise_and(8)%}{% set result = result + 'Bit8, '%}
    {% endif %}
    {% if val_int | bitwise_and(9)%}{% set result = result + 'Bit9, '%}
    {% endif %}
    {% if val_int | bitwise_and(10)%}{% set result = result + 'Bit10, '%}
    {% endif %}
    {% if val_int | bitwise_and(11)%}{% set result = result + 'Bit11, '%}
    {% endif %}
    {% if val_int | bitwise_and(12)%}{% set result = result + 'Bit12, '%}
    {% endif %}
    {% if val_int | bitwise_and(13)%}{% set result = result + 'Bit13, '%}
    {% endif %}
    {% if val_int | bitwise_and(14)%}{% set result = result + 'Bit14, '%}
    {% endif %}
    {% if val_int | bitwise_and(15)%}{% set result = result + 'Bit15, '%}
    {% endif %}
    {% if val_int | bitwise_and(16)%}{% set result = result + 'Bit16, '%}
    {% endif %}
  {% endif %}
  {{ result }}
{% else %}
  {{ this.state }}
{% endif %}
'''

    __input_coef_val_tpl = "{% if 'Output_Coefficient' in value_json and value_json['Input_Coefficient'] != None %}{{value_json['Input_Coefficient']|string() +' %'}}{% else %}{{ this.state }}{% endif %}"  # noqa: E501
    __output_coef_val_tpl = "{% if 'Output_Coefficient' in value_json and value_json['Output_Coefficient'] != None %}{{value_json['Output_Coefficient']|string() +' %'}}{% else %}{{ this.state }}{% endif %}"  # noqa: E501

    __info_defs = {
        # collector values used for device registration:
        Register.COLLECTOR_FW_VERSION:  {'name': ['collector', 'Collector_Fw_Version'],       'level': logging.INFO,  'unit': ''},  # noqa: E501
        Register.CHIP_TYPE:  {'name': ['collector', 'Chip_Type'],        'singleton': False,  'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.CHIP_MODEL: {'name': ['collector', 'Chip_Model'],       'singleton': False,  'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.TRACE_URL:  {'name': ['collector', 'Trace_URL'],        'singleton': False,  'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.LOGGER_URL: {'name': ['collector', 'Logger_URL'],       'singleton': False,  'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.MAC_ADDR:   {'name': ['collector', 'MAC-Addr'],         'singleton': False,  'level': logging.INFO,  'unit': ''},  # noqa: E501
        Register.COLLECTOR_SNR: {'name': ['collector', 'Serial_Number'], 'singleton': False,  'level': logging.INFO,  'unit': ''},  # noqa: E501


        # inverter values used for device registration:
        Register.PRODUCT_NAME:    {'name': ['inverter', 'Product_Name'],           'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.MANUFACTURER:    {'name': ['inverter', 'Manufacturer'],           'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.VERSION:         {'name': ['inverter', 'Version'],                'level': logging.INFO,  'unit': ''},  # noqa: E501
        Register.SERIAL_NUMBER:   {'name': ['inverter', 'Serial_Number'],          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.EQUIPMENT_MODEL: {'name': ['inverter', 'Equipment_Model'],        'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.NO_INPUTS:       {'name': ['inverter', 'No_Inputs'],              'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.MAX_DESIGNED_POWER: {'name': ['inverter',  'Max_Designed_Power'], 'level': logging.INFO,  'unit': 'W',    'ha': {'dev': 'inverter', 'dev_cla': None, 'stat_cla': None, 'id': 'designed_power_', 'val_tpl': __designed_power_val_tpl, 'name': 'Max Designed Power', 'icon': LIGHTNING, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.RATED_POWER:        {'name': ['inverter',  'Rated_Power'],        'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'inverter', 'dev_cla': None, 'stat_cla': None, 'id': 'rated_power_',    'val_tpl': __rated_power_val_tpl,    'name': 'Rated Power',        'icon': LIGHTNING, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.WORK_MODE:          {'name': ['inverter',  'Work_Mode'],          'level': logging.DEBUG, 'unit': '',     'ha': {'dev': 'inverter', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'work_mode_', 'name': 'Work Mode', 'val_tpl': __work_mode_val_tpl,  'icon': POWER, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.INPUT_COEFFICIENT:  {'name': ['inverter',  'Input_Coefficient'],  'level': logging.DEBUG, 'unit': '%',    'ha': {'dev': 'inverter', 'dev_cla': None, 'stat_cla': None, 'id': 'input_coef_',    'val_tpl': __input_coef_val_tpl,    'name': 'Input Coefficient', 'icon': LIGHTNING, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.OUTPUT_COEFFICIENT: {'name': ['inverter',  'Output_Coefficient'], 'level': logging.INFO,  'unit': '%',    'ha': {'dev': 'inverter', 'dev_cla': None, 'stat_cla': None, 'id': 'output_coef_',    'val_tpl': __output_coef_val_tpl,    'name': 'Output Coefficient', 'icon': LIGHTNING, 'ent_cat': 'diagnostic'}},  # noqa: E501
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
        Register.BOOT_STATUS:      {'name': ['inverter', 'BOOT_STATUS'],           'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.DSP_STATUS:       {'name': ['inverter', 'DSP_STATUS'],            'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        # proxy:
        Register.INVERTER_CNT:       {'name': ['proxy', 'Inverter_Cnt'],       'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'inv_count_',     'fmt': FMT_INT, 'name': 'Active Inverter Connections',    'icon': COUNTER}},  # noqa: E501
        Register.CLOUD_CONN_CNT:     {'name': ['proxy', 'Cloud_Conn_Cnt'],     'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'cloud_conn_count_', 'fmt': FMT_INT, 'name': 'Active Cloud Connections',    'icon': COUNTER}},  # noqa: E501
        Register.UNKNOWN_SNR:        {'name': ['proxy', 'Unknown_SNR'],        'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'unknown_snr_',   'fmt': FMT_INT, 'name': 'Unknown Serial No',    'icon': COUNTER, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.UNKNOWN_MSG:        {'name': ['proxy', 'Unknown_Msg'],        'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'unknown_msg_',   'fmt': FMT_INT, 'name': 'Unknown Msg Type',     'icon': COUNTER, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.INVALID_DATA_TYPE:  {'name': ['proxy', 'Invalid_Data_Type'],  'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'inv_data_type_', 'fmt': FMT_INT, 'name': 'Invalid Data Type',    'icon': COUNTER, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.INTERNAL_ERROR:     {'name': ['proxy', 'Internal_Error'],     'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'intern_err_',    'fmt': FMT_INT, 'name': 'Internal Error',       'icon': COUNTER, 'ent_cat': 'diagnostic', 'en': False}},  # noqa: E501
        Register.UNKNOWN_CTRL:       {'name': ['proxy', 'Unknown_Ctrl'],       'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'unknown_ctrl_',  'fmt': FMT_INT, 'name': 'Unknown Control Type', 'icon': COUNTER, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.OTA_START_MSG:      {'name': ['proxy', 'OTA_Start_Msg'],      'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'ota_start_cmd_', 'fmt': FMT_INT, 'name': 'OTA Start Cmd',        'icon': COUNTER, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.SW_EXCEPTION:       {'name': ['proxy', 'SW_Exception'],       'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'sw_exception_',  'fmt': FMT_INT, 'name': 'Internal SW Exception', 'icon': COUNTER, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.INVALID_MSG_FMT:    {'name': ['proxy', 'Invalid_Msg_Format'], 'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'inv_msg_fmt_',   'fmt': FMT_INT, 'name': 'Invalid Message Format', 'icon': COUNTER, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.AT_COMMAND:         {'name': ['proxy', 'AT_Command'],         'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'at_cmd_',        'fmt': FMT_INT, 'name': 'AT Command',           'icon': COUNTER, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.AT_COMMAND_BLOCKED: {'name': ['proxy', 'AT_Command_Blocked'], 'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'at_cmd_blocked_', 'fmt': FMT_INT, 'name': 'AT Command Blocked',   'icon': COUNTER, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.MODBUS_COMMAND:     {'name': ['proxy', 'Modbus_Command'],     'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'modbus_cmd_',    'fmt': FMT_INT, 'name': 'Modbus Command',       'icon': COUNTER, 'ent_cat': 'diagnostic'}},  # noqa: E501
        # 0xffffff03:  {'name':['proxy', 'Voltage'],                        'level': logging.DEBUG, 'unit': 'V',    'ha':{'dev':'proxy', 'dev_cla': 'voltage',     'stat_cla': 'measurement', 'id':'proxy_volt_',  'fmt':FMT_FLOAT,'name': 'Grid Voltage'}},  # noqa: E501

        # events
        Register.EVENT_ALARM:  {'name': ['events', 'Inverter_Alarm'],              'level': logging.INFO, 'unit': '', 'ha': {'dev': 'inverter', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'inv_alarm_', 'name': 'Inverter Alarm', 'val_tpl': __inv_alarm_val_tpl, 'icon': 'mdi:alarm-light'}},  # noqa: E501
        Register.EVENT_FAULT:  {'name': ['events', 'Inverter_Fault'],              'level': logging.INFO, 'unit': '', 'ha': {'dev': 'inverter', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'inv_fault_', 'name': 'Inverter Fault', 'val_tpl': __inv_fault_val_tpl, 'icon': 'mdi:alarm-light'}},  # noqa: E501
        Register.EVENT_BF1:    {'name': ['events', 'Inverter_Bitfield_1'],         'level': logging.INFO, 'unit': ''},  # noqa: E501
        Register.EVENT_BF2:    {'name': ['events', 'Inverter_bitfield_2'],         'level': logging.INFO, 'unit': ''},  # noqa: E501
        # Register.EVENT_409:  {'name': ['events', '409_No_Utility'],                'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        # Register.EVENT_415:  {'name': ['events', '415_GridFreqOverRating'],        'level': logging.DEBUG, 'unit': ''},  # noqa: E501

        # grid measures:
        Register.TS_GRID:         {'name': ['grid', 'Timestamp'],                  'level': logging.INFO,  'unit': ''},  # noqa: E501
        Register.GRID_VOLTAGE:    {'name': ['grid', 'Voltage'],                    'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'inverter', 'dev_cla': 'voltage',     'stat_cla': 'measurement', 'id': 'out_volt_',  'fmt': FMT_FLOAT, 'name': 'Grid Voltage', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.GRID_CURRENT:    {'name': ['grid', 'Current'],                    'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'inverter', 'dev_cla': 'current',     'stat_cla': 'measurement', 'id': 'out_cur_',   'fmt': FMT_FLOAT, 'name': 'Grid Current', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.GRID_FREQUENCY:  {'name': ['grid', 'Frequency'],                  'level': logging.DEBUG, 'unit': 'Hz',   'ha': {'dev': 'inverter', 'dev_cla': 'frequency',   'stat_cla': 'measurement', 'id': 'out_freq_',  'fmt': FMT_FLOAT, 'name': 'Grid Frequency', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.OUTPUT_POWER:    {'name': ['grid', 'Output_Power'],               'level': logging.INFO,  'unit': 'W',    'ha': {'dev': 'inverter', 'dev_cla': 'power',       'stat_cla': 'measurement', 'id': 'out_power_', 'fmt': FMT_FLOAT, 'name': 'Power'}},  # noqa: E501
        Register.INVERTER_TEMP:   {'name': ['env',  'Inverter_Temp'],              'level': logging.DEBUG, 'unit': '°C',   'ha': {'dev': 'inverter', 'dev_cla': 'temperature', 'stat_cla': 'measurement', 'id': 'temp_',       'fmt': FMT_INT, 'name': 'Temperature'}},  # noqa: E501
        Register.INVERTER_STATUS: {'name': ['env',  'Inverter_Status'],            'level': logging.INFO,  'unit': '',     'ha': {'dev': 'inverter', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'inv_status_', 'name': 'Inverter Status', 'val_tpl': __status_type_val_tpl,          'icon': POWER}},  # noqa: E501
        Register.DETECT_STATUS_1: {'name': ['env',  'Detect_Status_1'],            'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.DETECT_STATUS_2: {'name': ['env',  'Detect_Status_2'],            'level': logging.DEBUG, 'unit': ''},  # noqa: E501

        # input measures:
        Register.TS_INPUT:     {'name': ['input', 'Timestamp'],                    'level': logging.INFO,  'unit': ''},  # noqa: E501
        Register.PV1_VOLTAGE:  {'name': ['input', 'pv1', 'Voltage'],               'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv1', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv1_',  'val_tpl': "{{ (value_json['pv1']['Voltage'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV1_CURRENT:  {'name': ['input', 'pv1', 'Current'],               'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv1', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv1_',   'val_tpl': "{{ (value_json['pv1']['Current'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV1_POWER:    {'name': ['input', 'pv1', 'Power'],                 'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv1', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv1_', 'val_tpl': "{{ (value_json['pv1']['Power'] | float)}}"}},  # noqa: E501
        Register.PV2_VOLTAGE:  {'name': ['input', 'pv2', 'Voltage'],               'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv2', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv2_',  'val_tpl': "{{ (value_json['pv2']['Voltage'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV2_CURRENT:  {'name': ['input', 'pv2', 'Current'],               'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv2', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv2_',   'val_tpl': "{{ (value_json['pv2']['Current'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV2_POWER:    {'name': ['input', 'pv2', 'Power'],                 'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv2', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv2_', 'val_tpl': "{{ (value_json['pv2']['Power'] | float)}}"}},  # noqa: E501
        Register.PV3_VOLTAGE:  {'name': ['input', 'pv3', 'Voltage'],               'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv3', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv3_',  'val_tpl': "{{ (value_json['pv3']['Voltage'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV3_CURRENT:  {'name': ['input', 'pv3', 'Current'],               'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv3', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv3_',   'val_tpl': "{{ (value_json['pv3']['Current'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV3_POWER:    {'name': ['input', 'pv3', 'Power'],                 'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv3', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv3_', 'val_tpl': "{{ (value_json['pv3']['Power'] | float)}}"}},  # noqa: E501
        Register.PV4_VOLTAGE:  {'name': ['input', 'pv4', 'Voltage'],               'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv4', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv4_',  'val_tpl': "{{ (value_json['pv4']['Voltage'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV4_CURRENT:  {'name': ['input', 'pv4', 'Current'],               'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv4', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv4_',   'val_tpl': "{{ (value_json['pv4']['Current'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV4_POWER:    {'name': ['input', 'pv4', 'Power'],                 'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv4', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv4_', 'val_tpl': "{{ (value_json['pv4']['Power'] | float)}}"}},  # noqa: E501
        Register.PV5_VOLTAGE:  {'name': ['input', 'pv5', 'Voltage'],               'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv5', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv5_',  'val_tpl': "{{ (value_json['pv5']['Voltage'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV5_CURRENT:  {'name': ['input', 'pv5', 'Current'],               'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv5', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv5_',   'val_tpl': "{{ (value_json['pv5']['Current'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV5_POWER:    {'name': ['input', 'pv5', 'Power'],                 'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv5', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv5_', 'val_tpl': "{{ (value_json['pv5']['Power'] | float)}}"}},  # noqa: E501
        Register.PV6_VOLTAGE:  {'name': ['input', 'pv6', 'Voltage'],               'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv6', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv6_',  'val_tpl': "{{ (value_json['pv6']['Voltage'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV6_CURRENT:  {'name': ['input', 'pv6', 'Current'],               'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv6', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv6_',   'val_tpl': "{{ (value_json['pv6']['Current'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.PV6_POWER:    {'name': ['input', 'pv6', 'Power'],                 'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv6', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv6_', 'val_tpl': "{{ (value_json['pv6']['Power'] | float)}}"}},  # noqa: E501
        Register.PV1_DAILY_GENERATION:  {'name': ['input', 'pv1', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv1', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv1_', 'name': DAILY_GEN, 'val_tpl': "{{ (value_json['pv1']['Daily_Generation'] | float)}}", 'icon': SOLAR_POWER_VAR, 'must_incr': True}},  # noqa: E501
        Register.PV1_TOTAL_GENERATION:  {'name': ['input', 'pv1', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv1', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv1_', 'name': TOTAL_GEN, 'val_tpl': "{{ (value_json['pv1']['Total_Generation'] | float)}}", 'icon': SOLAR_POWER, 'must_incr': True}},  # noqa: E501
        Register.PV2_DAILY_GENERATION:  {'name': ['input', 'pv2', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv2', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv2_', 'name': DAILY_GEN, 'val_tpl': "{{ (value_json['pv2']['Daily_Generation'] | float)}}", 'icon': SOLAR_POWER_VAR, 'must_incr': True}},  # noqa: E501
        Register.PV2_TOTAL_GENERATION:  {'name': ['input', 'pv2', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv2', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv2_', 'name': TOTAL_GEN, 'val_tpl': "{{ (value_json['pv2']['Total_Generation'] | float)}}", 'icon': SOLAR_POWER, 'must_incr': True}},  # noqa: E501
        Register.PV3_DAILY_GENERATION:  {'name': ['input', 'pv3', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv3', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv3_', 'name': DAILY_GEN, 'val_tpl': "{{ (value_json['pv3']['Daily_Generation'] | float)}}", 'icon': SOLAR_POWER_VAR, 'must_incr': True}},  # noqa: E501
        Register.PV3_TOTAL_GENERATION:  {'name': ['input', 'pv3', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv3', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv3_', 'name': TOTAL_GEN, 'val_tpl': "{{ (value_json['pv3']['Total_Generation'] | float)}}", 'icon': SOLAR_POWER, 'must_incr': True}},  # noqa: E501
        Register.PV4_DAILY_GENERATION:  {'name': ['input', 'pv4', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv4', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv4_', 'name': DAILY_GEN, 'val_tpl': "{{ (value_json['pv4']['Daily_Generation'] | float)}}", 'icon': SOLAR_POWER_VAR, 'must_incr': True}},  # noqa: E501
        Register.PV4_TOTAL_GENERATION:  {'name': ['input', 'pv4', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv4', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv4_', 'name': TOTAL_GEN, 'val_tpl': "{{ (value_json['pv4']['Total_Generation'] | float)}}", 'icon': SOLAR_POWER, 'must_incr': True}},  # noqa: E501
        Register.PV5_DAILY_GENERATION:  {'name': ['input', 'pv5', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv5', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv5_', 'name': DAILY_GEN, 'val_tpl': "{{ (value_json['pv5']['Daily_Generation'] | float)}}", 'icon': SOLAR_POWER_VAR, 'must_incr': True}},  # noqa: E501
        Register.PV5_TOTAL_GENERATION:  {'name': ['input', 'pv5', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv5', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv5_', 'name': TOTAL_GEN, 'val_tpl': "{{ (value_json['pv5']['Total_Generation'] | float)}}", 'icon': SOLAR_POWER, 'must_incr': True}},  # noqa: E501
        Register.PV6_DAILY_GENERATION:  {'name': ['input', 'pv6', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv6', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv6_', 'name': DAILY_GEN, 'val_tpl': "{{ (value_json['pv6']['Daily_Generation'] | float)}}", 'icon': SOLAR_POWER_VAR, 'must_incr': True}},  # noqa: E501
        Register.PV6_TOTAL_GENERATION:  {'name': ['input', 'pv6', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv6', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv6_', 'name': TOTAL_GEN, 'val_tpl': "{{ (value_json['pv6']['Total_Generation'] | float)}}", 'icon': SOLAR_POWER, 'must_incr': True}},  # noqa: E501
        # total:
        Register.TS_TOTAL:          {'name': ['total', 'Timestamp'],               'level': logging.INFO,  'unit': ''},  # noqa: E501
        Register.DAILY_GENERATION:  {'name': ['total', 'Daily_Generation'],        'level': logging.INFO,  'unit': 'kWh',  'ha': {'dev': 'inverter', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_', 'fmt': FMT_FLOAT, 'name': DAILY_GEN, 'icon': SOLAR_POWER_VAR, 'must_incr': True}},  # noqa: E501
        Register.TOTAL_GENERATION:  {'name': ['total', 'Total_Generation'],        'level': logging.INFO,  'unit': 'kWh',  'ha': {'dev': 'inverter', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_', 'fmt': FMT_FLOAT, 'name': TOTAL_GEN, 'icon': SOLAR_POWER, 'must_incr': True}},  # noqa: E501

        # controller:
        Register.SIGNAL_STRENGTH:    {'name': ['controller', 'Signal_Strength'],    'level': logging.INFO, 'unit': '%',    'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': 'measurement', 'id': 'signal_',              'fmt': FMT_INT,           'name': 'Signal Strength', 'icon': WIFI}},  # noqa: E501
        Register.POWER_ON_TIME:      {'name': ['controller', 'Power_On_Time'],      'level': logging.INFO, 'unit': 's',    'ha': {'dev': 'controller', 'dev_cla': 'duration', 'stat_cla': 'measurement', 'id': 'power_on_time_',       'fmt': FMT_INT,           'name': 'Power on Time', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.COLLECT_INTERVAL:   {'name': ['controller', 'Collect_Interval'],   'level': logging.INFO, 'unit': 'min',  'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'data_collect_intval_', 'fmt': '| string + " min"', 'name': 'Data Collect Interval', 'icon': UPDATE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.CONNECT_COUNT:      {'name': ['controller', 'Connect_Count'],      'level': logging.INFO, 'unit': '',     'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'connect_count_',       'fmt': FMT_INT,           'name': 'Connect Count',    'icon': COUNTER, 'comp': 'sensor', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.COMMUNICATION_TYPE: {'name': ['controller', 'Communication_Type'], 'level': logging.INFO, 'unit': '',     'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'comm_type_',           'name': 'Communication Type', 'val_tpl': __comm_type_val_tpl, 'comp': 'sensor', 'icon': WIFI}},  # noqa: E501
        Register.DATA_UP_INTERVAL:   {'name': ['controller', 'Data_Up_Interval'],   'level': logging.INFO, 'unit': 's',    'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'data_up_intval_', 'fmt': FMT_STRING_SEC, 'name': 'Data Up Interval', 'icon': UPDATE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.HEARTBEAT_INTERVAL: {'name': ['controller', 'Heartbeat_Interval'], 'level': logging.INFO, 'unit': 's',    'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'heartbeat_intval_',    'fmt': FMT_STRING_SEC, 'name': 'Heartbeat Interval', 'icon': UPDATE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.IP_ADDRESS:         {'name': ['controller', 'IP_Address'],         'level': logging.INFO, 'unit': '',     'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'ip_address_',           'fmt': '| string',        'name': 'IP Address', 'icon': WIFI, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.POLLING_INTERVAL:   {'name': ['controller', 'Polling_Interval'],   'level': logging.INFO, 'unit': 's',    'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': None,          'id': 'polling_intval_', 'fmt': FMT_STRING_SEC, 'name': 'Polling Interval', 'icon': UPDATE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.SENSOR_LIST:        {'name': ['controller', 'Sensor_List'],        'level': logging.INFO,  'unit': ''},  # noqa: E501
        Register.SSID:               {'name': ['controller', 'WiFi_SSID'],          'level': logging.DEBUG, 'unit': ''},  # noqa: E501

        Register.OUTPUT_SHUTDOWN:    {'name': ['other', 'Output_Shutdown'],         'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.RATED_LEVEL:        {'name': ['other', 'Rated_Level'],             'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.GRID_VOLT_CAL_COEF: {'name': ['other', 'Grid_Volt_Cal_Coef'],      'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        Register.PROD_COMPL_TYPE:    {'name': ['other', 'Prod_Compliance_Type'],    'level': logging.INFO,  'unit': ''},  # noqa: E501
        Register.INV_UNKNOWN_1:      {'name': ['inv_unknown', 'Unknown_1'],         'level': logging.DEBUG, 'unit': ''},  # noqa: E501

        Register.BATT_PV1_VOLT:      {'name': ['batterie', 'pv1', 'Voltage'],       'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'bat_inp_pv1', 'dev_cla': 'voltage',   'stat_cla': 'measurement', 'id': 'volt_pv1_', 'val_tpl': "{{ (value_json['pv1']['Voltage'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_PV1_CUR:       {'name': ['batterie', 'pv1', 'Current'],       'level': logging.INFO, 'unit': 'A',    'ha': {'dev': 'bat_inp_pv1', 'dev_cla': 'current',   'stat_cla': 'measurement', 'id': 'cur_pv1_',  'val_tpl': "{{ (value_json['pv1']['Current'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_PV2_VOLT:      {'name': ['batterie', 'pv2', 'Voltage'],       'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'bat_inp_pv2', 'dev_cla': 'voltage',   'stat_cla': 'measurement', 'id': 'volt_pv2_', 'val_tpl': "{{ (value_json['pv2']['Voltage'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_PV2_CUR:       {'name': ['batterie', 'pv2', 'Current'],       'level': logging.INFO, 'unit': 'A',    'ha': {'dev': 'bat_inp_pv2', 'dev_cla': 'current',   'stat_cla': 'measurement', 'id': 'cur_pv2_',  'val_tpl': "{{ (value_json['pv2']['Current'] | float)}}", 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_38:            {'name': ['batterie', 'Reg_38'],               'level': logging.INFO, 'unit': '',     'ha': {'dev': 'batterie', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'batt_38_', 'fmt': FMT_FLOAT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_TOTAL_GEN:     {'name': ['batterie', 'Total_Generation'],     'level': logging.INFO, 'unit': 'kWh',  'ha': {'dev': 'batterie', 'dev_cla': 'energy',   'stat_cla': 'total', 'id': 'total_gen_', 'fmt': FMT_FLOAT, 'name': TOTAL_GEN, 'icon': SOLAR_POWER, 'must_incr': True}},  # noqa: E501
        Register.BATT_STATUS_1:      {'name': ['batterie', 'Status_1'],             'level': logging.INFO, 'unit': '',     'ha': {'dev': 'batterie', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'status1_', 'name': 'MPPT-1 Status', 'val_tpl': __mppt1_status_type_val_tpl, 'icon': POWER}},  # noqa: E501
        Register.BATT_STATUS_2:      {'name': ['batterie', 'Status_2'],             'level': logging.INFO, 'unit': '',     'ha': {'dev': 'batterie', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'status2_', 'name': 'MPPT-2 Status', 'val_tpl': __mppt2_status_type_val_tpl, 'icon': POWER}},  # noqa: E501
        Register.BATT_VOLT:          {'name': ['batterie', 'Voltage'],              'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_bat_', 'fmt': FMT_FLOAT, 'name': 'Batterie Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CUR:           {'name': ['batterie', 'Current'],              'level': logging.INFO, 'unit': 'A',    'ha': {'dev': 'batterie', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_bat_',  'fmt': FMT_FLOAT, 'name': 'Batterie Current', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_SOC:           {'name': ['batterie', 'SOC'],                  'level': logging.INFO, 'unit': '%',    'ha': {'dev': 'batterie', 'dev_cla': None,      'stat_cla': 'measurement', 'id': 'soc_',     'fmt': FMT_FLOAT,           'name': 'State of Charge (SOC)', 'icon': 'mdi:battery-90'}},  # noqa: E501
        Register.BATT_CELL1_VOLT:    {'name': ['batterie', 'Cell', 'Volt1'],        'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell1_', 'val_tpl': "{{ (value_json['Cell']['Volt1'] | float)}}", 'name': 'Cell-01 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL3_VOLT:    {'name': ['batterie', 'Cell', 'Volt3'],        'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell3_', 'val_tpl': "{{ (value_json['Cell']['Volt2'] | float)}}", 'name': 'Cell-03 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL4_VOLT:    {'name': ['batterie', 'Cell', 'Volt4'],        'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell4_', 'val_tpl': "{{ (value_json['Cell']['Volt3'] | float)}}", 'name': 'Cell-04 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL2_VOLT:    {'name': ['batterie', 'Cell', 'Volt2'],        'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell2_', 'val_tpl': "{{ (value_json['Cell']['Volt4'] | float)}}", 'name': 'Cell-02 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL5_VOLT:    {'name': ['batterie', 'Cell', 'Volt5'],        'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell5_', 'val_tpl': "{{ (value_json['Cell']['Volt5'] | float)}}", 'name': 'Cell-05 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL6_VOLT:    {'name': ['batterie', 'Cell', 'Volt6'],        'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell6_', 'val_tpl': "{{ (value_json['Cell']['Volt6'] | float)}}", 'name': 'Cell-06 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL7_VOLT:    {'name': ['batterie', 'Cell', 'Volt7'],        'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell7_', 'val_tpl': "{{ (value_json['Cell']['Volt7'] | float)}}", 'name': 'Cell-07 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL8_VOLT:    {'name': ['batterie', 'Cell', 'Volt8'],        'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell8_', 'val_tpl': "{{ (value_json['Cell']['Volt8'] | float)}}", 'name': 'Cell-08 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL9_VOLT:    {'name': ['batterie', 'Cell', 'Volt9'],        'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell9_', 'val_tpl': "{{ (value_json['Cell']['Volt9'] | float)}}", 'name': 'Cell-09 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL10_VOLT:   {'name': ['batterie', 'Cell', 'Volt10'],       'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell10_', 'val_tpl': "{{ (value_json['Cell']['Volt10'] | float)}}", 'name': 'Cell-10 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL11_VOLT:   {'name': ['batterie', 'Cell', 'Volt11'],       'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell11_', 'val_tpl': "{{ (value_json['Cell']['Volt11'] | float)}}", 'name': 'Cell-11 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL12_VOLT:   {'name': ['batterie', 'Cell', 'Volt12'],       'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell12_', 'val_tpl': "{{ (value_json['Cell']['Volt12'] | float)}}", 'name': 'Cell-12 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL13_VOLT:   {'name': ['batterie', 'Cell', 'Volt13'],       'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell13_', 'val_tpl': "{{ (value_json['Cell']['Volt13'] | float)}}", 'name': 'Cell-13 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL14_VOLT:   {'name': ['batterie', 'Cell', 'Volt14'],       'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell14_', 'val_tpl': "{{ (value_json['Cell']['Volt14'] | float)}}", 'name': 'Cell-14 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL15_VOLT:   {'name': ['batterie', 'Cell', 'Volt15'],       'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell15_', 'val_tpl': "{{ (value_json['Cell']['Volt15'] | float)}}", 'name': 'Cell-15 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_CELL16_VOLT:   {'name': ['batterie', 'Cell', 'Volt16'],       'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_cell16_', 'val_tpl': "{{ (value_json['Cell']['Volt16'] | float)}}", 'name': 'Cell-16 Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_TEMP_1:        {'name': ['batterie', 'Temp_1'],               'level': logging.INFO, 'unit': '°C',   'ha': {'dev': 'batterie', 'dev_cla': 'temperature', 'stat_cla': 'measurement', 'id': 'temp_1_', 'fmt': FMT_INT, 'name': 'Batterie Temp-1', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_TEMP_2:        {'name': ['batterie', 'Temp_2'],               'level': logging.INFO, 'unit': '°C',   'ha': {'dev': 'batterie', 'dev_cla': 'temperature', 'stat_cla': 'measurement', 'id': 'temp_2_', 'fmt': FMT_INT, 'name': 'Batterie Temp-2', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_TEMP_3:        {'name': ['batterie', 'Temp_3'],               'level': logging.INFO, 'unit': '°C',   'ha': {'dev': 'batterie', 'dev_cla': 'temperature', 'stat_cla': 'measurement', 'id': 'temp_3_', 'fmt': FMT_INT, 'name': 'Batterie Temp-3', 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_OUT_VOLT:      {'name': ['batterie', 'out', 'Voltage'],       'level': logging.INFO, 'unit': 'V',    'ha': {'dev': 'batterie', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'out_volt_', 'val_tpl': "{{ (value_json['out']['Voltage'] | float)}}", 'name': 'Output Voltage', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_OUT_CUR:       {'name': ['batterie', 'out', 'Current'],       'level': logging.INFO, 'unit': 'A',    'ha': {'dev': 'batterie', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'out_cur_',  'val_tpl': "{{ (value_json['out']['Current'] | float)}}", 'name': 'Output Current', 'icon': GAUGE, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_OUT_STATUS:    {'name': ['batterie', 'out', 'Out_Status'],    'level': logging.INFO, 'unit': '',     'ha': {'dev': 'batterie', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'out_status_', 'name': 'Output Status', 'val_tpl': __out_status_type_val_tpl,          'icon': POWER}},  # noqa: E501
        Register.BATT_TEMP_4:        {'name': ['batterie', 'Controller_Temp'],      'level': logging.INFO, 'unit': '°C',   'ha': {'dev': 'batterie', 'dev_cla': 'temperature', 'stat_cla': 'measurement', 'id': 'temp_4_', 'fmt': FMT_INT, 'name': 'Ctrl Temperature'}},  # noqa: E501
        Register.BATT_74:            {'name': ['batterie', 'Reg_74'],               'level': logging.INFO, 'unit': '',     'ha': {'dev': 'batterie', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'batt_74_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_76:            {'name': ['batterie', 'Reg_76'],               'level': logging.INFO, 'unit': '',     'ha': {'dev': 'batterie', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'batt_76_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_78:            {'name': ['batterie', 'Reg_78'],               'level': logging.INFO, 'unit': '',     'ha': {'dev': 'batterie', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'batt_78_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.BATT_PV_PWR:        {'name': ['batterie', 'PV_Power'],             'level': logging.INFO, 'unit': 'W',    'ha': {'dev': 'batterie', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'pv_power_', 'fmt': FMT_INT, 'name': 'PV Power'}},  # noqa: E501
        Register.BATT_PWR:           {'name': ['batterie', 'Power'],                'level': logging.INFO, 'unit': 'W',    'ha': {'dev': 'batterie', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_',    'fmt': FMT_INT, 'name': 'Batterie Power'}},  # noqa: E501
        Register.BATT_OUT_PWR:       {'name': ['batterie', 'out', 'Power'],         'level': logging.INFO, 'unit': 'W',    'ha': {'dev': 'batterie', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'out_power_', 'val_tpl': "{{ (value_json['out']['Power'] | int)}}", 'name': 'Output Power'}},  # noqa: E501

        Register.TEST_VAL_0:         {'name': ['input', 'Val_0'],                   'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_0_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_1:         {'name': ['input', 'Val_1'],                   'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_1_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_2:         {'name': ['input', 'Val_2'],                   'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_2_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_3:         {'name': ['input', 'Val_3'],                   'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_3_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_4:         {'name': ['input', 'Val_4'],                   'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_4_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_5:         {'name': ['input', 'Val_5'],                   'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_5_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_6:         {'name': ['input', 'Val_6'],                   'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_6_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_7:         {'name': ['input', 'Val_7'],                   'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_7_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_8:         {'name': ['input', 'Val_8'],                   'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_8_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_9:         {'name': ['input', 'Val_9'],                   'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_9_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_10:        {'name': ['input', 'Val_10'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_10_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_11:        {'name': ['input', 'Val_11'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_11_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_12:        {'name': ['input', 'Val_12'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_12_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_13:        {'name': ['input', 'Val_13'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_13_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_14:        {'name': ['input', 'Val_14'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_14_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_15:        {'name': ['input', 'Val_15'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_15_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_16:        {'name': ['input', 'Val_16'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_16_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_17:        {'name': ['input', 'Val_17'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_17_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_18:        {'name': ['input', 'Val_18'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_18_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_19:        {'name': ['input', 'Val_19'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_19_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_20:        {'name': ['input', 'Val_20'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_20_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_21:        {'name': ['input', 'Val_21'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_21_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_22:        {'name': ['input', 'Val_22'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_22_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_23:        {'name': ['input', 'Val_23'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_23_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_24:        {'name': ['input', 'Val_24'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_24_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_25:        {'name': ['input', 'Val_25'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_25_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_26:        {'name': ['input', 'Val_26'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_26_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_27:        {'name': ['input', 'Val_27'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_27_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_28:        {'name': ['input', 'Val_28'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_28_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_29:        {'name': ['input', 'Val_29'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_29_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_30:        {'name': ['input', 'Val_30'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_30_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_31:        {'name': ['input', 'Val_31'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_31_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_VAL_32:        {'name': ['input', 'Val_32'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'val_32_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501

        Register.TEST_IVAL_1:        {'name': ['input', 'iVal_1'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'ival_1_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_IVAL_2:        {'name': ['input', 'iVal_2'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'ival_2_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_IVAL_3:        {'name': ['input', 'iVal_3'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'ival_3_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_IVAL_4:        {'name': ['input', 'iVal_4'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'ival_4_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_IVAL_5:        {'name': ['input', 'iVal_5'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'ival_5_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_IVAL_6:        {'name': ['input', 'iVal_6'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'ival_6_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_IVAL_7:        {'name': ['input', 'iVal_7'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'ival_7_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_IVAL_8:        {'name': ['input', 'iVal_8'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'ival_8_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_IVAL_9:        {'name': ['input', 'iVal_9'],                  'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'ival_9_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_IVAL_10:        {'name': ['input', 'iVal_10'],                'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'ival_10_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_IVAL_11:        {'name': ['input', 'iVal_11'],                'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'ival_11_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
        Register.TEST_IVAL_12:        {'name': ['input', 'iVal_12'],                'level': logging.INFO, 'unit': '',     'ha': {'dev': 'inverter', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'ival_12_', 'fmt': FMT_INT, 'ent_cat': 'diagnostic'}},  # noqa: E501
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

    @classmethod
    def inc_counter(cls, counter: str) -> None:
        '''inc proxy statistic counter'''
        db_dict = cls.stat['proxy']
        db_dict[counter] += 1
        cls.new_stat_data['proxy'] = True

    @classmethod
    def dec_counter(cls, counter: str) -> None:
        '''dec proxy statistic counter'''
        db_dict = cls.stat['proxy']
        db_dict[counter] -= 1
        cls.new_stat_data['proxy'] = True

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

        # check if we have details for home assistant
        if 'ha' in row:
            return self.__ha_conf(row, key, ha_prfx, node_id, snr, sug_area)
        return None

    def __ha_conf(self, row, key, ha_prfx, node_id, snr,
                  sug_area: str) -> tuple[str, str, str, str] | None:
        ha = row['ha']
        if 'comp' in ha:
            component = ha['comp']
        else:
            component = 'sensor'
        attr = self.__build_attr(row, key, ha_prfx, node_id, snr)
        if 'dev' in ha:
            device = self.info_devs[ha['dev']]
            if 'dep' in device and self.ignore_this_device(device['dep']):  # noqa: E501
                return None
            attr['dev'] = self.__build_dev(device, key, ha, snr,
                                           sug_area)
            attr['o'] = self.__build_origin()

        else:
            self.inc_counter('Internal_Error')
            logging.error(f"Infos.info_defs: the row for {key} "
                          "missing 'dev' value for ha register")
        return json.dumps(attr), component, node_id, attr['uniq_id']

    def __build_attr(self, row, key, ha_prfx, node_id, snr):
        attr = {}
        ha = row['ha']
        if 'name' in ha:
            attr['name'] = ha['name']
        else:
            attr['name'] = row['name'][-1]
        prfx = ha_prfx + node_id
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
        return attr

    def __build_dev(self, device, key, ha, snr, sug_area):
        dev = {}
        singleton = 'singleton' in device and device['singleton']
        # the same name for 'name' and 'suggested area', so we get
        # dedicated devices in home assistant with short value
        # name and headline
        if (sug_area == '' or singleton):
            dev['name'] = device['name']
            dev['sa'] = device['name']
        else:
            dev['name'] = device['name']+' - '+sug_area
            dev['sa'] = device['name']+' - '+sug_area
        self.__add_via_dev(dev, device, key, snr)
        for key in ('mdl', 'mf', 'sw', 'hw', 'sn'):      # add optional
            # values fpr 'modell', 'manufacturer', 'sw version' and
            # 'hw version'
            if key in device:
                data = self.dev_value(device[key])
                if data is not None:
                    dev[key] = data
        if singleton:
            dev['ids'] = [f"{ha['dev']}"]
        else:
            dev['ids'] = [f"{ha['dev']}_{snr}"]
        self.__add_connection(dev, device)
        return dev

    def __add_connection(self, dev, device):
        if 'mac' in device:
            mac_str = self.dev_value(device['mac'])
            if mac_str is not None:
                if 12 == len(mac_str):
                    mac_str = ':'.join(mac_str[i:i+2] for i in range(0, 12, 2))
                dev['cns'] = [["mac", f"{mac_str}"]]

    def __add_via_dev(self, dev, device, key, snr):
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

    def __build_origin(self):
        origin = {}
        origin['name'] = self.app_name
        origin['sw'] = self.version
        return origin

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
        if id not in self.info_defs:
            return not_found_result
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
