import logging
import weakref

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
