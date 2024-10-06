
if __name__ == "app.src.byte_fifo":
    from app.src.messages import hex_dump_str, hex_dump_memory
else:  # pragma: no cover
    from messages import hex_dump_str, hex_dump_memory


class ByteFifo:
    """ a byte FIFO buffer with trigger callback """
    def __init__(self):
        self.__buf = bytearray()
        self.__trigger_cb = None

    def reg_trigger(self, cb) -> None:
        self.__trigger_cb = cb

    def __iadd__(self, data):
        self.__buf.extend(data)
        return self

    def __call__(self):
        '''triggers the observer'''
        if callable(self.__trigger_cb):
            return self.__trigger_cb()
        return None

    def get(self, size: int = None) -> bytearray:
        '''removes size numbers of byte and return them'''
        if not size:
            data = self.__buf
            self.clear()
        else:
            data = self.__buf[:size]
            # The fast delete syntax
            self.__buf[:size] = b''
        return data

    def peek(self, size: int = None) -> bytearray:
        '''returns size numbers of byte without removing them'''
        if not size:
            return self.__buf
        return self.__buf[:size]

    def clear(self):
        self.__buf = bytearray()

    def __len__(self) -> int:
        return len(self.__buf)

    def __str__(self) -> str:
        return hex_dump_str(self.__buf, self.__len__())

    def logging(self, level, info):
        hex_dump_memory(level, info, self.__buf, self.__len__())
