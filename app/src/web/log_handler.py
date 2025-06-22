from logging import Handler
from logging import LogRecord
import logging
from collections import deque

from singleton import Singleton


class LogHandler(Handler, metaclass=Singleton):
    def __init__(self, capacity=64):
        super().__init__(logging.WARNING)
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)

    def emit(self, record: LogRecord):
        self.buffer.append({
            'ctime': record.created,
            'level': record.levelno,
            'lname': record.levelname,
            'msg': record.getMessage()
        })

    def get_buffer(self, elms=0) -> list:
        return list(self.buffer)[-elms:]

    def clear(self):
        self.buffer.clear()
