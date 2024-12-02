import asyncio
import logging
from itertools import count


class Timer:
    def __init__(self, cb, id_str: str = ''):
        self.__timeout_cb = cb
        self.loop = asyncio.get_event_loop()
        self.tim = None
        self.id_str = id_str
        self.exp_count = count(0)

    def start(self, timeout: float) -> None:
        '''Start timer with timeout seconds'''
        if self.tim:
            self.tim.cancel()
        self.tim = self.loop.call_later(timeout, self.__timeout)
        logging.debug(f'[{self.id_str}]Start timer')

    def stop(self) -> None:
        '''Stop timer'''
        logging.debug(f'[{self.id_str}]Stop timer')
        if self.tim:
            self.tim.cancel()
            self.tim = None

    def __timeout(self) -> None:
        '''timer expired handler'''
        logging.debug(f'[{self.id_str}]Timer expired')
        self.__timeout_cb(next(self.exp_count))

    def close(self) -> None:
        self.stop()
        self.__timeout_cb = None
