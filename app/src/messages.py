import logging
import weakref

if __name__ == "app.src.messages":
    from app.src.infos import Infos
else:  # pragma: no cover
    from infos import Infos

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


class IterRegistry(type):
    def __iter__(cls):
        for ref in cls._registry:
            obj = ref()
            if obj is not None:
                yield obj


class Message(metaclass=IterRegistry):
    _registry = []

    def __init__(self, server_side: bool):
        self._registry.append(weakref.ref(self))

        self.server_side = server_side
        self.header_valid = False
        self.header_len = 0
        self.data_len = 0
        self.unique_id = 0
        self.node_id = ''
        self.sug_area = ''
        self._recv_buffer = bytearray(0)
        self._send_buffer = bytearray(0)
        self._forward_buffer = bytearray(0)
        self.db = Infos()
        self.new_data = {}

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
        pass  # pragma: no cover

    def inc_counter(self, counter: str) -> None:
        self.db.inc_counter(counter)
        Infos.new_stat_data['proxy'] = True

    def dec_counter(self, counter: str) -> None:
        self.db.dec_counter(counter)
        Infos.new_stat_data['proxy'] = True
