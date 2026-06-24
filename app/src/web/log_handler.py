from logging import Handler
from logging import LogRecord
import logging
from collections import deque

from singleton import Singleton


class BaseHandler(Handler, metaclass=Singleton):
    """Base class for singleton LogHandlers that store logs in memory."""
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
        """Returns the saved logs as a list."""
        return list(self.buffer)[-elms:]

    def clear(self):
        self.buffer.clear()


class LogHandler(BaseHandler):
    """Log handler for collecting warnings and error messages."""
    def __init__(self, capacity=64):
        super().__init__(capacity, logging.WARNING)


class TestHandler(BaseHandler):
    """Log handler for test results."""
    def __init__(self, capacity=16):
        super().__init__(capacity, logging.INFO)
