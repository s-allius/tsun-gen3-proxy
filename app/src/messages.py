import struct
import logging
import time
from datetime import datetime
import weakref

if __name__ == "app.src.messages":
    from app.src.infos import Infos
    from app.src.config import Config
else:  # pragma: no cover
    from infos import Infos
    from config import Config

logger = logging.getLogger('msg')


def hex_dump_memory(level, info, data, num):
    n = 0
    lines = []
    lines.append(info)
    tracer = logging.getLogger('tracer')
    if not tracer.isEnabledFor(level):
        return

    for i in range(0, num, 16):
        line = '  '
        line += '%04x | ' % (i)
        n += 16

        for j in range(n-16, n):
            if j >= len(data):
                break
            line += '%02x ' % abs(data[j])

        line += ' ' * (3 * 16 + 9 - len(line)) + ' | '

        for j in range(n-16, n):
            if j >= len(data):
                break
            c = data[j] if not (data[j] < 0x20 or data[j] > 0x7e) else '.'
            line += '%c' % c

        lines.append(line)

    tracer.log(level, '\n'.join(lines))


class Control:
    def __init__(self, ctrl: int):
        self.ctrl = ctrl

    def __int__(self) -> int:
        return self.ctrl

    def is_ind(self) -> bool:
        return (self.ctrl == 0x91)

    def is_req(self) -> bool:
        return (self.ctrl == 0x70)

    def is_resp(self) -> bool:
        return (self.ctrl == 0x99)


class IterRegistry(type):
    def __iter__(cls):
        for ref in cls._registry:
            obj = ref()
            if obj is not None:
                yield obj


class Message(metaclass=IterRegistry):
    _registry = []
    new_stat_data = {}

    def __init__(self, server_side: bool, id_str=b''):
        self._registry.append(weakref.ref(self))
        self.server_side = server_side
        self.header_valid = False
        self.header_len = 0
        self.data_len = 0
        self.unique_id = 0
        self.node_id = ''
        self.sug_area = ''
        self.id_str = id_str
        self.contact_name = b''
        self.contact_mail = b''
        self._recv_buffer = b''
        self._send_buffer = bytearray(0)
        self._forward_buffer = bytearray(0)
        self.db = Infos()
        self.new_data = {}
        self.switch = {
            0x00: self.msg_contact_info,
            0x13: self.msg_ota_update,
            0x22: self.msg_get_time,
            0x71: self.msg_collector_data,
            0x04: self.msg_inverter_data,
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
        self.db.inc_counter(counter)
        self.new_stat_data['proxy'] = True

    def dec_counter(self, counter: str) -> None:
        self.db.dec_counter(counter)
        self.new_stat_data['proxy'] = True

    def set_serial_no(self, serial_no: str):

        if self.unique_id == serial_no:
            logger.debug(f'SerialNo: {serial_no}')
        else:
            inverters = Config.get('inverters')
            # logger.debug(f'Inverters: {inverters}')

            if serial_no in inverters:
                inv = inverters[serial_no]
                self.node_id = inv['node_id']
                self.sug_area = inv['suggested_area']
                logger.debug(f'SerialNo {serial_no} allowed! area:{self.sug_area}')  # noqa: E501
            else:
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
                                                            self.data_len):
            hex_dump_memory(logging.INFO, f'Received from {self.addr}:',
                            self._recv_buffer, self.header_len+self.data_len)

            self.set_serial_no(self.id_str.decode("utf-8"))
            self.__dispatch_msg()
            self.__flush_recv_msg()
        return

    def forward(self, buffer, buflen) -> None:
        tsun = Config.get('tsun')
        if tsun['enabled']:
            self._forward_buffer = buffer[:buflen]
            hex_dump_memory(logging.DEBUG, 'Store for forwarding:',
                            buffer, buflen)

            self.__parse_header(self._forward_buffer,
                                len(self._forward_buffer))
            fnc = self.switch.get(self.msg_id, self.msg_unknown)
            logger.info(self.__flow_str(self.server_side, 'forwrd') +
                        f' Ctl: {int(self.ctrl):#02x} Msg: {fnc.__name__!r}')
        return

    def _init_new_client_conn(self, contact_name, contact_mail) -> None:
        logger.info(f'name: {contact_name} mail: {contact_mail}')
        self.msg_id = 0
        self.__build_header(0x91)
        self._send_buffer += struct.pack(f'!{len(contact_name)+1}p'
                                         f'{len(contact_mail)+1}p',
                                         contact_name, contact_mail)

        self.__finish_send_msg()

    '''
    Our private methods
    '''
    def __flow_str(self, server_side: bool, type:
                   ('rx', 'tx', 'forwrd', 'drop')):  # noqa: F821
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

    def _timestamp(self):   # pragma: no cover
        if False:
            # utc as epoche
            ts = time.time()
        else:
            # convert localtime in epoche
            ts = (datetime.now() - datetime(1970, 1, 1)).total_seconds()
        return round(ts*1000)

    # check if there is a complete header in the buffer, parse it
    # and set
    #   self.header_len
    #   self.data_len
    #   self.id_str
    #   self.ctrl
    #   self.msg_id
    #
    # if the header is incomplete, than self.header_len is still 0
    #
    def __parse_header(self, buf: bytes, buf_len: int) -> None:

        if (buf_len < 5):      # enough bytes to read len and id_len?
            return
        result = struct.unpack_from('!lB', buf, 0)
        len = result[0]    # len of complete message
        id_len = result[1]    # len of variable id string

        hdr_len = 5+id_len+2

        if (buf_len < hdr_len):  # enough bytes for complete header?
            return

        result = struct.unpack_from(f'!{id_len+1}pBB', buf, 4)

        # store parsed header values in the class
        self.id_str = result[0]
        self.ctrl = Control(result[1])
        self.msg_id = result[2]
        self.data_len = len-id_len-3
        self.header_len = hdr_len
        self.header_valid = True
        return

    def __build_header(self, ctrl) -> None:
        self.send_msg_ofs = len(self._send_buffer)
        self._send_buffer += struct.pack(f'!l{len(self.id_str)+1}pBB',
                                         0, self.id_str, ctrl, self.msg_id)
        fnc = self.switch.get(self.msg_id, self.msg_unknown)
        logger.info(self.__flow_str(self.server_side, 'tx') +
                    f' Ctl: {int(ctrl):#02x} Msg: {fnc.__name__!r}')

    def __finish_send_msg(self) -> None:
        _len = len(self._send_buffer) - self.send_msg_ofs
        struct.pack_into('!l', self._send_buffer, self.send_msg_ofs, _len-4)

    def __dispatch_msg(self) -> None:
        fnc = self.switch.get(self.msg_id, self.msg_unknown)
        if self.unique_id:
            logger.info(self.__flow_str(self.server_side, 'rx') +
                        f' Ctl: {int(self.ctrl):#02x} Msg: {fnc.__name__!r}')
            fnc()
        else:
            logger.info(self.__flow_str(self.server_side, 'drop') +
                        f' Ctl: {int(self.ctrl):#02x} Msg: {fnc.__name__!r}')

    def __flush_recv_msg(self) -> None:
        self._recv_buffer = self._recv_buffer[(self.header_len+self.data_len):]
        self.header_valid = False

    '''
    Message handler methods
    '''
    def msg_contact_info(self):
        if self.ctrl.is_ind():
            self.__build_header(0x99)
            self._send_buffer += b'\x01'
            self.__finish_send_msg()
            self.__process_contact_info()
            # don't forward this contact info here, we will build one
            # when the remote connection is established
            return
        elif self.ctrl.is_resp():
            return  # ignore received response from tsun
        else:
            self.inc_counter('Unknown_Ctrl')
            self.forward(self._recv_buffer, self.header_len+self.data_len)

    def __process_contact_info(self):
        result = struct.unpack_from('!B', self._recv_buffer, self.header_len)
        name_len = result[0]

        result = struct.unpack_from(f'!{name_len+1}pB', self._recv_buffer,
                                    self.header_len)
        self.contact_name = result[0]
        mail_len = result[1]
        logger.info(f'name: {self.contact_name}')

        result = struct.unpack_from(f'!{mail_len+1}p', self._recv_buffer,
                                    self.header_len+name_len+1)
        self.contact_mail = result[0]
        logger.info(f'mail: {self.contact_mail}')

    def msg_get_time(self):
        tsun = Config.get('tsun')
        if tsun['enabled']:
            if self.ctrl.is_resp():
                ts = self._timestamp()
                result = struct.unpack_from('!q', self._recv_buffer,
                                            self.header_len)
                logger.debug(f'tsun-time: {result[0]:08x}'
                             f'  proxy-time: {ts:08x}')
            elif not self.ctrl.is_ind():
                self.inc_counter('Unknown_Ctrl')
            self.forward(self._recv_buffer, self.header_len+self.data_len)
        else:
            if self.ctrl.is_ind():
                ts = self._timestamp()
                logger.debug(f'time: {ts:08x}')

                self.__build_header(0x99)
                self._send_buffer += struct.pack('!q', ts)
                self.__finish_send_msg()

            elif self.ctrl.is_resp():
                result = struct.unpack_from('!q', self._recv_buffer,
                                            self.header_len)
                logger.debug(f'tsun-time: {result[0]:08x}')
            else:
                self.inc_counter('Unknown_Ctrl')

    def parse_msg_header(self):
        result = struct.unpack_from('!lB', self._recv_buffer, self.header_len)

        data_id = result[0]    # len of complete message
        id_len = result[1]     # len of variable id string
        logger.debug(f'Data_ID: {data_id}   id_len:  {id_len}')

        msg_hdr_len = 5+id_len+9

        result = struct.unpack_from(f'!{id_len+1}pBq', self._recv_buffer,
                                    self.header_len + 4)

        logger.debug(f'ID: {result[0]}  B: {result[1]}')
        logger.debug(f'time: {result[2]:08x}')
        # logger.info(f'time: {datetime.utcfromtimestamp(result[2]).strftime(
        # "%Y-%m-%d %H:%M:%S")}')
        return msg_hdr_len

    def msg_collector_data(self):
        if self.ctrl.is_ind():
            self.__build_header(0x99)
            self._send_buffer += b'\x01'
            self.__finish_send_msg()
            self.__process_data()

        elif self.ctrl.is_resp():
            return  # ignore received response
        else:
            self.inc_counter('Unknown_Ctrl')

        self.forward(self._recv_buffer, self.header_len+self.data_len)

    def msg_inverter_data(self):
        if self.ctrl.is_ind():
            self.__build_header(0x99)
            self._send_buffer += b'\x01'
            self.__finish_send_msg()
            self.__process_data()

        elif self.ctrl.is_resp():
            return  # ignore received response
        else:
            self.inc_counter('Unknown_Ctrl')

        self.forward(self._recv_buffer, self.header_len+self.data_len)

    def __process_data(self):
        msg_hdr_len = self.parse_msg_header()

        for key, update in self.db.parse(self._recv_buffer[self.header_len
                                                           + msg_hdr_len:]):
            if update:
                self.new_data[key] = True

    def msg_ota_update(self):
        if self.ctrl.is_req():
            pass
        elif self.ctrl.is_ind():
            pass
        else:
            self.inc_counter('Unknown_Ctrl')
        self.forward(self._recv_buffer, self.header_len+self.data_len)

    def msg_unknown(self):
        logger.warning(f"Unknow Msg: ID:{self.msg_id}")
        self.inc_counter('Unknown_Msg')
        self.forward(self._recv_buffer, self.header_len+self.data_len)
