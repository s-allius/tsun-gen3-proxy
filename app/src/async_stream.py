import logging

logger = logging.getLogger('conn')


class AsyncStream():

    def __init__(self, reader, writer, addr) -> None:
        logger.debug('AsyncStream.__init__')
        self.reader = reader
        self.writer = writer
        self.addr = addr
        self.r_addr = ''
        self.l_addr = ''

    def disc(self) -> None:
        logger.debug(f'AsyncStream.disc() l{self.l_addr} | r{self.r_addr}')
        self.writer.close()

    def close(self):
        logger.debug(f'AsyncStream.close() l{self.l_addr} | r{self.r_addr}')
        self.writer.close()

    def __del__(self):
        logger.debug(
            f"AsyncStream.__del__  l{self.l_addr} | r{self.r_addr}")
