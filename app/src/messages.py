import logging
import weakref
from typing import Callable
from enum import Enum


if __name__ == "app.src.messages":
    from app.src.iter_registry import IterRegistry
    from app.src.infos import Infos, Register
    from app.src.modbus import Modbus
else:  # pragma: no cover
    from iter_registry import IterRegistry
    from infos import Infos, Register
    from modbus import Modbus

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


class Message(metaclass=IterRegistry):
    _registry = []
    MAX_START_TIME = 400
    '''maximum time without a received msg in sec'''
    MAX_INV_IDLE_TIME = 120
    '''maximum time without a received msg from the inverter in sec'''
    MAX_DEF_IDLE_TIME = 360
    '''maximum default time without a received msg in sec'''

    def __init__(self, server_side: bool, send_modbus_cb:
                 Callable[[bytes, int, str], None], mb_timeout: int):
        self._registry.append(weakref.ref(self))

        self.server_side = server_side
        if server_side:
            self.mb = Modbus(send_modbus_cb, mb_timeout)
        else:
            self.mb = None

        self.header_valid = False
        self.header_len = 0
        self.data_len = 0
        self.unique_id = 0
        self._node_id = ''
        self.sug_area = ''
        self.new_data = {}
        self.state = State.init
        self.shutdown_started = False

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

    '''
    Our puplic methods
    '''
    def close(self) -> None:
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
