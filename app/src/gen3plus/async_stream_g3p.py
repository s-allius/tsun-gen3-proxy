import logging
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

        self.remoteStream = remote_stream

    '''
    Our puplic methods
    '''
    def close(self):
        AsyncStream.close(self)
        SolarmanV5.close(self)
        #  logger.info(f'AsyncStream refs: {gc.get_referrers(self)}')

    async def async_create_remote(self) -> None:
        pass

    async def async_publ_mqtt(self) -> None:
        pass

    '''
    Our private methods
    '''
    def __del__(self):
        super().__del__()
