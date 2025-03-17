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
    INV_ADDR = 1
    '''MODBUS server address of the TSUN inverter'''
    READ_REGS = 3
    '''MODBUS function code: Read Holding Register'''
    READ_INPUTS = 4
    '''MODBUS function code: Read Input Register'''
    WRITE_SINGLE_REG = 6
    '''Modbus function code: Write Single Register'''

    __crc_tab = []
    mb_reg_mapping = {
        0x0000: {'reg': Register.SERIAL_NUMBER,        'fmt': '!16s'},               # noqa: E501
        0x0008: {'reg': Register.BATT_PV1_VOLT,        'fmt': '!H', 'ratio': 0.01},  # noqa: E501, PV1 voltage
        0x0009: {'reg': Register.BATT_PV1_CUR,         'fmt': '!H', 'ratio': 0.01},  # noqa: E501, PV1 current
        0x000a: {'reg': Register.BATT_PV2_VOLT,        'fmt': '!H', 'ratio': 0.01},  # noqa: E501, PV2 voltage
        0x000b: {'reg': Register.BATT_PV2_CUR,         'fmt': '!H', 'ratio': 0.01},  # noqa: E501, PV2 current
        0x000c: {'reg': Register.BATT_38,              'fmt': '!h'},                 # noqa: E501
        0x000d: {'reg': Register.BATT_TOTAL_GEN,       'fmt': '!h', 'ratio': 0.01},  # noqa: E501
        0x000e: {'reg': Register.BATT_STATUS_1,        'fmt': '!h'},                 # noqa: E501
        0x000f: {'reg': Register.BATT_STATUS_2,        'fmt': '!h'},                 # noqa: E501
        0x0010: {'reg': Register.BATT_VOLT,            'fmt': '!h', 'ratio': 0.01},  # noqa: E501
        0x0011: {'reg': Register.BATT_CUR,             'fmt': '!h', 'ratio': 0.01},  # noqa: E501
        0x0012: {'reg': Register.BATT_SOC,             'fmt': '!H', 'ratio': 0.01},  # noqa: E501, state of charge (SOC) in percent
        0x0013: {'reg': Register.BATT_46,              'fmt': '!h'},                 # noqa: E501
        0x0014: {'reg': Register.BATT_48,              'fmt': '!h'},                 # noqa: E501
        0x0015: {'reg': Register.BATT_4a,              'fmt': '!h'},                 # noqa: E501
        0x0016: {'reg': Register.BATT_4c,              'fmt': '!h'},                 # noqa: E501
        0x0017: {'reg': Register.BATT_4e,              'fmt': '!h'},                 # noqa: E501
        0x0023: {'reg': Register.BATT_TEMP_1,          'fmt': '!h'},                 # noqa: E501
        0x0024: {'reg': Register.BATT_TEMP_2,          'fmt': '!h'},                 # noqa: E501
        0x0025: {'reg': Register.BATT_TEMP_3,          'fmt': '!h'},                 # noqa: E501
        0x0026: {'reg': Register.BATT_OUT_VOLT,        'fmt': '!h', 'ratio': 0.01},  # noqa: E501
        0x0027: {'reg': Register.BATT_OUT_CUR,         'fmt': '!h', 'ratio': 0.01},  # noqa: E501
        0x0028: {'reg': Register.BATT_OUT_STATUS,      'fmt': '!h'},                 # noqa: E501
        0x0029: {'reg': Register.BATT_TEMP_4,          'fmt': '!h'},                 # noqa: E501
        0x002a: {'reg': Register.BATT_74,              'fmt': '!h'},                 # noqa: E501
        0x002b: {'reg': Register.BATT_76,              'fmt': '!h'},                 # noqa: E501
        0x002c: {'reg': Register.BATT_78,              'fmt': '!h'},                 # noqa: E501

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

    def recv_resp(self, info_db, buf: bytes) -> \
            Generator[tuple[str, bool, int | float | str], None, None]:
        """Generator which check and parse a received MODBUS response.

        Keyword arguments:
            info_db: database for info lockups
            buf: received Modbus RTU response frame

        Returns on error and set Self.err to:
            1: CRC error
            2: Wrong server address
            3: Unexpected function code
            4: Unexpected data length
            5: No MODBUS request pending
        """
        # logging.info(f'recv_resp: first byte modbus:{buf[0]} len:{len(buf)}')

        fcode = buf[1]
        data_available = self.last_addr == self.INV_ADDR and \
            (fcode == 3 or fcode == 4)

        if self.__resp_error_check(buf, data_available):
            return

        if data_available:
            elmlen = buf[2] >> 1
            first_reg = self.last_reg  # save last_reg before sending next pdu
            self.__stop_timer()          # stop timer and send next pdu
            yield from self.__process_data(info_db, buf, first_reg, elmlen)
        else:
            self.__stop_timer()

        self.counter['retries'][f'{self.retry_cnt}'] += 1
        if self.rsp_handler:
            self.rsp_handler()
        self.__send_next_from_que()

    def __resp_error_check(self, buf: bytes, data_available: bool) -> bool:
        '''Check the MODBUS response for errors, returns True if one accure'''
        if not self.req_pend:
            self.err = 5
            return True
        if not self.__check_crc(buf):
            logger.error(f'[{self.node_id}] Modbus resp: CRC error')
            self.err = 1
            return True
        if buf[0] != self.last_addr:
            logger.info(f'[{self.node_id}] Modbus resp: Wrong addr {buf[0]}')
            self.err = 2
            return True
        fcode = buf[1]
        if fcode != self.last_fcode:
            logger.info(f'[{self.node_id}] Modbus: Wrong fcode {fcode}'
                        f' != {self.last_fcode}')
            self.err = 3
            return True
        if data_available:
            elmlen = buf[2] >> 1
            if elmlen != self.last_len:
                logger.info(f'[{self.node_id}] Modbus: len error {elmlen}'
                            f' != {self.last_len}')
                self.err = 4
                return True

        return False

    def __process_data(self, info_db, buf: bytes, first_reg, elmlen):
        '''Generator over received registers, updates the db'''
        for i in range(0, elmlen):
            addr = first_reg+i
            if addr in self.mb_reg_mapping:
                row = self.mb_reg_mapping[addr]
                info_id = row['reg']
                keys, level, unit, must_incr = info_db._key_obj(info_id)
                if keys:
                    result = Fmt.get_value(buf, 3+2*i, row)
                    name, update = info_db.update_db(keys, must_incr,
                                                     result)
                    yield keys[0], update, result
                    if update:
                        info_db.tracer.log(level,
                                           f'[{self.node_id}] MODBUS: {name}'
                                           f' : {result}{unit}')

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
    def __check_crc(self, msg: bytes) -> bool:
        '''Check CRC-16 and returns True if valid'''
        return 0 == self.__calc_crc(msg)

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
