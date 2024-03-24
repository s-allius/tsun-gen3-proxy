import logging
import traceback
# from config import Config
# import gc
# from messages import Message, hex_dump_memory
from async_stream import AsyncStream
from gen3plus.solarman_v5 import SolarmanV5

logger = logging.getLogger('conn')


class AsyncStreamG3P(AsyncStream, SolarmanV5):

    def __init__(self, reader, writer, addr, remote_stream,
                 server_side: bool) -> None:
        AsyncStream.__init__(self, reader, writer, addr)
        SolarmanV5.__init__(self, server_side)

    '''
    Our puplic methods
    '''
    async def loop(self):
        self.r_addr = self.writer.get_extra_info('peername')
        self.l_addr = self.writer.get_extra_info('sockname')

        while True:
            try:
                await self.__async_read()

                if self.unique_id:
                    # await self.__async_write()
                    # await self.__async_forward()
                    await self.async_publ_mqtt()

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

    def close(self):
        AsyncStream.close(self)
        SolarmanV5.close(self)
        #  logger.info(f'AsyncStream refs: {gc.get_referrers(self)}')

    '''
    Our private methods
    '''
    async def __async_read(self) -> None:
        data = await self.reader.read(4096)
        if data:
            self._recv_buffer += data
            self.read()                # call read in parent class
        else:
            raise RuntimeError("Peer closed.")

    async def async_publ_mqtt(self) -> None:
        pass

    def __del__(self):
        super().__del__()
