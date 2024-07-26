import struct
import logging
import time
from datetime import datetime

if __name__ == "app.src.gen3.talent":
    from app.src.messages import hex_dump_memory, Message, State
    from app.src.modbus import Modbus
    from app.src.my_timer import Timer
    from app.src.config import Config
    from app.src.gen3.infos_g3 import InfosG3
    from app.src.infos import Register
else:  # pragma: no cover
    from messages import hex_dump_memory, Message, State
    from modbus import Modbus
    from my_timer import Timer
    from config import Config
    from gen3.infos_g3 import InfosG3
    from infos import Register

logger = logging.getLogger('msg')


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


class Talent(Message):
    MB_START_TIMEOUT = 40
    MB_REGULAR_TIMEOUT = 60

    def __init__(self, server_side: bool, id_str=b''):
        super().__init__(server_side, self.send_modbus_cb, mb_timeout=11)
        self.await_conn_resp_cnt = 0
        self.id_str = id_str
        self.contact_name = b''
        self.contact_mail = b''
        self.ts_offset = 0        # time offset between tsun cloud and local
        self.db = InfosG3()
        self.switch = {
            0x00: self.msg_contact_info,
            0x13: self.msg_ota_update,
            0x22: self.msg_get_time,
            0x71: self.msg_collector_data,
            # 0x76:
            0x77: self.msg_modbus,
            # 0x78:
            0x04: self.msg_inverter_data,
        }
        self.log_lvl = {
            0x00: logging.INFO,
            0x13: logging.INFO,
            0x22: logging.INFO,
            0x71: logging.INFO,
            # 0x76:
            0x77: self.get_modbus_log_lvl,
            # 0x78:
            0x04: logging.INFO,
        }
        self.modbus_elms = 0    # for unit tests
        self.node_id = 'G3'     # will be overwritten in __set_serial_no
        self.mb_timer = Timer(self.mb_timout_cb, self.node_id)
        self.modbus_polling = False

    '''
    Our puplic methods
    '''
    def close(self) -> None:
        logging.debug('Talent.close()')
        if self.server_side:
            # set inverter state to offline, if output power is very low
            logging.debug('close power: '
                          f'{self.db.get_db_value(Register.OUTPUT_POWER, -1)}')
            if self.db.get_db_value(Register.OUTPUT_POWER, 999) < 2:
                self.db.set_db_def_value(Register.INVERTER_STATUS, 0)
                self.new_data['env'] = True

        # we have references to methods of this class in self.switch
        # so we have to erase self.switch, otherwise this instance can't be
        # deallocated by the garbage collector ==> we get a memory leak
        self.switch.clear()
        self.log_lvl.clear()
        self.state = State.closed
        self.mb_timer.close()
        super().close()

    def __set_serial_no(self, serial_no: str):

        if self.unique_id == serial_no:
            logger.debug(f'SerialNo: {serial_no}')
        else:
            inverters = Config.get('inverters')
            # logger.debug(f'Inverters: {inverters}')

            if serial_no in inverters:
                inv = inverters[serial_no]
                self.node_id = inv['node_id']
                self.sug_area = inv['suggested_area']
                self.modbus_polling = inv['modbus_polling']
                logger.debug(f'SerialNo {serial_no} allowed! area:{self.sug_area}')  # noqa: E501
                self.db.set_pv_module_details(inv)
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

    def read(self) -> float:
        self._read()

        if not self.header_valid:
            self.__parse_header(self._recv_buffer, len(self._recv_buffer))

        if self.header_valid and len(self._recv_buffer) >= (self.header_len +
                                                            self.data_len):
            if self.state == State.init:
                self.state = State.received     # received 1st package

            log_lvl = self.log_lvl.get(self.msg_id, logging.WARNING)
            if callable(log_lvl):
                log_lvl = log_lvl()

            hex_dump_memory(log_lvl, f'Received from {self.addr}:',
                            self._recv_buffer, self.header_len+self.data_len)

            self.__set_serial_no(self.id_str.decode("utf-8"))
            self.__dispatch_msg()
            self.__flush_recv_msg()
        return 0.5  # wait 500ms before sending a response

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

    def send_modbus_cb(self, modbus_pdu: bytearray, log_lvl: int, state: str):
        if self.state != State.up:
            logger.warning(f'[{self.node_id}] ignore MODBUS cmd,'
                           ' cause the state is not UP anymore')
            return

        self.__build_header(0x70, 0x77)
        self._send_buffer += b'\x00\x01\xa3\x28'   # fixme
        self._send_buffer += struct.pack('!B', len(modbus_pdu))
        self._send_buffer += modbus_pdu
        self.__finish_send_msg()

        hex_dump_memory(log_lvl, f'Send Modbus {state}:{self.addr}:',
                        self._send_buffer, len(self._send_buffer))
        self.writer.write(self._send_buffer)
        self._send_buffer = bytearray(0)  # self._send_buffer[sent:]

    def _send_modbus_cmd(self, func, addr, val, log_lvl) -> None:
        if self.state != State.up:
            logger.log(log_lvl, f'[{self.node_id}] ignore MODBUS cmd,'
                       ' as the state is not UP')
            return
        self.mb.build_msg(Modbus.INV_ADDR, func, addr, val, log_lvl)

    async def send_modbus_cmd(self, func, addr, val, log_lvl) -> None:
        self._send_modbus_cmd(func, addr, val, log_lvl)

    def mb_timout_cb(self, exp_cnt):
        self.mb_timer.start(self.MB_REGULAR_TIMEOUT)

        if 2 == (exp_cnt % 30):
            # logging.info("Regular Modbus Status request")
            self._send_modbus_cmd(Modbus.READ_REGS, 0x2000, 96, logging.DEBUG)
        else:
            self._send_modbus_cmd(Modbus.READ_REGS, 0x3000, 48, logging.DEBUG)

    def _init_new_client_conn(self) -> bool:
        contact_name = self.contact_name
        contact_mail = self.contact_mail
        logger.info(f'name: {contact_name} mail: {contact_mail}')
        self.msg_id = 0
        self.await_conn_resp_cnt += 1
        self.__build_header(0x91)
        self._send_buffer += struct.pack(f'!{len(contact_name)+1}p'
                                         f'{len(contact_mail)+1}p',
                                         contact_name, contact_mail)

        self.__finish_send_msg()
        return True

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

    def _timestamp(self):   # pragma: no cover
        if False:
            # utc as epoche
            ts = time.time()
        else:
            # convert localtime in epoche
            ts = (datetime.now() - datetime(1970, 1, 1)).total_seconds()
        return round(ts*1000)

    def _update_header(self, _forward_buffer):
        '''update header for message before forwarding,
        add time offset to timestamp'''
        _len = len(_forward_buffer)
        result = struct.unpack_from('!lB', _forward_buffer, 0)
        id_len = result[1]    # len of variable id string
        if _len < 2*id_len + 21:
            return

        result = struct.unpack_from('!B', _forward_buffer, id_len+6)
        msg_code = result[0]
        if msg_code == 0x71 or msg_code == 0x04:
            result = struct.unpack_from('!q', _forward_buffer, 13+2*id_len)
            ts = result[0] + self.ts_offset
            logger.debug(f'offset: {self.ts_offset:08x}'
                         f'  proxy-time: {ts:08x}')
            struct.pack_into('!q', _forward_buffer, 13+2*id_len, ts)

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

    def __build_header(self, ctrl, msg_id=None) -> None:
        if not msg_id:
            msg_id = self.msg_id
        self.send_msg_ofs = len(self._send_buffer)
        self._send_buffer += struct.pack(f'!l{len(self.id_str)+1}pBB',
                                         0, self.id_str, ctrl, msg_id)
        fnc = self.switch.get(msg_id, self.msg_unknown)
        logger.info(self.__flow_str(self.server_side, 'tx') +
                    f' Ctl: {int(ctrl):#02x} Msg: {fnc.__name__!r}')

    def __finish_send_msg(self) -> None:
        _len = len(self._send_buffer) - self.send_msg_ofs
        struct.pack_into('!l', self._send_buffer, self.send_msg_ofs, _len-4)

    def __dispatch_msg(self) -> None:
        fnc = self.switch.get(self.msg_id, self.msg_unknown)
        if self.unique_id:
            logger.info(self.__flow_str(self.server_side, 'rx') +
                        f' Ctl: {int(self.ctrl):#02x} ({self.state}) '
                        f'Msg: {fnc.__name__!r}')
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
            if self.server_side and self.__process_contact_info():
                self.__build_header(0x91)
                self._send_buffer += b'\x01'
                self.__finish_send_msg()
            # don't forward this contact info here, we will build one
            # when the remote connection is established
            elif self.await_conn_resp_cnt > 0:
                self.await_conn_resp_cnt -= 1
            else:
                self.forward(self._recv_buffer, self.header_len+self.data_len)
            return
        else:
            logger.warning('Unknown Ctrl')
            self.inc_counter('Unknown_Ctrl')
            self.forward(self._recv_buffer, self.header_len+self.data_len)

    def __process_contact_info(self) -> bool:
        result = struct.unpack_from('!B', self._recv_buffer, self.header_len)
        name_len = result[0]
        if self.data_len < name_len+2:
            return False
        result = struct.unpack_from(f'!{name_len+1}pB', self._recv_buffer,
                                    self.header_len)
        self.contact_name = result[0]
        mail_len = result[1]
        logger.info(f'name: {self.contact_name}')

        result = struct.unpack_from(f'!{mail_len+1}p', self._recv_buffer,
                                    self.header_len+name_len+1)
        self.contact_mail = result[0]
        logger.info(f'mail: {self.contact_mail}')
        return True

    def msg_get_time(self):
        if self.ctrl.is_ind():
            if self.data_len == 0:
                self.state = State.pend     # block MODBUS cmds
                if (self.modbus_polling):
                    self.mb_timer.start(self.MB_START_TIMEOUT)
                    self.db.set_db_def_value(Register.POLLING_INTERVAL,
                                             self.MB_REGULAR_TIMEOUT)

                ts = self._timestamp()
                logger.debug(f'time: {ts:08x}')
                self.__build_header(0x91)
                self._send_buffer += struct.pack('!q', ts)
                self.__finish_send_msg()

            elif self.data_len >= 8:
                ts = self._timestamp()
                result = struct.unpack_from('!q', self._recv_buffer,
                                            self.header_len)
                self.ts_offset = result[0]-ts
                logger.debug(f'tsun-time: {int(result[0]):08x}'
                             f'  proxy-time: {ts:08x}'
                             f'  offset: {self.ts_offset}')
                return  # ignore received response
        else:
            logger.warning('Unknown Ctrl')
            self.inc_counter('Unknown_Ctrl')

        self.forward(self._recv_buffer, self.header_len+self.data_len)

    def parse_msg_header(self):
        result = struct.unpack_from('!lB', self._recv_buffer, self.header_len)

        data_id = result[0]    # len of complete message
        id_len = result[1]     # len of variable id string
        logger.debug(f'Data_ID: 0x{data_id:08x}   id_len:  {id_len}')

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
            logger.warning('Unknown Ctrl')
            self.inc_counter('Unknown_Ctrl')

        self.forward(self._recv_buffer, self.header_len+self.data_len)

    def msg_inverter_data(self):
        if self.ctrl.is_ind():
            self.__build_header(0x99)
            self._send_buffer += b'\x01'
            self.__finish_send_msg()
            self.__process_data()
            self.state = State.up  # allow MODBUS cmds

        elif self.ctrl.is_resp():
            return  # ignore received response
        else:
            logger.warning('Unknown Ctrl')
            self.inc_counter('Unknown_Ctrl')

        self.forward(self._recv_buffer, self.header_len+self.data_len)

    def __process_data(self):
        msg_hdr_len = self.parse_msg_header()

        for key, update in self.db.parse(self._recv_buffer, self.header_len
                                         + msg_hdr_len, self.node_id):
            if update:
                self.new_data[key] = True

    def msg_ota_update(self):
        if self.ctrl.is_req():
            self.inc_counter('OTA_Start_Msg')
        elif self.ctrl.is_ind():
            pass
        else:
            logger.warning('Unknown Ctrl')
            self.inc_counter('Unknown_Ctrl')
        self.forward(self._recv_buffer, self.header_len+self.data_len)

    def parse_modbus_header(self):

        msg_hdr_len = 5

        result = struct.unpack_from('!lBB', self._recv_buffer,
                                    self.header_len)
        modbus_len = result[1]
        # logger.debug(f'Ref: {result[0]}')
        # logger.debug(f'Modbus MsgLen: {modbus_len} Func:{result[2]}')
        return msg_hdr_len, modbus_len

    def get_modbus_log_lvl(self) -> int:
        if self.ctrl.is_req():
            return logging.INFO
        elif self.ctrl.is_ind():
            if self.server_side:
                return self.mb.last_log_lvl
        return logging.WARNING

    def msg_modbus(self):
        hdr_len, modbus_len = self.parse_modbus_header()
        data = self._recv_buffer[self.header_len:
                                 self.header_len+self.data_len]

        if self.ctrl.is_req():
            if self.remoteStream.mb.recv_req(data[hdr_len:],
                                             self.remoteStream.
                                             msg_forward):
                self.inc_counter('Modbus_Command')
            else:
                self.inc_counter('Invalid_Msg_Format')
        elif self.ctrl.is_ind():
            self.modbus_elms = 0
            # logger.debug(f'Modbus Ind  MsgLen: {modbus_len}')
            if not self.server_side:
                logger.warning('Unknown Message')
                self.inc_counter('Unknown_Msg')
                return

            for key, update, _ in self.mb.recv_resp(self.db, data[
                    hdr_len:],
                    self.node_id):
                if update:
                    self.new_data[key] = True
                self.modbus_elms += 1          # count for unit tests
        else:
            logger.warning('Unknown Ctrl')
            self.inc_counter('Unknown_Ctrl')
            self.forward(self._recv_buffer, self.header_len+self.data_len)

    def msg_forward(self):
        self.forward(self._recv_buffer, self.header_len+self.data_len)

    def msg_unknown(self):
        logger.warning(f"Unknow Msg: ID:{self.msg_id}")
        self.inc_counter('Unknown_Msg')
        self.forward(self._recv_buffer, self.header_len+self.data_len)
