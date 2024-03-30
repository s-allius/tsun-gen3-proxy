import struct
import logging
# import time
from datetime import datetime

if __name__ == "app.src.gen3plus.solarman_v5":
    from app.src.messages import hex_dump_memory, Message
    from app.src.config import Config
    from app.src.gen3plus.infos_g3p import InfosG3P
else:  # pragma: no cover
    from messages import hex_dump_memory, Message
    from config import Config
    from gen3plus.infos_g3p import InfosG3P
# import traceback

logger = logging.getLogger('msg')


class SolarmanV5(Message):

    def __init__(self, server_side: bool):
        super().__init__(server_side)

        self.header_len = 11  # overwrite construcor in class Message
        self.control = 0
        self.serial = 0
        self.snr = 0
        # self.await_conn_resp_cnt = 0
        # self.id_str = id_str
        self.db = InfosG3P()
        self.switch = {
            0x4110: self.msg_dev_ind,    # hello
            0x1110: self.msg_dev_rsp,
            0x4210: self.msg_data_ind,   # data every 5 minutes
            0x1210: self.msg_data_rsp,
            0x4310: self.msg_unknown,    # regulary after 3-6 hours
            0x4710: self.msg_hbeat_ind,  # heatbeat
            0x1710: self.msg_hbeat_rsp,  # every 2 minutes
            0x4810: self.msg_unknown,    # hello end
        }

    '''
    Our puplic methods
    '''
    def close(self) -> None:
        logging.debug('Solarman.close()')
        # we have refernces to methods of this class in self.switch
        # so we have to erase self.switch, otherwise this instance can't be
        # deallocated by the garbage collector ==> we get a memory leak
        self.switch.clear()

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

    def forward(self, buffer, buflen) -> None:
        tsun = Config.get('solarman')
        if tsun['enabled']:
            self._forward_buffer = buffer[:buflen]
            hex_dump_memory(logging.DEBUG, 'Store for forwarding:',
                            buffer, buflen)

            self.__parse_header(self._forward_buffer,
                                len(self._forward_buffer))
            fnc = self.switch.get(self.control, self.msg_unknown)
            logger.info(self.__flow_str(self.server_side, 'forwrd') +
                        f' Ctl: {int(self.control):#04x}'
                        f' Msg: {fnc.__name__!r}')
        return

    def _init_new_client_conn(self) -> bool:
        # self.__build_header(0x91)
        # self._send_buffer += struct.pack(f'!{len(contact_name)+1}p'
        #                                  f'{len(contact_mail)+1}p',
        #                                  contact_name, contact_mail)

        # self.__finish_send_msg()
        return False

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
        logger.warning(f"Unknow Msg: ID:{int(self.control):#04x}")
        self.inc_counter('Unknown_Msg')
        self.forward(self._recv_buffer, self.header_len+self.data_len+2)

    def msg_dev_ind(self):
        data = self._recv_buffer[self.header_len:]
        result = struct.unpack_from('<BLLL', data, 0)
        ftype = result[0]  # always 2
        total = result[1]
        tim = result[2]
        res = result[3]  # always zero
        logger.info(f'frame type:{ftype:02x} total:{total}s'
                    f' timer:{tim:08x}s  null:{res}')
        dt = datetime.fromtimestamp(total)
        logger.info(f'ts: {dt.strftime("%Y-%m-%d %H:%M:%S")}')

        self.__process_data(ftype)
        self.forward(self._recv_buffer, self.header_len+self.data_len+2)

    def msg_dev_rsp(self):
        self.msg_response()

    def msg_data_ind(self):
        data = self._recv_buffer
        result = struct.unpack_from('<BLLLLL', data, self.header_len)
        ftype = result[0]  # 1 or 0x81
        total = result[1]
        tim = result[2]
        offset = result[3]
        unkn = result[4]
        cnt = result[5]
        logger.info(f'ftype:{ftype:02x} total:{total}s'
                    f' timer:{tim:08x}s  ofs:{offset}'
                    f' ??: {unkn:08x} cnt:{cnt}')
        dt = datetime.fromtimestamp(total)
        logger.info(f'ts: {dt.strftime("%Y-%m-%d %H:%M:%S")}')

        self.__process_data(ftype & 0x7f)
        self.forward(self._recv_buffer, self.header_len+self.data_len+2)

    def __process_data(self, ftype):
        msg_type = self.control >> 8
        for key, update in self.db.parse(self._recv_buffer, msg_type, ftype):
            if update:
                self.new_data[key] = True

    def msg_data_rsp(self):
        self.msg_response()

    def msg_hbeat_ind(self):
        data = self._recv_buffer[self.header_len:]
        result = struct.unpack_from('<B', data, 0)
        ftype = result[0]  # always 0
        if ftype != 0:
            logger.info(f'hb frame_type:{ftype}')

        self.forward(self._recv_buffer, self.header_len+self.data_len+2)

    def msg_hbeat_rsp(self):
        self.msg_response()

    def msg_response(self):
        data = self._recv_buffer[self.header_len:]
        result = struct.unpack_from('<BBLL', data, 0)
        ftype = result[0]  # always 2
        valid = result[1] == 1  # status
        ts = result[2]
        repeat = result[3]  # always 60
        logger.info(f'ftype:{ftype} accepted:{valid}'
                    f' ts:{ts:08x}  repeat:{repeat}s')

        dt = datetime.fromtimestamp(ts)
        logger.info(f'ts: {dt.strftime("%Y-%m-%d %H:%M:%S")}')
        self.forward(self._recv_buffer, self.header_len+self.data_len+2)
