from logging import Handler
from logging import LogRecord
import logging
from collections import deque

from singleton import Singleton


class BaseHandler(Handler, metaclass=Singleton):
    def __init__(self, capacity, level=logging.WARNING):
        super().__init__(level)
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


class LogHandler(BaseHandler):
    def __init__(self, capacity=64):
        super().__init__(capacity, logging.WARNING)


class TestHandler(BaseHandler):
    def __init__(self, capacity=16):
        super().__init__(capacity, logging.INFO)
