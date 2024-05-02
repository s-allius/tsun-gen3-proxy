import logging
# import gc
from async_stream import AsyncStream
from gen3.talent import Talent

logger = logging.getLogger('conn')


class ConnectionG3(AsyncStream, Talent):

    def __init__(self, reader, writer, addr, remote_stream, server_side: bool,
                 id_str=b'') -> None:
        AsyncStream.__init__(self, reader, writer, addr)
        Talent.__init__(self, server_side, id_str)

        self.remoteStream = remote_stream

    '''
    Our puplic methods
    '''
    def close(self):
        AsyncStream.close(self)
        Talent.close(self)
        # logger.info(f'AsyncStream refs: {gc.get_referrers(self)}')

    async def async_create_remote(self) -> None:
        pass

    async def async_publ_mqtt(self) -> None:
        pass

    async def flush_send_msg(self) -> None:
        self.writer.write(self._send_buffer)
        await self.writer.drain()
        self._send_buffer = bytearray(0)

    '''
    Our private methods
    '''
    def __del__(self):
        super().__del__()
