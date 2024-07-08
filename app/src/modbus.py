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

if __name__ == "app.src.modbus":
    from app.src.infos import Register
else:  # pragma: no cover
    from infos import Register

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
    map = {
        0x2007: {'reg': Register.MAX_DESIGNED_POWER,   'fmt': '!H', 'ratio':  1},  # noqa: E501
        0x203e: {'reg': Register.NO_INPUTS,   'fmt': '!H', 'ratio':  1/256},  # noqa: E501

        0x3000: {'reg': Register.INVERTER_STATUS,      'fmt': '!H'},                 # noqa: E501
        0x3008: {'reg': Register.VERSION,              'fmt': '!H', 'eval': "f'V{(result>>12)}.{(result>>8)&0xf}.{(result>>4)&0xf}{result&0xf}'"},  # noqa: E501
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
        0x301d: {'reg': Register.TOTAL_GENERATION,     'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x301f: {'reg': Register.PV1_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x3020: {'reg': Register.PV1_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x3022: {'reg': Register.PV2_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x3023: {'reg': Register.PV2_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x3025: {'reg': Register.PV3_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x3026: {'reg': Register.PV3_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x3028: {'reg': Register.PV4_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x3029: {'reg': Register.PV4_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
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

    def close(self):
        """free the queue and erase the callback handlers"""
        logging.debug('Modbus close:')
        self.__stop_timer()
        self.rsp_handler = None
        self.snd_handler = None
        while not self.que.empty:
            self.que.get_nowait()

    def __del__(self):
        """log statistics on the deleting of a MODBUS instance"""
        logging.debug(f'Modbus __del__:\n {self.counter}')

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

    def recv_req(self, buf: bytearray,
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

    def recv_resp(self, info_db, buf: bytearray, node_id: str) -> \
            Generator[tuple[str, bool, int | float | str], None, None]:
        """Generator which check and parse a received MODBUS response.

        Keyword arguments:
            info_db: database for info lockups
            buf: received Modbus RTU response frame
            node_id: string for logging which identifies the slave

        Returns on error and set Self.err to:
            1: CRC error
            2: Wrong server address
            3: Unexpected function code
            4: Unexpected data length
            5: No MODBUS request pending
        """
        # logging.info(f'recv_resp: first byte modbus:{buf[0]} len:{len(buf)}')
        if not self.req_pend:
            self.err = 5
            return
        if not self.__check_crc(buf):
            logger.error(f'[{node_id}] Modbus resp: CRC error')
            self.err = 1
            return
        if buf[0] != self.last_addr:
            logger.info(f'[{node_id}] Modbus resp: Wrong addr {buf[0]}')
            self.err = 2
            return
        fcode = buf[1]
        if fcode != self.last_fcode:
            logger.info(f'[{node_id}] Modbus: Wrong fcode {fcode}'
                        f' != {self.last_fcode}')
            self.err = 3
            return
        if self.last_addr == self.INV_ADDR and \
                (fcode == 3 or fcode == 4):
            elmlen = buf[2] >> 1
            if elmlen != self.last_len:
                logger.info(f'[{node_id}] Modbus: len error {elmlen}'
                            f' != {self.last_len}')
                self.err = 4
                return
            first_reg = self.last_reg  # save last_reg before sending next pdu
            self.__stop_timer()          # stop timer and send next pdu

            for i in range(0, elmlen):
                addr = first_reg+i
                if addr in self.map:
                    row = self.map[addr]
                    info_id = row['reg']
                    fmt = row['fmt']
                    val = struct.unpack_from(fmt, buf, 3+2*i)
                    result = val[0]

                    if 'eval' in row:
                        result = eval(row['eval'])
                    if 'ratio' in row:
                        result = round(result * row['ratio'], 2)

                    keys, level, unit, must_incr = info_db._key_obj(info_id)

                    if keys:
                        name, update = info_db.update_db(keys, must_incr,
                                                         result)
                        yield keys[0], update, result
                        if update:
                            info_db.tracer.log(level,
                                               f'[{node_id}] MODBUS: {name}'
                                               f' : {result}{unit}')
        else:
            self.__stop_timer()

        self.counter['retries'][f'{self.retry_cnt}'] += 1
        if self.rsp_handler:
            self.rsp_handler()
        self.__send_next_from_que()

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
            logger.info(f'Modbus timeout {self}')
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
    def __check_crc(self, msg: bytearray) -> bool:
        '''Check CRC-16 and returns True if valid'''
        return 0 == self.__calc_crc(msg)

    def __calc_crc(self, buffer: bytearray) -> int:
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
