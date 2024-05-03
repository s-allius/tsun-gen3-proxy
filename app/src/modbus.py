import struct

if __name__ == "app.src.modbus":
    from app.src.singleton import Singleton
else:  # pragma: no cover
    from singleton import Singleton

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


class Modbus(metaclass=Singleton):

    READ_REGS = 3
    READ_INPUTS = 4
    WRITE_SINGLE_REG = 6
    '''Modbus function codes'''

    __crc_tab = []

    def __init__(self):
        self.__build_crc_tab(CRC_POLY)

    def build_msg(self, addr, func, reg, val):
        msg = struct.pack('>BBHH', addr, func, reg, val)
        msg += struct.pack('<H', self.__calc_crc(msg))
        return msg

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
