import logging
import struct

if __name__ == "app.src.gen3plus.solarman_v5":
    from app.src.messages import hex_dump_memory
    from app.src.config import Config
else:  # pragma: no cover
    from messages import hex_dump_memory
    from config import Config
# import traceback

logger = logging.getLogger('msg')


class SolarmanV5():

    def __init__(self, server_side: bool, id_str=b''):
        # self._registry.append(weakref.ref(self))
        self.server_side = server_side
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
        # self._send_buffer = bytearray(0)
        self._forward_buffer = bytearray(0)
        # self.db = Infos()
        # self.new_data = {}
        self.switch = {
            0x4110: self.msg_dev_ind,
        }
    '''
    Empty methods, that have to be implemented in any child class which
    don't use asyncio
    '''
    def _read(self) -> None:     # read data bytes from socket and copy them
        # to our _recv_buffer
        return  # pragma: no cover

    '''
    Our puplic methods
    '''
    def close(self) -> None:
        # we have refernces to methods of this class in self.switch
        # so we have to erase self.switch, otherwise this instance can't be
        # deallocated by the garbage collector ==> we get a memory leak
        self.switch.clear()

    def inc_counter(self, counter: str) -> None:
        # self.db.inc_counter(counter)
        # self.new_stat_data['proxy'] = True
        pass

    def dec_counter(self, counter: str) -> None:
        # self.db.dec_counter(counter)
        # self.new_stat_data['proxy'] = True
        pass

    def set_serial_no(self, serial_no: int):

        if self.unique_id == serial_no:
            logger.debug(f'SerialNo: {serial_no}')
        else:
            found = False
            inverters = Config.get('inverters')
            # logger.debug(f'Inverters: {inverters}')

            for key, inv in inverters.items():
                # logger.debug(f'key: {key} -> {inv}')
                if type(inv) is dict and inv['monitor_sn'] == serial_no:
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
        self._recv_buffer = self._recv_buffer[(self.header_len+self.data_len):]
        self.header_valid = False

    '''
    Message handler methods
    '''
    def msg_unknown(self):
        logger.warning(f"Unknow Msg: ID:{self.control}")
        # self.inc_counter('Unknown_Msg')
        # self.forward(self._recv_buffer, self.header_len+self.data_len)

    def msg_dev_ind(self):
        logger.warning(f"Msg: Device Indication ID:{self.control}")
        # self.inc_counter('Unknown_Msg')
        # self.forward(self._recv_buffer, self.header_len+self.data_len)
