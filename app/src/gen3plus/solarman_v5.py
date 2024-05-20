import struct
# import json
import logging
import time
from datetime import datetime

if __name__ == "app.src.gen3plus.solarman_v5":
    from app.src.messages import hex_dump_memory, Message
    from app.src.modbus import Modbus
    from app.src.config import Config
    from app.src.gen3plus.infos_g3p import InfosG3P
    from app.src.infos import Register
else:  # pragma: no cover
    from messages import hex_dump_memory, Message
    from config import Config
    from modbus import Modbus
    from gen3plus.infos_g3p import InfosG3P
    from infos import Register
# import traceback

logger = logging.getLogger('msg')


class Sequence():
    def __init__(self, server_side: bool):
        self.rcv_idx = 0
        self.snd_idx = 0
        self.server_side = server_side

    def set_recv(self, val: int):
        if self.server_side:
            self.rcv_idx = val >> 8
            self.snd_idx = val & 0xff
        else:
            self.rcv_idx = val & 0xff
            self.snd_idx = val >> 8

    def get_send(self):
        self.snd_idx += 1
        self.snd_idx &= 0xff
        if self.server_side:
            return (self.rcv_idx << 8) | self.snd_idx
        else:
            return (self.snd_idx << 8) | self.rcv_idx

    def __str__(self):
        return f'{self.rcv_idx:02x}:{self.snd_idx:02x}'


class SolarmanV5(Message):
    AT_CMD = 1
    MB_RTU_CMD = 2

    def __init__(self, server_side: bool):
        super().__init__(server_side, self.send_modbus_cb, 5)

        self.header_len = 11  # overwrite construcor in class Message
        self.control = 0
        self.seq = Sequence(server_side)
        self.snr = 0
        self.db = InfosG3P()
        self.time_ofs = 0
        self.forward_at_cmd_resp = False
        self.switch = {

            0x4210: self.msg_data_ind,   # real time data
            0x1210: self.msg_response,   # at least every 5 minutes

            0x4710: self.msg_hbeat_ind,  # heatbeat
            0x1710: self.msg_response,   # every 2 minutes

            # every 3 hours comes a sync seuqence:
            # 00:00:00  0x4110   device data     ftype: 0x02
            # 00:00:02  0x4210   real time data  ftype: 0x01
            # 00:00:03  0x4210   real time data  ftype: 0x81
            # 00:00:05  0x4310   wifi data       ftype: 0x81    sub-id 0x0018: 0c   # noqa: E501
            # 00:00:06  0x4310   wifi data       ftype: 0x81    sub-id 0x0018: 1c   # noqa: E501
            # 00:00:07  0x4310   wifi data       ftype: 0x01    sub-id 0x0018: 0c   # noqa: E501
            # 00:00:08  0x4810   options?        ftype: 0x01

            0x4110: self.msg_dev_ind,     # device data, sync start
            0x1110: self.msg_response,    # every 3 hours

            0x4310: self.msg_sync_start,  # regulary after 3-6 hours
            0x1310: self.msg_response,
            0x4810: self.msg_sync_end,    # sync end
            0x1810: self.msg_response,

            #
            # MODbus or AT cmd
            0x4510: self.msg_command_req,  # from server
            0x1510: self.msg_command_rsp,     # from inverter
        }
        self.modbus_elms = 0    # for unit tests

    '''
    Our puplic methods
    '''
    def close(self) -> None:
        logging.debug('Solarman.close()')
        # we have refernces to methods of this class in self.switch
        # so we have to erase self.switch, otherwise this instance can't be
        # deallocated by the garbage collector ==> we get a memory leak
        self.switch.clear()
        self.state = self.STATE_CLOSED
        super().close()

    def __set_serial_no(self, snr: int):
        serial_no = str(snr)
        if self.unique_id == serial_no:
            logger.debug(f'SerialNo: {serial_no}')
        else:
            found = False
            inverters = Config.get('inverters')
            # logger.debug(f'Inverters: {inverters}')

            for inv in inverters.values():
                # logger.debug(f'key: {key} -> {inv}')
                if (type(inv) is dict and 'monitor_sn' in inv
                   and inv['monitor_sn'] == snr):
                    found = True
                    self.node_id = inv['node_id']
                    self.sug_area = inv['suggested_area']
                    logger.debug(f'SerialNo {serial_no} allowed! area:{self.sug_area}')  # noqa: E501
                    self.db.set_pv_module_details(inv)

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
                self.__set_serial_no(self.snr)
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

    def _timestamp(self):
        # utc as epoche
        return int(time.time())    # pragma: no cover

    def _heartbeat(self) -> int:
        return 60                  # pragma: no cover

    def __parse_header(self, buf: bytes, buf_len: int) -> None:

        if (buf_len < self.header_len):  # enough bytes for complete header?
            return

        result = struct.unpack_from('<BHHHL', buf, 0)

        # store parsed header values in the class
        start = result[0]            # start byte
        self.data_len = result[1]    # len of variable id string
        self.control = result[2]
        self.seq.set_recv(result[3])
        self.snr = result[4]

        if start != 0xA5:
            self.inc_counter('Invalid_Msg_Format')
            # erase broken recv buffer
            self._recv_buffer = bytearray()
            return
        self.header_valid = True
        return

    def __trailer_is_ok(self, buf: bytes, buf_len: int) -> bool:
        crc = buf[self.data_len+11]
        stop = buf[self.data_len+12]
        if stop != 0x15:
            self.inc_counter('Invalid_Msg_Format')
            if len(self._recv_buffer) > (self.data_len+13):
                next_start = buf[self.data_len+13]
                if next_start != 0xa5:
                    # erase broken recv buffer
                    self._recv_buffer = bytearray()

            return False

        check = sum(buf[1:buf_len-2]) & 0xff
        if check != crc:
            self.inc_counter('Invalid_Msg_Format')
            logger.debug(f'CRC {int(crc):#02x} {int(check):#08x}'
                         f' Stop:{int(stop):#02x}')
            # start & stop byte are valid, discard only this message
            return False

        return True

    def __build_header(self, ctrl) -> None:
        '''build header for new transmit message'''
        self.send_msg_ofs = len(self._send_buffer)

        self._send_buffer += struct.pack(
            '<BHHHL', 0xA5, 0, ctrl, self.seq.get_send(), self.snr)
        fnc = self.switch.get(ctrl, self.msg_unknown)
        logger.info(self.__flow_str(self.server_side, 'tx') +
                    f' Ctl: {int(ctrl):#04x} Msg: {fnc.__name__!r}')

    def __finish_send_msg(self) -> None:
        '''finish the transmit message, set lenght and checksum'''
        _len = len(self._send_buffer) - self.send_msg_ofs
        struct.pack_into('<H', self._send_buffer, self.send_msg_ofs+1, _len-11)
        check = sum(self._send_buffer[self.send_msg_ofs+1:self.send_msg_ofs +
                                      _len]) & 0xff
        self._send_buffer += struct.pack('<BB', check, 0x15)    # crc & stop

    def _update_header(self, _forward_buffer):
        '''update header for message before forwarding,
        set sequence and checksum'''
        _len = len(_forward_buffer)
        struct.pack_into('<H', _forward_buffer, 1,
                         _len-13)
        struct.pack_into('<H', _forward_buffer, 5,
                         self.seq.get_send())

        check = sum(_forward_buffer[1:_len-2]) & 0xff
        struct.pack_into('<B', _forward_buffer, _len-2, check)

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

    def __send_ack_rsp(self, msgtype, ftype, ack=1):
        self.__build_header(msgtype)
        self._send_buffer += struct.pack('<BBLL', ftype, ack,
                                         self._timestamp(),
                                         self._heartbeat())
        self.__finish_send_msg()

    def send_modbus_cb(self, pdu: bytearray, state: str):
        if self.state != self.STATE_UP:
            return
        self.__build_header(0x4510)
        self._send_buffer += struct.pack('<BHLLL', self.MB_RTU_CMD,
                                         0x2b0, 0, 0, 0)
        self._send_buffer += pdu
        self.__finish_send_msg()
        hex_dump_memory(logging.INFO, f'Send Modbus {state}:{self.addr}:',
                        self._send_buffer, len(self._send_buffer))
        self.writer.write(self._send_buffer)
        self._send_buffer = bytearray(0)  # self._send_buffer[sent:]

    async def send_modbus_cmd(self, func, addr, val) -> None:
        if self.state != self.STATE_UP:
            return
        self.mb.build_msg(Modbus.INV_ADDR, func, addr, val)

    async def send_at_cmd(self, AT_cmd: str) -> None:
        if self.state != self.STATE_UP:
            return
        self.forward_at_cmd_resp = False
        self.__build_header(0x4510)
        self._send_buffer += struct.pack(f'<BHLLL{len(AT_cmd)}sc', self.AT_CMD,
                                         2, 0, 0, 0, AT_cmd.encode('utf-8'),
                                         b'\r')
        self.__finish_send_msg()
        try:
            await self.async_write('Send AT Command:')
        except Exception:
            self._send_buffer = bytearray(0)

    def __forward_msg(self):
        self.forward(self._recv_buffer, self.header_len+self.data_len+2)

    def __build_model_name(self):
        db = self.db
        MaxPow = db.get_db_value(Register.MAX_DESIGNED_POWER, 0)
        Rated = db.get_db_value(Register.RATED_POWER, 0)
        Model = None
        if MaxPow == 2000:
            if Rated == 800 or Rated == 600:
                Model = f'TSOL-MS{MaxPow}({Rated})'
            else:
                Model = f'TSOL-MS{MaxPow}'
        elif MaxPow == 1800 or MaxPow == 1600:
            Model = f'TSOL-MS{MaxPow}'
        if Model:
            logger.info(f'Model: {Model}')
            self.db.set_db_def_value(Register.EQUIPMENT_MODEL, Model)

    def __process_data(self, ftype):
        inv_update = False
        msg_type = self.control >> 8
        for key, update in self.db.parse(self._recv_buffer, msg_type, ftype,
                                         self.node_id):
            if update:
                if key == 'inverter':
                    inv_update = True
                self.new_data[key] = True

        if inv_update:
            self.__build_model_name()
    '''
    Message handler methods
    '''
    def msg_unknown(self):
        logger.warning(f"Unknow Msg: ID:{int(self.control):#04x}")
        self.inc_counter('Unknown_Msg')
        self.__forward_msg()

    def msg_dev_ind(self):
        data = self._recv_buffer[self.header_len:]
        result = struct.unpack_from('<BLLL', data, 0)
        ftype = result[0]  # always 2
        # total = result[1]
        tim = result[2]
        res = result[3]  # always zero
        logger.info(f'frame type:{ftype:02x}'
                    f' timer:{tim:08x}s  null:{res}')
        # if self.time_ofs:
        #     dt = datetime.fromtimestamp(total + self.time_ofs)
        #     logger.info(f'ts: {dt.strftime("%Y-%m-%d %H:%M:%S")}')

        self.__process_data(ftype)
        self.__forward_msg()
        self.__send_ack_rsp(0x1110, ftype)

    def msg_data_ind(self):
        data = self._recv_buffer
        result = struct.unpack_from('<BHLLLHL', data, self.header_len)
        ftype = result[0]  # 1 or 0x81
        # total = result[2]
        tim = result[3]
        if 1 == ftype:
            self.time_ofs = result[4]
        unkn = result[5]
        cnt = result[6]
        logger.info(f'ftype:{ftype:02x} timer:{tim:08x}s'
                    f' ??: {unkn:04x} cnt:{cnt}')
        # if self.time_ofs:
        #     dt = datetime.fromtimestamp(total + self.time_ofs)
        #     logger.info(f'ts: {dt.strftime("%Y-%m-%d %H:%M:%S")}')

        self.__process_data(ftype)
        self.__forward_msg()
        self.__send_ack_rsp(0x1210, ftype)
        self.state = self.STATE_UP

    def msg_sync_start(self):
        data = self._recv_buffer[self.header_len:]
        result = struct.unpack_from('<BLLL', data, 0)
        ftype = result[0]
        total = result[1]
        self.time_ofs = result[3]

        dt = datetime.fromtimestamp(total + self.time_ofs)
        logger.info(f'ts: {dt.strftime("%Y-%m-%d %H:%M:%S")}')

        self.__forward_msg()
        self.__send_ack_rsp(0x1310, ftype)

    def msg_command_req(self):
        data = self._recv_buffer[self.header_len:
                                 self.header_len+self.data_len]
        result = struct.unpack_from('<B', data, 0)
        ftype = result[0]
        if ftype == self.AT_CMD:
            self.inc_counter('AT_Command')
            self.forward_at_cmd_resp = True
        elif ftype == self.MB_RTU_CMD:
            if self.remoteStream.mb.recv_req(data[15:],
                                             self.__forward_msg()):
                self.inc_counter('Modbus_Command')
            else:
                self.inc_counter('Invalid_Msg_Format')
            return

        self.__forward_msg()

    def msg_command_rsp(self):
        data = self._recv_buffer[self.header_len:
                                 self.header_len+self.data_len]
        ftype = data[0]
        if ftype == self.AT_CMD:
            if not self.forward_at_cmd_resp:
                return
        elif ftype == self.MB_RTU_CMD:
            valid = data[1]
            modbus_msg_len = self.data_len - 14
            # logger.debug(f'modbus_len:{modbus_msg_len} accepted:{valid}')
            if valid == 1 and modbus_msg_len > 4:
                # logger.info(f'first byte modbus:{data[14]}')
                inv_update = False
                self.modbus_elms = 0

                for key, update, _ in self.mb.recv_resp(self.db, data[14:],
                                                        self.node_id):
                    self.modbus_elms += 1
                    if update:
                        if key == 'inverter':
                            inv_update = True
                        self.new_data[key] = True

                if inv_update:
                    self.__build_model_name()
            return
        self.__forward_msg()

    def msg_hbeat_ind(self):
        data = self._recv_buffer[self.header_len:]
        result = struct.unpack_from('<B', data, 0)
        ftype = result[0]

        self.__forward_msg()
        self.__send_ack_rsp(0x1710, ftype)
        self.state = self.STATE_UP

    def msg_sync_end(self):
        data = self._recv_buffer[self.header_len:]
        result = struct.unpack_from('<BLLL', data, 0)
        ftype = result[0]
        total = result[1]
        self.time_ofs = result[3]

        dt = datetime.fromtimestamp(total + self.time_ofs)
        logger.info(f'ts: {dt.strftime("%Y-%m-%d %H:%M:%S")}')

        self.__forward_msg()
        self.__send_ack_rsp(0x1810, ftype)

    def msg_response(self):
        data = self._recv_buffer[self.header_len:]
        result = struct.unpack_from('<BBLL', data, 0)
        ftype = result[0]  # always 2
        valid = result[1] == 1  # status
        ts = result[2]
        set_hb = result[3]  # always 60 or 120
        logger.debug(f'ftype:{ftype} accepted:{valid}'
                     f' ts:{ts:08x}  nextHeartbeat: {set_hb}s')

        dt = datetime.fromtimestamp(ts)
        logger.debug(f'ts: {dt.strftime("%Y-%m-%d %H:%M:%S")}')
        self.__forward_msg()
