import struct
import logging

if __name__ == "app.src.gen3plus.solarman_v5":
    from app.src.messages import hex_dump_memory, Message
    from app.src.infos import Infos
    from app.src.config import Config
else:  # pragma: no cover
    from messages import hex_dump_memory, Message
    from infos import Infos
    from config import Config
# import traceback

logger = logging.getLogger('msg')


class SolarmanV5(Message):

    def __init__(self, server_side: bool):
        super().__init__(server_side)

        self.header_valid = False
        self.header_len = 11
        self.data_len = 0
        self.control = 0
        self.serial = 0
        self.snr = 0
        self.unique_id = 0
        self.node_id = ''
        self.sug_area = ''
        # self.await_conn_resp_cnt = 0
        # self.id_str = id_str
        self._recv_buffer = bytearray(0)
        self._send_buffer = bytearray(0)
        self._forward_buffer = bytearray(0)
        self.db = Infos()
        self.new_data = {}
        self.switch = {
            0x4110: self.msg_dev_ind,  # hello
            0x4210: self.msg_unknown,  # data
            0x4310: self.msg_unknown,
            0x4710: self.msg_unknown,  # heatbeat
            0x4810: self.msg_unknown,  # hello end
        }

    '''
    Our puplic methods
    '''
    def close(self) -> None:
        # we have refernces to methods of this class in self.switch
        # so we have to erase self.switch, otherwise this instance can't be
        # deallocated by the garbage collector ==> we get a memory leak
        self.switch.clear()

    def inc_counter(self, counter: str) -> None:
        self.db.inc_counter(counter)
        Infos.new_stat_data['proxy'] = True
        pass

    def dec_counter(self, counter: str) -> None:
        self.db.dec_counter(counter)
        Infos.new_stat_data['proxy'] = True
        pass

    def set_serial_no(self, snr: int):
        serial_no = str(snr)
        if self.unique_id == serial_no:
            logger.debug(f'SerialNo: {serial_no}')
        else:
            found = False
            inverters = Config.get('inverters')
            # logger.debug(f'Inverters: {inverters}')

            for key, inv in inverters.items():
                # logger.debug(f'key: {key} -> {inv}')
                if (type(inv) is dict and 'monitor_sn' in inv
                   and inv['monitor_sn'] == snr):
                    found = True
                    self.node_id = inv['node_id']
                    self.sug_area = inv['suggested_area']
                    logger.debug(f'SerialNo {serial_no} allowed! area:{self.sug_area}')  # noqa: E501

            if not found:
                self.node_id = ''
                self.sug_area = ''
                if 'allow_all' not in inverters or not inverters['allow_all']:
                    self.inc_counter('Unknown_SNR')
                    self.unique_id = None
                    logger.warning(f'ignore message from unknow inverter! (SerialNo: {serial_no})')  # noqa: E501
                    return
                logger.debug(f'SerialNo {serial_no} not known but accepted!')

            self.unique_id = serial_no

    def read(self) -> None:
        self._read()

        if not self.header_valid:
            self.__parse_header(self._recv_buffer, len(self._recv_buffer))

        if self.header_valid and len(self._recv_buffer) >= (self.header_len +
                                                            self.data_len+2):
            hex_dump_memory(logging.INFO, f'Received from {self.addr}:',
                            self._recv_buffer, self.header_len+self.data_len+2)
            if self.__trailer_is_ok(self._recv_buffer, self.header_len
                                    + self.data_len + 2):
                self.set_serial_no(self.snr)
                self.__dispatch_msg()
            self.__flush_recv_msg()
        return

    '''
    Our private methods
    '''
    def __flow_str(self, server_side: bool, type: str):  # noqa: F821
        switch = {
            'rx':      '  <',
            'tx':      '  >',
            'forwrd':  '<< ',
            'drop':    ' xx',
            'rxS':     '>  ',
            'txS':     '<  ',
            'forwrdS': ' >>',
            'dropS':   'xx ',
        }
        if server_side:
            type += 'S'
        return switch.get(type, '???')

    def __parse_header(self, buf: bytes, buf_len: int) -> None:

        if (buf_len < self.header_len):  # enough bytes for complete header?
            return

        result = struct.unpack_from('<BHHHL', buf, 0)

        # store parsed header values in the class
        start = result[0]    # len of complete message
        self.data_len = result[1]    # len of variable id string
        self.control = result[2]
        self.serial = result[3]
        self.snr = result[4]

        if start != 0xA5:
            return
        self.header_valid = True
        return

    def __trailer_is_ok(self, buf: bytes, buf_len: int) -> bool:
        crc = buf[self.data_len+11]
        stop = buf[self.data_len+12]
        if stop != 0x15:
            return False
        check = sum(buf[1:buf_len-2]) & 0xff
        if check != crc:
            logger.debug(f'CRC {int(crc):#02x} {int(check):#08x}'
                         f' Stop:{int(stop):#02x}')
            return False

        return True

    def parse_header(self, buf: bytes, buf_len: int) -> None:

        if (buf_len < self.header_len):      # header complete?
            return

        result = struct.unpack_from('<BHHHL', buf, 0)

        start = result[0]    # len of complete message
        self.data_len = result[1]    # len of variable id string
        self.control = result[2]
        self.serial = result[3]
        self.snr = result[4]
        if start != 0xA5:
            return
        if (buf_len < 13 + self.data_len):
            return

        self.crc = buf[self.data_len+11]
        self.stop = buf[self.data_len+12]

        yield self.control, buf[11:11+self.data_len]

    def __dispatch_msg(self) -> None:
        fnc = self.switch.get(self.control, self.msg_unknown)
        if self.unique_id:
            logger.info(self.__flow_str(self.server_side, 'rx') +
                        f' Ctl: {int(self.control):#04x}' +
                        f' Msg: {fnc.__name__!r}')
            fnc()
        else:
            logger.info(self.__flow_str(self.server_side, 'drop') +
                        f' Ctl: {int(self.control):#04x}' +
                        f' Msg: {fnc.__name__!r}')

    def __flush_recv_msg(self) -> None:
        self._recv_buffer = self._recv_buffer[(self.header_len +
                                               self.data_len+2):]
        self.header_valid = False
    '''
    def modbus(self, data):
        POLY = 0xA001

        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = ((crc >> 1) ^ POLY
                if (crc & 0x0001)
                else crc >> 1)
        return crc

    def validate_modbus_crc(self, frame):
        # Calculate crc with all but the last 2 bytes of
        # the frame (they contain the crc)
        calc_crc = 0xFFFF
        for pos in frame[:-2]:
            calc_crc ^= pos
            for i in range(8):
                if (calc_crc & 1) != 0:
                    calc_crc >>= 1
                    calc_crc ^= 0xA001  # bitwise 'or' with modbus magic
                                        # number (0xa001 == bitwise
                                        # reverse of 0x8005)
                else:
                    calc_crc >>= 1

        # Compare calculated crc with the one supplied in the frame....
        frame_crc, = struct.unpack('<H', frame[-2:])
        if calc_crc == frame_crc:
            return 1
        else:
            return 0
    '''
    '''
    Message handler methods
    '''
    def msg_unknown(self):
        logger.warning(f"Unknow Msg: ID:{self.control}")
        self.inc_counter('Unknown_Msg')
        self.forward(self._recv_buffer, self.header_len+self.data_len)

    def msg_dev_ind(self):
        data = self._recv_buffer[self.header_len:]
        result = struct.unpack_from('<BLLL', data, 0)
        code = result[0]  # always 2
        total = result[1]
        tim = result[2]
        res = result[3]  # always zero
        logger.info(f'code:{code} total:{total}s'
                    f' timer:{tim}s  null:{res}')
        if (code == 2):
            result = struct.unpack_from('<BBBBBB40s', data, 13)
            upload_period = result[0]
            data_acq_period = result[1]
            heart_beat = result[2]
            res = result[3]
            wifi = result[4]
            ver = result[6]
            # res2 = result[5]
            logger.info(f'upload:{upload_period}min '
                        f'data collect:{data_acq_period}s '
                        f'heartbeat:{heart_beat}s '
                        f'wifi:{wifi}%')
            logger.info(f'ver:{ver}')

        # self.forward(self._recv_buffer, self.header_len+self.data_len)
