import struct
import logging
from typing import Generator

if __name__ == "app.src.modbus":
    from app.src.infos import Register
else:  # pragma: no cover
    from infos import Register

#######
# TSUN uses the Modbus in the RTU transmission mode.
# see: https://modbus.org/docs/Modbus_over_serial_line_V1_02.pdf
#
# A Modbus PDU consists of: 'Function-Code' + 'Data'
# A Modbus RTU message consists of: 'Addr' + 'Modbus-PDU' + 'CRC-16'
#
# The 16-bit CRC is known as CRC-16-ANSI(reverse)
# see: https://en.wikipedia.org/wiki/Computation_of_cyclic_redundancy_checks
#######

CRC_POLY = 0xA001  # (LSBF/reverse)
CRC_INIT = 0xFFFF


class Modbus():
    INV_ADDR = 1
    READ_REGS = 3
    READ_INPUTS = 4
    WRITE_SINGLE_REG = 6
    '''Modbus function codes'''

    __crc_tab = []
    map = {
        0x2007: {'reg': Register.MAX_DESIGNED_POWER,   'fmt': '!H', 'ratio':  1},  # noqa: E501
        # 0x????: {'reg': Register.INVERTER_STATUS,      'fmt': '!H'},                 # noqa: E501
        0x3008: {'reg': Register.VERSION,              'fmt': '!H', 'eval': "f'v{(result>>12)}.{(result>>8)&0xf}.{(result>>4)&0xf}{result&0xf}'"},  # noqa: E501
        0x3009: {'reg': Register.GRID_VOLTAGE,         'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x300a: {'reg': Register.GRID_CURRENT,         'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x300b: {'reg': Register.GRID_FREQUENCY,       'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x300c: {'reg': Register.INVERTER_TEMP,        'fmt': '!H', 'eval': 'result-40'},  # noqa: E501
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
        # 0x301d: {'reg': Register.TOTAL_GENERATION,     'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x301f: {'reg': Register.PV1_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        # 0x3020: {'reg': Register.PV1_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x3022: {'reg': Register.PV2_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        # 0x3023: {'reg': Register.PV2_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x3025: {'reg': Register.PV3_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        # 0x3026: {'reg': Register.PV3_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x3028: {'reg': Register.PV4_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        # 0x3029: {'reg': Register.PV4_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
    }

    def __init__(self):
        if not len(self.__crc_tab):
            self.__build_crc_tab(CRC_POLY)
        self.last_fcode = 0
        self.last_len = 0
        self.last_reg = 0
        self.err = 0

    def build_msg(self, addr, func, reg, val):
        msg = struct.pack('>BBHH', addr, func, reg, val)
        msg += struct.pack('<H', self.__calc_crc(msg))
        self.last_fcode = func
        self.last_reg = reg
        self.last_len = val
        self.err = 0
        return msg

    def recv_req(self, buf: bytearray) -> bool:
        # logging.info(f'recv_req: first byte modbus:{buf[0]} len:{len(buf)}')
        if not self.check_crc(buf):
            self.err = 1
            logging.error('Modbus: CRC error')
            return False
        if buf[0] != self.INV_ADDR:
            self.err = 2
            logging.info(f'Modbus: Wrong addr{buf[0]}')
            return False
        res = struct.unpack_from('>BHH', buf, 1)
        self.last_fcode = res[0]
        self.last_reg = res[1]
        self.last_len = res[2]
        self.err = 0
        return True

    def recv_resp(self, info_db, buf: bytearray, node_id: str) -> \
            Generator[tuple[str, bool], None, None]:
        # logging.info(f'recv_resp: first byte modbus:{buf[0]} len:{len(buf)}')
        if not self.check_crc(buf):
            logging.error('Modbus: CRC error')
            self.err = 1
            return
        if buf[0] != self.INV_ADDR:
            logging.info(f'Modbus: Wrong addr {buf[0]}')
            self.err = 2
            return
        if buf[1] != self.last_fcode:
            logging.info(f'Modbus: Wrong fcode {buf[1]} != {self.last_fcode}')
            self.err = 3
            return
        elmlen = buf[2] >> 1
        if elmlen != self.last_len:
            logging.info(f'Modbus: len error {elmlen} != {self.last_len}')
            self.err = 4
            return
        self.err = 0

        for i in range(0, elmlen):
            val = struct.unpack_from('>H', buf, 3+2*i)
            addr = self.last_reg+i
            # logging.info(f'Modbus: 0x{addr:04x}: {val[0]}')
            if addr in self.map:
                row = self.map[addr]
                info_id = row['reg']
                result = val[0]
                # fmt = row['fmt']
                # res = struct.unpack_from(fmt, buf, addr)
                # result = res[0]

                if 'eval' in row:
                    result = eval(row['eval'])
                if 'ratio' in row:
                    result = round(result * row['ratio'], 2)

                keys, level, unit, must_incr = info_db._key_obj(info_id)

                if keys:
                    name, update = info_db.update_db(keys, must_incr, result)
                    yield keys[0], update
                else:
                    name = str(f'info-id.0x{addr:x}')
                    update = False
                if update:
                    info_db.tracer.log(level,
                                       f'MODBUS[{node_id}]: {name} : {result}'
                                       f'{unit}')

    def check_crc(self, msg) -> bool:
        return 0 == self.__calc_crc(msg)

    def __calc_crc(self, buffer: bytes) -> int:
        crc = CRC_INIT

        for cur in buffer:
            crc = (crc >> 8) ^ self.__crc_tab[(crc ^ cur) & 0xFF]
        return crc

    def __build_crc_tab(self, poly) -> None:
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
