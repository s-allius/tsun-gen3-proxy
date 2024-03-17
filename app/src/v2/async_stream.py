import logging
import traceback
# from config import Config
# import gc
# from messages import Message, hex_dump_memory
from v2.solarman_v5 import SolarmanV5

logger = logging.getLogger('conn')


class AsyncStreamV2(SolarmanV5):  # Message):

    def __init__(self, reader, writer, addr, remote_stream, server_side: bool,
                 id_str=b'') -> None:
        super().__init__(server_side, id_str)
        self.reader = reader
        self.writer = writer
        self.addr = addr
        self.r_addr = ''
        self.l_addr = ''
        self._recv_buffer = bytearray(0)

    '''
    Our puplic methods
    '''
    async def loop(self):
        self.r_addr = self.writer.get_extra_info('peername')
        self.l_addr = self.writer.get_extra_info('sockname')
        logger.info(f'in AsyncStreamV2.loop() l{self.l_addr}')

        while True:
            try:
                await self.__async_read()

            except (ConnectionResetError,
                    ConnectionAbortedError,
                    BrokenPipeError,
                    RuntimeError) as error:
                logger.warning(f'In loop for l{self.l_addr} | '
                               f'r{self.r_addr}: {error}')
                self.close()
                return self
            except Exception:
                self.inc_counter('SW_Exception')
                logger.error(
                    f"Exception for {self.addr}:\n"
                    f"{traceback.format_exc()}")
                self.close()
                return self

    def disc(self) -> None:
        logger.debug(
            f'in AsyncStreamV2.disc() l{self.l_addr} | r{self.r_addr}')
        self.writer.close()

    def close(self):
        logger.debug(
            f'in AsyncStreamV2.close() l{self.l_addr} | r{self.r_addr}')
        self.writer.close()
        # super().close()         # call close handler in the parent class

#        logger.info(f'AsyncStream refs: {gc.get_referrers(self)}')

    '''
    Our private methods
    '''
    async def __async_read(self) -> None:
        logger.debug('in AsyncStreamV2.__async_read()')
        data = await self.reader.read(4096)

        if data:
            self._recv_buffer += data
            self.read()                # call read in parent class
        else:
            raise RuntimeError("Peer closed.")

    def __del__(self):
        logger.debug(
            f"AsyncStreamV2.__del__  l{self.l_addr} | r{self.r_addr}")
