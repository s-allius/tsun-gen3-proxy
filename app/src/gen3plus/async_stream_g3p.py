import logging
# from config import Config
# import gc
# from messages import Message, hex_dump_memory
from async_stream import AsyncStream
from gen3plus.solarman_v5 import SolarmanV5
from messages import hex_dump_memory

logger = logging.getLogger('conn')


class AsyncStreamG3P(AsyncStream, SolarmanV5):

    def __init__(self, reader, writer, addr, remote_stream,
                 server_side: bool) -> None:
        AsyncStream.__init__(self, reader, writer, addr)
        SolarmanV5.__init__(self, server_side)

        self.remoteStream = remote_stream

    '''
    Our puplic methods
    '''
    def close(self):
        AsyncStream.close(self)
        SolarmanV5.close(self)
        #  logger.info(f'AsyncStream refs: {gc.get_referrers(self)}')

    '''
    Our private methods
    '''
    async def _async_read(self) -> None:
        data = await self.reader.read(4096)
        if data:
            self._recv_buffer += data
            self.read()                # call read in parent class
        else:
            raise RuntimeError("Peer closed.")

    async def _async_write(self) -> None:
        if self._send_buffer:
            hex_dump_memory(logging.INFO, f'Transmit to {self.addr}:',
                            self._send_buffer, len(self._send_buffer))
            self.writer.write(self._send_buffer)
            await self.writer.drain()
            self._send_buffer = bytearray(0)  # self._send_buffer[sent:]

    async def _async_forward(self) -> None:
        if self._forward_buffer:
            if not self.remoteStream:
                await self.async_create_remote()
                if self.remoteStream:
                    self.remoteStream._init_new_client_conn(self.contact_name,
                                                            self.contact_mail)
                    await self.remoteStream._async_write()

            if self.remoteStream:
                hex_dump_memory(logging.INFO,
                                f'Forward to {self.remoteStream.addr}:',
                                self._forward_buffer,
                                len(self._forward_buffer))
                self.remoteStream.writer.write(self._forward_buffer)
                await self.remoteStream.writer.drain()
                self._forward_buffer = bytearray(0)

    async def async_create_remote(self) -> None:
        pass

    async def async_publ_mqtt(self) -> None:
        pass

    def __del__(self):
        super().__del__()
