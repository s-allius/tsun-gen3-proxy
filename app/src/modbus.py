'''MODBUS  module for TSUN inverter support

TSUN uses the MODBUS in the RTU transmission mode over serial line.
see: https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf
see: https://modbus.org/docs/Modbus_over_serial_line_V1_02.pdf

A Modbus PDU consists of: 'Function-Code' + 'Data'
A Modbus RTU message consists of: 'Addr' + 'Modbus-PDU' + 'CRC-16'
The inverter is a MODBUS server and the proxy the MODBUS client.

The 16-bit CRC is known as CRC-16-ANSI(reverse)
see: https://en.wikipedia.org/wiki/Computation_of_cyclic_redundancy_checks
'''
import struct
import logging
import asyncio
from typing import Generator, Callable

from infos import Register, Fmt

logger = logging.getLogger('data')

CRC_POLY = 0xA001  # (LSBF/reverse)
CRC_INIT = 0xFFFF


class Modbus():
    '''Simple MODBUS implementation with TX queue and retransmit timer'''

    # Error codes
    ERR_CRC = 1
    '''CRC error: The received message has an invalid CRC checksum.'''

    ERR_WRONG_ADDR = 2
    '''Wrong server address:
    The response address does not match the expected address.'''

    ERR_UNEXPECTED_FCODE = 3
    '''Unexpected function code:
    The function code in the response does not match the request.'''

    ERR_UNEXPECTED_LEN = 4
    '''Unexpected data length:
    The length of the data in the response does not match
    the expected length.'''

    ERR_NO_REQ_PENDING = 5
    '''No MODBUS request pending:
    A response was received, but no request is currently pending.'''

    ERR_UNKNOWN_ADDR = 6
    '''Unknown start register address:
    The response indicates an unknown register address.'''

    ERR_INVALID_LEN = 7
    '''Invalid length requested:
    The response indicates an invalid length in the request.'''

    ERR_UNKNOWN_STATUS = 8
    '''Unknown status code:
    The response contains an unrecognized status code.'''

    INV_ADDR = 1
    '''MODBUS server address of the TSUN inverter'''
    READ_REGS = 3
    '''MODBUS function code: Read Holding Register'''
    READ_INPUTS = 4
    '''MODBUS function code: Read Input Register'''
    WRITE_SINGLE_REG = 6
    '''Modbus function code: Write Single Register'''

    NATIVE_READ_VALUES = (0xA1, 0x01)
    '''MODBUS function code: Read Measurement Values (native)'''
    NATIVE_READ_ALARMS = (0xA2, 0x02)
    '''MODBUS function code: Read Alarm Values (native)'''
    NATIVE_READ_BLOCK_A = (0xA3, 0x03)
    '''MODBUS function code: Read Input Block A Values (native)'''
    NATIVE_READ_BLOCK_B = (0xA4, 0x04)
    '''MODBUS function code: Read Input Block B Values (native)'''
    NATIVE_READ_REGS = (0xA1, 0x21)
    '''MODBUS function code: Read Holding Register (native)'''

    __crc_tab = []
    mb_reg_mapping = {
        # sensor_list: 0x3026
        0x0000: {'reg': Register.SERIAL_NUMBER,        'fmt': '!16s'},               # noqa: E501
        0x0008: {'reg': Register.BATT_PV1_VOLT,        'fmt': '!H', 'ratio': 0.01},  # noqa: E501, PV1 voltage
        0x0009: {'reg': Register.BATT_PV1_CUR,         'fmt': '!H', 'ratio': 0.01},  # noqa: E501, PV1 current
        0x000a: {'reg': Register.BATT_PV2_VOLT,        'fmt': '!H', 'ratio': 0.01},  # noqa: E501, PV2 voltage
        0x000b: {'reg': Register.BATT_PV2_CUR,         'fmt': '!H', 'ratio': 0.01},  # noqa: E501, PV2 current
        0x000c: {'reg': Register.BATT_TOTAL_CHARG,     'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x000e: {'reg': Register.BATT_PV1_STATUS,      'fmt': '!H'},                 # noqa: E501
        0x000f: {'reg': Register.BATT_PV2_STATUS,      'fmt': '!H'},                 # noqa: E501
        0x0010: {'reg': Register.BATT_VOLT,            'fmt': '!h', 'ratio': 0.01},  # noqa: E501
        0x0011: {'reg': Register.BATT_CUR,             'fmt': '!h', 'ratio': 0.01},  # noqa: E501
        0x0012: {'reg': Register.BATT_SOC,             'fmt': '!H', 'ratio': 0.01},  # noqa: E501, state of charge (SOC) in percent
        0x0013: {'reg': Register.BATT_CELL1_VOLT,      'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x0014: {'reg': Register.BATT_CELL2_VOLT,      'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x0015: {'reg': Register.BATT_CELL3_VOLT,      'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x0016: {'reg': Register.BATT_CELL4_VOLT,      'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x0017: {'reg': Register.BATT_CELL5_VOLT,      'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x0018: {'reg': Register.BATT_CELL6_VOLT,      'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x0019: {'reg': Register.BATT_CELL7_VOLT,      'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x001a: {'reg': Register.BATT_CELL8_VOLT,      'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x001b: {'reg': Register.BATT_CELL9_VOLT,      'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x001c: {'reg': Register.BATT_CELL10_VOLT,     'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x001d: {'reg': Register.BATT_CELL11_VOLT,     'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x001e: {'reg': Register.BATT_CELL12_VOLT,     'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x001f: {'reg': Register.BATT_CELL13_VOLT,     'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x0020: {'reg': Register.BATT_CELL14_VOLT,     'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x0021: {'reg': Register.BATT_CELL15_VOLT,     'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x0022: {'reg': Register.BATT_CELL16_VOLT,     'fmt': '!H', 'ratio': 0.001},  # noqa: E501
        0x0023: {'reg': Register.BATT_TEMP_1,          'fmt': '!h'},                 # noqa: E501
        0x0024: {'reg': Register.BATT_TEMP_2,          'fmt': '!h'},                 # noqa: E501
        0x0025: {'reg': Register.BATT_TEMP_3,          'fmt': '!h'},                 # noqa: E501
        0x0026: {'reg': Register.BATT_OUT_VOLT,        'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x0027: {'reg': Register.BATT_OUT_CUR,         'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x0028: {'reg': Register.BATT_OUT_STATUS,      'fmt': '!H'},                 # noqa: E501
        0x0029: {'reg': Register.BATT_TEMP_4,          'fmt': '!h'},                 # noqa: E501
        0x002a: {'reg': Register.BATT_ALARM,           'fmt': '!h'},                 # noqa: E501
        0x002b: {'reg': Register.BATT_HW_VERS,         'fmt': '!h'},                 # noqa: E501
        0x002c: {'reg': Register.BATT_SW_VERS,         'fmt': '!h'},                 # noqa: E501

        # sensor_list: 0x1511
        2000:   {'reg': Register.PROD_COMPL_TYPE,      'fmt': '<H'},
        2042:   {'reg': Register.MAX_DESIGNED_POWER,   'fmt': '<H', 'ratio':  1},    # noqa: E501

        3000:   {'reg': Register.INVERTER_STATUS,      'fmt': '<H'},                 # noqa: E501
        # 3008:   {'reg': Register.VERSION,              'fmt': '<H', 'func': Fmt.version},  # noqa: E501
        # 3009:   {'reg': Register.TEST_VAL_1,           'fmt': '<H', 'ratio': 1},    # noqa: E501
        3010:   {'reg': Register.DC1_BUS_VOLTAGE,      'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        # 3011:   {'reg': Register.TEST_VAL_3,           'fmt': '<H', 'ratio': 1},    # noqa: E501
        3012:   {'reg': Register.GRID_VOLTAGE,         'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3013:   {'reg': Register.GRID_CURRENT,         'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        # 3014:   {'reg': Register.TEST_VAL_4,           'fmt': '<H', 'ratio': 1},    # noqa: E501
        3015:   {'reg': Register.GRID_FREQUENCY,       'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        # 3016:   {'reg': Register.TEST_VAL_5,           'fmt': '<H', 'ratio': 1},    # noqa: E501
        3017:   {'reg': Register.INVERTER_TEMP,        'fmt': '<H', 'offset': -40},  # noqa: E501
        # 3018:   {'reg': Register.TEST_VAL_6,           'fmt': '<H', 'ratio': 1},    # noqa: E501
        3019:   {'reg': Register.DC2_BUS_VOLTAGE,      'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        3020:   {'reg': Register.RATED_POWER,          'fmt': '<H', 'ratio':    1},  # noqa: E501
        3021:   {'reg': Register.OUTPUT_POWER,         'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3022:   {'reg': Register.DAILY_GENERATION,     'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        3023:   {'reg': Register.TOTAL_GENERATION,     'fmt': '<HH', 'func': Fmt.swap, 'ratio': 0.01},  # noqa: E501
        # 3025:   {'reg': Register.TEST_VAL_8,           'fmt': '<H', 'ratio': 1},    # noqa: E501
        # 3026:   {'reg': Register.TEST_VAL_9,           'fmt': '<H', 'ratio': 1},    # noqa: E501
        # 3027:   {'reg': Register.TEST_VAL_10,          'fmt': '<H', 'ratio': 1},    # noqa: E501
        3028:   {'reg': Register.AMBIENT_TEMP,         'fmt': '<H', 'offset': -40},  # noqa: E501
        # 3029:   {'reg': Register.TEST_VAL_11,          'fmt': '<H', 'ratio': 1},    # noqa: E501
        # 3030:   {'reg': Register.TEST_VAL_12,          'fmt': '<H', 'ratio': 1},    # noqa: E501
        # 3031:   {'reg': Register.TEST_VAL_13,          'fmt': '<H', 'ratio': 1},    # noqa: E501

        3600:   {'reg': Register.PV1_VOLTAGE,           'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3601:   {'reg': Register.PV1_CURRENT,           'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        3602:   {'reg': Register.PV1_POWER,             'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3603:   {'reg': Register.PV1_DAILY_GENERATION,  'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        3607:   {'reg': Register.PV2_VOLTAGE,           'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3608:   {'reg': Register.PV2_CURRENT,           'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        3609:   {'reg': Register.PV2_POWER,             'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3610:   {'reg': Register.PV2_DAILY_GENERATION,  'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        3614:   {'reg': Register.PV3_VOLTAGE,           'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3615:   {'reg': Register.PV3_CURRENT,           'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        3616:   {'reg': Register.PV3_POWER,             'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3617:   {'reg': Register.PV3_DAILY_GENERATION,  'fmt': '<H', 'ratio': 0.01},  # noqa: E501

        3624:   {'reg': Register.PV1_TOTAL_GENERATION,  'fmt': '<HH', 'func': Fmt.swap, 'ratio': 0.01},  # noqa: E501
        3626:   {'reg': Register.PV2_TOTAL_GENERATION,  'fmt': '<HH', 'func': Fmt.swap, 'ratio': 0.01},  # noqa: E501
        3628:   {'reg': Register.PV3_TOTAL_GENERATION,  'fmt': '<HH', 'func': Fmt.swap, 'ratio': 0.01},  # noqa: E501

        3800:   {'reg': Register.PV4_VOLTAGE,           'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3801:   {'reg': Register.PV4_CURRENT,           'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        3802:   {'reg': Register.PV4_POWER,             'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3803:   {'reg': Register.PV4_DAILY_GENERATION,  'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        3807:   {'reg': Register.PV5_VOLTAGE,           'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3808:   {'reg': Register.PV5_CURRENT,           'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        3809:   {'reg': Register.PV5_POWER,             'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3810:   {'reg': Register.PV5_DAILY_GENERATION,  'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        3814:   {'reg': Register.PV6_VOLTAGE,           'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3815:   {'reg': Register.PV6_CURRENT,           'fmt': '<H', 'ratio': 0.01},  # noqa: E501
        3816:   {'reg': Register.PV6_POWER,             'fmt': '<H', 'ratio': 0.1},   # noqa: E501
        3817:   {'reg': Register.PV6_DAILY_GENERATION,  'fmt': '<H', 'ratio': 0.01},  # noqa: E501

        3824:   {'reg': Register.PV4_TOTAL_GENERATION,  'fmt': '<HH', 'func': Fmt.swap, 'ratio': 0.01},  # noqa: E501
        3826:   {'reg': Register.PV5_TOTAL_GENERATION,  'fmt': '<HH', 'func': Fmt.swap, 'ratio': 0.01},  # noqa: E501
        3828:   {'reg': Register.PV6_TOTAL_GENERATION,  'fmt': '<HH', 'func': Fmt.swap, 'ratio': 0.01},  # noqa: E501

        # sensor_list: 0x1097
        0x1000: {'reg': Register.SERIAL_NUMBER,        'fmt': '!16s'},               # noqa: E501
        # 0x1008: {},  # val 0002
        # 0x1009: {},  # val 0006
        0x100a: {'reg': Register.PROT_VERSION,         'fmt': '!H', 'func': Fmt.version},  # noqa: E501
        0x100c: {'reg': Register.VERSION,              'fmt': '!H', 'func': Fmt.version},  # noqa: E501

        # 0x1100: val 0001 or 0002
        0x1100: {'reg': Register.INVERTER_STATUS,      'fmt': '!H'},                 # noqa: E501
        # 0x1104: {},  # val ff01
        # 0x1105. val 0000 or 0008 (temp alaram)
        0x1105: {'reg': Register.EVENT_ALARM,          'fmt': '!H'},                 # noqa: E501
        0x1106: {'reg': Register.EVENT_FAULT,          'fmt': '!H'},                 # noqa: E501
        0x1107: {'reg': Register.EVENT_BF1,            'fmt': '!H'},                 # noqa: E501
        0x1108: {'reg': Register.EVENT_BF2,            'fmt': '!H'},                 # noqa: E501

        0x1200: {'reg': Register.GRID_VOLTAGE,         'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x1201: {'reg': Register.GRID_CURRENT,         'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x1202: {'reg': Register.OUTPUT_POWER,         'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x1203: {'reg': Register.TEST_VAL_3,           'fmt': '!H'},                 # noqa: E501
        0x1209: {'reg': Register.GRID_FREQUENCY,       'fmt': '!H', 'ratio': 0.01},  # noqa: E501

        0x1210: {'reg': Register.RATED_POWER,          'fmt': '!H'},                 # noqa: E501
        0x1211: {'reg': Register.TEST_VAL_6,           'fmt': '!H'},                 # noqa: E501
        0x1212: {'reg': Register.DAILY_GENERATION,     'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x1213: {'reg': Register.TOTAL_GENERATION,     'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x1215: {'reg': Register.TEST_VAL_10,          'fmt': '!H'},                 # noqa: E501
        0x1216: {'reg': Register.INSULATION_IMP_RX,    'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x1217: {'reg': Register.INSULATION_IMP_RY,    'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x1218: {'reg': Register.INVERTER_TEMP,        'fmt': '!H', 'offset': -40},  # noqa: E501

        0x1302: {'reg': Register.PV1_VOLTAGE,           'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x1303: {'reg': Register.PV1_CURRENT,           'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x1304: {'reg': Register.PV1_POWER,             'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x1305: {'reg': Register.PV1_DAILY_GENERATION,  'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x1307: {'reg': Register.PV1_TOTAL_GENERATION,  'fmt': '!L', 'ratio': 0.01},  # noqa: E501

        0x1309: {'reg': Register.PV2_VOLTAGE,           'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x130a: {'reg': Register.PV2_CURRENT,           'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x130b: {'reg': Register.PV2_POWER,             'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x130c: {'reg': Register.PV2_DAILY_GENERATION,  'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x130e: {'reg': Register.PV2_TOTAL_GENERATION,  'fmt': '!L', 'ratio': 0.01},  # noqa: E501

        0x1310: {'reg': Register.PV3_VOLTAGE,           'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x1311: {'reg': Register.PV3_CURRENT,           'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x1312: {'reg': Register.PV3_POWER,             'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x1313: {'reg': Register.PV3_DAILY_GENERATION,  'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x1315: {'reg': Register.PV3_TOTAL_GENERATION,  'fmt': '!L', 'ratio': 0.01},  # noqa: E501

        0x1317: {'reg': Register.PV4_VOLTAGE,           'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x1318: {'reg': Register.PV4_CURRENT,           'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x1319: {'reg': Register.PV4_POWER,             'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x131a: {'reg': Register.PV4_DAILY_GENERATION,  'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x131c: {'reg': Register.PV4_TOTAL_GENERATION,  'fmt': '!L', 'ratio': 0.01},  # noqa: E501

        0x131e: {'reg': Register.PV5_VOLTAGE,           'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x131f: {'reg': Register.PV5_CURRENT,           'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x1320: {'reg': Register.PV5_POWER,             'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x1321: {'reg': Register.PV5_DAILY_GENERATION,  'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x1323: {'reg': Register.PV5_TOTAL_GENERATION,  'fmt': '!L', 'ratio': 0.01},  # noqa: E501

        0x1325: {'reg': Register.PV6_VOLTAGE,           'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x1326: {'reg': Register.PV6_CURRENT,           'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x1327: {'reg': Register.PV6_POWER,             'fmt': '!H', 'ratio': 0.1},   # noqa: E501
        0x1328: {'reg': Register.PV6_DAILY_GENERATION,  'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x132a: {'reg': Register.PV6_TOTAL_GENERATION,  'fmt': '!L', 'ratio': 0.01},  # noqa: E501

        0x1400: {'reg': Register.PROD_COMPL_TYPE,      'fmt': '!H'},
        0x1437: {'reg': Register.MAX_DESIGNED_POWER,   'fmt': '!H', 'ratio':  1},    # noqa: E501

        # sensor_list: 0x020b
        0x2000: {'reg': Register.BOOT_STATUS,          'fmt': '!H'},                 # noqa: E501
        0x2001: {'reg': Register.DSP_STATUS,           'fmt': '!H'},                 # noqa: E501
        0x2003: {'reg': Register.WORK_MODE,            'fmt': '!H'},
        0x2006: {'reg': Register.OUTPUT_SHUTDOWN,      'fmt': '!H'},
        0x2007: {'reg': Register.MAX_DESIGNED_POWER,   'fmt': '!H', 'ratio':  1},    # noqa: E501
        0x2008: {'reg': Register.RATED_LEVEL,          'fmt': '!H'},
        0x2009: {'reg': Register.INPUT_COEFFICIENT,    'fmt': '!H', 'ratio':  100/1024},  # noqa: E501
        0x200a: {'reg': Register.GRID_VOLT_CAL_COEF,   'fmt': '!H'},
        0x2010: {'reg': Register.PROD_COMPL_TYPE,      'fmt': '!H'},
        0x202c: {'reg': Register.OUTPUT_COEFFICIENT,   'fmt': '!H', 'ratio':  100/1024},  # noqa: E501
        # 0x204a: Zero Export Power Offset Value val(-32768 .. 32767)
        # 0x2047: Total Rated Power of Solar Plant (0..0xffff)
        # 0x2048: Zero Export Status.  # val: 0(off), 1(on),
        # sensor_list: 0x020b
        0x3000: {'reg': Register.INVERTER_STATUS,      'fmt': '!H'},                 # noqa: E501
        0x3001: {'reg': Register.DETECT_STATUS_1,      'fmt': '!H'},                 # noqa: E501
        0x3002: {'reg': Register.DETECT_STATUS_2,      'fmt': '!H'},                 # noqa: E501
        0x3003: {'reg': Register.EVENT_ALARM,          'fmt': '!H'},                 # noqa: E501
        0x3004: {'reg': Register.EVENT_FAULT,          'fmt': '!H'},                 # noqa: E501
        0x3005: {'reg': Register.EVENT_BF1,            'fmt': '!H'},                 # noqa: E501
        0x3006: {'reg': Register.EVENT_BF2,            'fmt': '!H'},                 # noqa: E501

        0x3008: {'reg': Register.VERSION,              'fmt': '!H', 'func': Fmt.version},  # noqa: E501
        0x3009: {'reg': Register.GRID_VOLTAGE,         'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x300a: {'reg': Register.GRID_CURRENT,         'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x300b: {'reg': Register.GRID_FREQUENCY,       'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x300c: {'reg': Register.INVERTER_TEMP,        'fmt': '!H', 'offset': -40},  # noqa: E501
        # 0x300d
        0x300e: {'reg': Register.RATED_POWER,          'fmt': '!H', 'ratio':    1},  # noqa: E501
        0x300f: {'reg': Register.OUTPUT_POWER,         'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x3010: {'reg': Register.PV1_VOLTAGE,          'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x3011: {'reg': Register.PV1_CURRENT,          'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x3012: {'reg': Register.PV1_POWER,            'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x3013: {'reg': Register.PV2_VOLTAGE,          'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x3014: {'reg': Register.PV2_CURRENT,          'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x3015: {'reg': Register.PV2_POWER,            'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x3016: {'reg': Register.PV3_VOLTAGE,          'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x3017: {'reg': Register.PV3_CURRENT,          'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x3018: {'reg': Register.PV3_POWER,            'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x3019: {'reg': Register.PV4_VOLTAGE,          'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x301a: {'reg': Register.PV4_CURRENT,          'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x301b: {'reg': Register.PV4_POWER,            'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x301c: {'reg': Register.DAILY_GENERATION,     'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x301d: {'reg': Register.TOTAL_GENERATION,     'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x301f: {'reg': Register.PV1_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x3020: {'reg': Register.PV1_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x3022: {'reg': Register.PV2_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x3023: {'reg': Register.PV2_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x3025: {'reg': Register.PV3_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x3026: {'reg': Register.PV3_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x3028: {'reg': Register.PV4_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x3029: {'reg': Register.PV4_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        # 0x302a
    }

    def __init__(self, snd_handler: Callable[[bytes, int, str], None],
                 timeout: int = 1):
        if not len(self.__crc_tab):
            self.__build_crc_tab(CRC_POLY)
        self.que = asyncio.Queue(100)
        self.snd_handler = snd_handler
        '''Send handler to transmit a MODBUS RTU request'''
        self.rsp_handler = None
        '''Response handler to forward the response'''
        self.timeout = timeout
        '''MODBUS response timeout in seconds'''
        self.max_retries = 1
        '''Max retransmit for MODBUS requests'''
        self.retry_cnt = 0
        self.last_req = b''
        self.counter = {}
        '''Dictenary with statistic counter'''
        self.counter['timeouts'] = 0
        self.counter['retries'] = {}
        for i in range(0, self.max_retries+1):
            self.counter['retries'][f'{i}'] = 0
        self.last_log_lvl = logging.DEBUG
        self.last_addr = 0
        self.last_fcode = 0
        self.last_len = 0
        self.last_reg = 0
        self.err = 0
        self.loop = asyncio.get_event_loop()
        self.req_pend = False
        self.tim = None
        self.node_id = ''

    def close(self):
        """free the queue and erase the callback handlers"""
        logging.debug('Modbus close:')
        self.__stop_timer()
        self.rsp_handler = None
        self.snd_handler = None
        while not self.que.empty():
            self.que.get_nowait()

    def set_node_id(self, node_id: str):
        self.node_id = node_id

    def build_native_msg(
            self, func: bytearray, reg: int, val: int,
            log_lvl=logging.DEBUG) -> None:
        """Build TSUN native MODBUS request frame and add it to the tx queue

        Keyword arguments:
            func[0]: MODBUS function code
            func[1]: sub address
            reg:  16-bit register number
            val:  16 bit value

        """
        msg = struct.pack('>BBBHHH', func[0], func[1], 0, reg, 2, val)
        msg += struct.pack('>H', self.__calc_crc(msg))
        self.que.put_nowait({'req': msg,
                             'rsp_hdl': None,
                             'log_lvl': log_lvl})
        if self.que.qsize() == 1:
            self.__send_next_from_que()

    def build_msg(self, addr: int, func: int, reg: int, val: int,
                  log_lvl=logging.DEBUG) -> None:
        """Build MODBUS RTU request frame and add it to the tx queue

        Keyword arguments:
            addr: RTU server address (inverter)
            func: MODBUS function code
            reg:  16-bit register number
            val:  16 bit value
        """
        msg = struct.pack('>BBHH', addr, func, reg, val)
        msg += struct.pack('<H', self.__calc_crc(msg))
        self.que.put_nowait({'req': msg,
                             'rsp_hdl': None,
                             'log_lvl': log_lvl})
        if self.que.qsize() == 1:
            self.__send_next_from_que()

    def recv_req(self, buf: bytes,
                 rsp_handler: Callable[[None], None] = None) -> bool:
        """Add the received Modbus RTU request to the tx queue

        Keyword arguments:
            buf: Modbus RTU pdu incl ADDR byte and trailing CRC
            rsp_handler: Callback, if the received pdu is valid

        Returns:
            True:   PDU was added to the queue
            False:  PDU was ignored, due to an error
        """
        # logging.info(f'recv_req: first byte modbus:{buf[0]} len:{len(buf)}')
        if not self.__check_crc(buf):
            self.err = 1
            logger.error('Modbus recv: CRC error')
            return False
        self.que.put_nowait({'req': buf,
                             'rsp_hdl': rsp_handler,
                             'log_lvl': logging.INFO})
        if self.que.qsize() == 1:
            self.__send_next_from_que()

        return True

    def recv_native_resp(
            self, info_db, buf: bytes
            ) -> Generator[tuple[str, bool, int | float | str], None, None]:
        """Generator which checks and parses a received MODBUS response."""
        fcode, status_code, first_reg, last_len = \
            self.__parse_native_response(buf)
        data_available = status_code == 0x01 and fcode in {
            0xa1, 0xa2, 0xa3, 0xa4}
        self.err = 0

        if self.__native_resp_error_check(buf, data_available, last_len):
            return

        yield from self.__handle_response(data_available, info_db, buf[7:],
                                          first_reg, last_len >> 1)

    def __native_resp_error_check(
            self, buf: bytes, data_available: bool, elmlen: int
            ) -> bool:
        """Check the MODBUS response for errors, returns True if one occurs."""
        if not self.req_pend:
            return self.__set_error(self.ERR_NO_REQ_PENDING)

        if not self.__check_crc(buf, swap_crc=True):
            logger.error(f'[{self.node_id}] Native resp: CRC error')
            return self.__set_error(self.ERR_CRC)

        if self.__check_status_code(buf[2]):
            return True

        if self.__check_function_code(buf[0]) or \
           self.__check_data_length(data_available, elmlen):
            return True

        return False

    def recv_resp(
            self, info_db, buf: bytes
            ) -> Generator[tuple[str, bool, int | float | str], None, None]:
        """Generator which checks and parses a received MODBUS response."""
        fcode = buf[1]
        data_available = self.last_addr == self.INV_ADDR and fcode in {3, 4}
        self.err = 0

        if self.__resp_error_check(buf, data_available):
            return

        yield from self.__handle_response(data_available, info_db,
                                          buf[3:], self.last_reg, buf[2] >> 1)

    def __resp_error_check(self, buf: bytes, data_available: bool) -> bool:
        """Check the MODBUS response for errors, returns True if one occurs."""
        if not self.req_pend:
            return self.__set_error(self.ERR_NO_REQ_PENDING)

        if not self.__check_crc(buf):
            logger.error(f'[{self.node_id}] Modbus resp: CRC error')
            return self.__set_error(self.ERR_CRC)

        if buf[0] != self.last_addr:
            logger.info(f'[{self.node_id}] Modbus resp: Wrong addr {buf[0]}')
            return self.__set_error(self.ERR_WRONG_ADDR)

        if self.__check_function_code(buf[1]) or \
           self.__check_data_length(data_available, buf[2] >> 1):
            return True

        return False

    # Neue Hilfsfunktionen
    def __parse_native_response(self, buf: bytes) -> tuple[int, int, int, int]:
        """Parse the native MODBUS response."""
        fcode = buf[0]
        status_code = buf[2]
        first_reg, last_len = struct.unpack_from('!HH', buf, 3)
        return fcode, status_code, first_reg, last_len

    def __set_error(self, code: int) -> bool:
        """Set the error code and return True."""
        self.err = code
        return True

    def __check_status_code(self, status_code: int) -> bool:
        """Check the status code for errors."""
        match status_code:
            case 0x01:
                return False
            case 0x11:
                logger.info(f'[{self.node_id}] Native resp: Unknown addr')
                return self.__set_error(self.ERR_UNKNOWN_ADDR)
            case 0x12:
                logger.info(f'[{self.node_id}] Native resp: Invalid length')
                return self.__set_error(self.ERR_INVALID_LEN)
            case _:
                logger.info(f'[{self.node_id}] Native resp: '
                            f'Unknown status code {status_code}')
                return self.__set_error(self.ERR_UNKNOWN_STATUS)

    def __check_function_code(self, fcode: int) -> bool:
        """Check if the function code matches the last function code."""
        if fcode != self.last_fcode:
            logger.info(f'[{self.node_id}] Native resp: '
                        f'Wrong fcode {fcode} != {self.last_fcode}')
            return self.__set_error(self.ERR_UNEXPECTED_FCODE)
        return False

    def __check_data_length(self, data_available: bool, elmlen: int) -> bool:
        """Check if the data length matches the expected length."""
        if data_available and elmlen != self.last_len:
            logger.info(f'[{self.node_id}] Native resp: '
                        f'len error {elmlen} != {self.last_len}')
            return self.__set_error(self.ERR_UNEXPECTED_LEN)
        return False

    def __handle_response(
            self, data_available: bool, info_db, buf: bytes,
            first_reg: int, elmlen: int
            ) -> Generator[tuple[str, bool, int | float | str], None, None]:
        """Generator which parses a received MODBUS data."""
        if data_available:
            self.__stop_timer()
            yield from self.__process_data(info_db, buf, first_reg, elmlen)
        else:
            self.__stop_timer()

        self.counter['retries'][f'{self.retry_cnt}'] += 1
        if self.rsp_handler:
            self.rsp_handler()
        self.__send_next_from_que()

    def __process_data(self, info_db, buf: bytes, first_reg, elmlen):
        '''Generator over received registers, updates the db'''
        for i in range(0, elmlen):
            addr = first_reg+i
            if addr in self.mb_reg_mapping:
                row = self.mb_reg_mapping[addr]
                info_id = row['reg']
                keys, level, unit, must_incr = info_db._key_obj(info_id)
                if keys:
                    result = Fmt.get_value(buf, 2*i, row)
                    name, update = info_db.update_db(keys, must_incr,
                                                     result)
                    yield keys[0], update, result
                    if update:
                        info_db.tracer.log(level,
                                           f'[{self.node_id}] MODBUS: {name}'
                                           f' : {result}{unit}')
                        logging.log(level, f'[{self.node_id}] MODBUS: {name} :'
                                           f' {result}{unit}')

    '''
    MODBUS response timer
    '''
    def __start_timer(self) -> None:
        '''Start response timer and set `req_pend` to True'''
        self.req_pend = True
        self.tim = self.loop.call_later(self.timeout, self.__timeout_cb)
        # logging.debug(f'Modbus start timer {self}')

    def __stop_timer(self) -> None:
        '''Stop response timer and set `req_pend` to False'''
        self.req_pend = False
        # logging.debug(f'Modbus stop timer {self}')
        if self.tim:
            self.tim.cancel()
            self.tim = None

    def __timeout_cb(self) -> None:
        '''Rsponse timeout handler retransmit pdu or send next pdu'''
        self.req_pend = False

        if self.retry_cnt < self.max_retries:
            logger.debug(f'Modbus retrans {self}')
            self.retry_cnt += 1
            self.__start_timer()
            self.snd_handler(self.last_req, self.last_log_lvl, state='Retrans')
        else:
            logger.info(f'[{self.node_id}] Modbus timeout '
                        f'(FCode: {self.last_fcode} '
                        f'Reg: 0x{self.last_reg:04x}, '
                        f'{self.last_len})')
            self.counter['timeouts'] += 1
            self.__send_next_from_que()

    def __send_next_from_que(self) -> None:
        '''Get next MODBUS pdu from queue and transmit it'''
        if self.req_pend:
            return
        try:
            item = self.que.get_nowait()
            req = item['req']
            self.last_req = req
            self.rsp_handler = item['rsp_hdl']
            self.last_log_lvl = item['log_lvl']
            if req[0] >= 0xA1:
                self.last_fcode = req[0]
                self.last_addr = req[1]

                res = struct.unpack_from('>HHH', req, 3)
                self.last_reg = res[0]
                self.last_len = res[1] * res[2]
            else:
                self.last_addr = req[0]
                self.last_fcode = req[1]

                res = struct.unpack_from('>HH', req, 2)
                self.last_reg = res[0]
                self.last_len = res[1]
            self.retry_cnt = 0
            self.__start_timer()
            self.snd_handler(self.last_req, self.last_log_lvl, state='Command')
        except asyncio.QueueEmpty:
            pass

    '''
    Helper function for CRC-16 handling
    '''
    def __check_crc(self, msg: bytes, swap_crc: bool = False) -> bool:
        '''Check CRC-16 and returns True if valid'''
        if swap_crc:
            # swap crc bytes for native response, to match the crc check
            msg = msg[0:-2] + msg[-2:][::-1]

        valid = 0 == self.__calc_crc(msg)
        if not valid:
            crc = self.__calc_crc(msg[:-2])
            logging.info(f'CRC error: {msg[-1]:02x}{msg[-2]:02x} != {crc:04x}'
                         f' for msg: {msg.hex()}')
        return valid

    def __calc_crc(self, buffer: bytes) -> int:
        '''Build CRC-16 for buffer and returns it'''
        crc = CRC_INIT

        for cur in buffer:
            crc = (crc >> 8) ^ self.__crc_tab[(crc ^ cur) & 0xFF]
        return crc

    def __build_crc_tab(self, poly: int) -> None:
        '''Build CRC-16 helper table, must be called exactly one time'''
        for index in range(256):
            data = index << 1
            crc = 0
            for _ in range(8, 0, -1):
                data >>= 1
                if (data ^ crc) & 1:
                    crc = (crc >> 1) ^ poly
                else:
                    crc >>= 1
            self.__crc_tab.append(crc)
