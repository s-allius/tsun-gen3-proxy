import logging
import weakref
from typing import Callable
from enum import Enum

from async_ifc import AsyncIfc
from protocol_ifc import ProtocolIfc
from infos import Infos, Register
from modbus import Modbus
from my_timer import Timer

logger = logging.getLogger('msg')


def __hex_val(n, data, data_len):
    line = ''
    for j in range(n-16, n):
        if j >= data_len:
            break
        line += '%02x ' % abs(data[j])
    return line


def __asc_val(n, data, data_len):
    line = ''
    for j in range(n-16, n):
        if j >= data_len:
            break
        c = data[j] if not (data[j] < 0x20 or data[j] > 0x7e) else '.'
        line += '%c' % c
    return line


def hex_dump(data, data_len) -> list:
    n = 0
    lines = []

    for i in range(0, data_len, 16):
        line = '  '
        line += '%04x | ' % (i)
        n += 16
        line += __hex_val(n, data, data_len)
        line += ' ' * (3 * 16 + 9 - len(line)) + ' | '
        line += __asc_val(n, data, data_len)
        lines.append(line)

    return lines


def hex_dump_str(data, data_len):
    lines = hex_dump(data, data_len)
    return '\n'.join(lines)


def hex_dump_memory(level, info, data, data_len):
    lines = []
    lines.append(info)
    tracer = logging.getLogger('tracer')
    if not tracer.isEnabledFor(level):
        return

    lines += hex_dump(data, data_len)

    tracer.log(level, '\n'.join(lines))


class State(Enum):
    '''state of the logical connection'''
    init = 0
    '''just created'''
    received = 1
    '''at least one packet received'''
    up = 2
    '''at least one cmd-rsp transaction'''
    pend = 3
    '''inverter transaction pending, don't send MODBUS cmds'''
    closed = 4
    '''connection closed'''


class Message(ProtocolIfc):
    MAX_START_TIME = 400
    '''maximum time without a received msg in sec'''
    MAX_INV_IDLE_TIME = 120
    '''maximum time without a received msg from the inverter in sec'''
    MAX_DEF_IDLE_TIME = 360
    '''maximum default time without a received msg in sec'''
    MB_START_TIMEOUT = 40
    '''start delay for Modbus polling in server mode'''
    MB_REGULAR_TIMEOUT = 60
    '''regular Modbus polling time in server mode'''

    def __init__(self, node_id, ifc: "AsyncIfc", server_side: bool,
                 send_modbus_cb: Callable[[bytes, int, str], None],
                 mb_timeout: int):
        self._registry.append(weakref.ref(self))

        self.server_side = server_side
        self.ifc = ifc
        self.node_id = node_id
        if server_side:
            self.mb = Modbus(send_modbus_cb, mb_timeout)
            self.mb_timer = Timer(self.mb_timout_cb, self.node_id)
        else:
            self.mb = None
            self.mb_timer = None
        self.header_valid = False
        self.header_len = 0
        self.data_len = 0
        self.unique_id = 0
        self.sug_area = ''
        self.new_data = {}
        self.state = State.init
        self.shutdown_started = False
        self.modbus_elms = 0    # for unit tests
        self.mb_timeout = self.MB_REGULAR_TIMEOUT
        self.mb_first_timeout = self.MB_START_TIMEOUT
        '''timer value for next Modbus polling request'''
        self.modbus_polling = False
        self.mb_start_reg = 0
        self.mb_step = 0
        self.mb_bytes = 0
        self.mb_inv_no = 1
        self.mb_scan = False

    @property
    def node_id(self):
        return self._node_id

    @node_id.setter
    def node_id(self, value):
        self._node_id = value
        self.ifc.set_node_id(value)

    '''
    Empty methods, that have to be implemented in any child class which
    don't use asyncio
    '''
    def _read(self) -> None:     # read data bytes from socket and copy them
        # to our _recv_buffer
        return  # pragma: no cover

    def _set_config_parms(self, inv: dict):
        '''init connection with params from the configuration'''
        self.node_id = inv['node_id']
        self.sug_area = inv['suggested_area']
        self.modbus_polling = inv['modbus_polling']
        if 'modbus_scanning' in inv:
            scan = inv['modbus_scanning']
            self.mb_scan = True
            self.mb_start_reg = scan['start']
            self.mb_step = scan['step']
            self.mb_bytes = scan['bytes']
            # if 'client_mode' in self.db and \
            #         self.db.client_mode:
            self.mb_start_reg = scan['start']
            # else:
            #     self.mb_start_reg = scan['start'] - scan['step']
        if self.mb:
            self.mb.set_node_id(self.node_id)

    def _set_mqtt_timestamp(self, key, ts: float | None):
        if key not in self.new_data or \
           not self.new_data[key]:
            if key == 'grid':
                info_id = Register.TS_GRID
            elif key == 'input':
                info_id = Register.TS_INPUT
            elif key == 'total':
                info_id = Register.TS_TOTAL
            else:
                return
            # tstr = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ts))
            # logger.info(f'update: key: {key} ts:{tstr}'
            self.db.set_db_def_value(info_id, round(ts))

    def _timeout(self) -> int:
        if self.state == State.init or self.state == State.received:
            to = self.MAX_START_TIME
        elif self.state == State.up and \
                self.server_side and self.modbus_polling:
            to = self.MAX_INV_IDLE_TIME
        else:
            to = self.MAX_DEF_IDLE_TIME
        return to

    def _send_modbus_cmd(self, dev_id, func, addr, val, log_lvl) -> None:
        if self.state != State.up:
            logger.log(log_lvl, f'[{self.node_id}] ignore MODBUS cmd,'
                       ' as the state is not UP')
            return
        self.mb.build_msg(dev_id, func, addr, val, log_lvl)

    async def send_modbus_cmd(self, func, addr, val, log_lvl) -> None:
        self._send_modbus_cmd(Modbus.INV_ADDR, func, addr, val, log_lvl)

    def _send_modbus_scan(self):
        self.mb_start_reg += self.mb_step
        if self.mb_start_reg > 0xffff:
            self.mb_start_reg = self.mb_start_reg & 0xffff
            self.mb_inv_no += 1
            logging.info(f"Next Round: inv:{self.mb_inv_no}"
                         f" reg:{self.mb_start_reg:04x}")
        if (self.mb_start_reg & 0xfffc) % 0x80 == 0:
            logging.info(f"[{self.node_id}] Scan info: "
                         f"inv:{self.mb_inv_no}"
                         f" reg:{self.mb_start_reg:04x}")
        self._send_modbus_cmd(self.mb_inv_no, Modbus.READ_REGS,
                              self.mb_start_reg, self.mb_bytes,
                              logging.INFO)

    def _dump_modbus_scan(self, data, hdr_len, modbus_msg_len):
        if (data[hdr_len] == self.mb_inv_no and
                data[hdr_len+1] == Modbus.READ_REGS):
            modbus_msg_len = self.data_len - hdr_len
            logging.info(f'[{self.node_id}] Valid MODBUS data '
                         f'(reg: 0x{self.mb.last_reg:04x}):')
            hex_dump_memory(logging.INFO, 'Valid MODBUS data '
                            f'(reg: 0x{self.mb.last_reg:04x}):',
                            data[hdr_len:], modbus_msg_len)

    '''
    Our puplic methods
    '''
    def close(self) -> None:
        if self.server_side:
            # set inverter state to offline, if output power is very low
            logging.debug('close power: '
                          f'{self.db.get_db_value(Register.OUTPUT_POWER, -1)}')
            if self.db.get_db_value(Register.OUTPUT_POWER, 999) < 2:
                self.db.set_db_def_value(Register.INVERTER_STATUS, 0)
                self.new_data['env'] = True
            self.mb_timer.close()
        self.state = State.closed
        self.ifc.rx_set_cb(None)
        self.ifc.prot_set_timeout_cb(None)
        self.ifc.prot_set_init_new_client_conn_cb(None)
        self.ifc.prot_set_update_header_cb(None)
        self.ifc = None

        if self.mb:
            self.mb.close()
            self.mb = None
        # pragma: no cover

    def inc_counter(self, counter: str) -> None:
        self.db.inc_counter(counter)
        Infos.new_stat_data['proxy'] = True

    def dec_counter(self, counter: str) -> None:
        self.db.dec_counter(counter)
        Infos.new_stat_data['proxy'] = True
