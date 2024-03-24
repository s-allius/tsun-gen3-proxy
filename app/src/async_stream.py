import logging
import traceback
from messages import hex_dump_memory

logger = logging.getLogger('conn')


class AsyncStream():

    def __init__(self, reader, writer, addr) -> None:
        logger.debug('AsyncStream.__init__')
        self.reader = reader
        self.writer = writer
        self.addr = addr
        self.r_addr = ''
        self.l_addr = ''

    async def loop(self):
        self.r_addr = self.writer.get_extra_info('peername')
        self.l_addr = self.writer.get_extra_info('sockname')

        while True:
            try:
                await self.__async_read()

                if self.unique_id:
                    await self.__async_write()
                    await self.__async_forward()
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

    def disc(self) -> None:
        logger.debug(f'AsyncStream.disc() l{self.l_addr} | r{self.r_addr}')
        self.writer.close()

    def close(self):
        logger.debug(f'AsyncStream.close() l{self.l_addr} | r{self.r_addr}')
        self.writer.close()

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

    async def __async_write(self) -> None:
        if self._send_buffer:
            hex_dump_memory(logging.INFO, f'Transmit to {self.addr}:',
                            self._send_buffer, len(self._send_buffer))
            self.writer.write(self._send_buffer)
            await self.writer.drain()
            self._send_buffer = bytearray(0)  # self._send_buffer[sent:]

    async def __async_forward(self) -> None:
        if self._forward_buffer:
            if not self.remoteStream:
                await self.async_create_remote()
                if self.remoteStream:
                    self.remoteStream._init_new_client_conn(self.contact_name,
                                                            self.contact_mail)
                    await self.remoteStream.__async_write()

            if self.remoteStream:
                hex_dump_memory(logging.INFO,
                                f'Forward to {self.remoteStream.addr}:',
                                self._forward_buffer,
                                len(self._forward_buffer))
                self.remoteStream.writer.write(self._forward_buffer)
                await self.remoteStream.writer.drain()
                self._forward_buffer = bytearray(0)

    def __del__(self):
        logger.debug(
            f"AsyncStream.__del__  l{self.l_addr} | r{self.r_addr}")
