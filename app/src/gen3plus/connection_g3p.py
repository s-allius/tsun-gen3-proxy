import logging
# import gc
from asyncio import StreamReader, StreamWriter
from async_stream import AsyncStream
from gen3plus.solarman_v5 import SolarmanV5

logger = logging.getLogger('conn')


class ConnectionG3P(AsyncStream, SolarmanV5):

    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 addr, remote_stream: 'ConnectionG3P',
                 server_side: bool) -> None:
        AsyncStream.__init__(self, reader, writer, addr)
        SolarmanV5.__init__(self, server_side)

        self.remoteStream: 'ConnectionG3P' = remote_stream

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

    def healthy(self) -> bool:
        logger.debug('ConnectionG3P healthy()')
        return AsyncStream.healthy(self)

    '''
    Our private methods
    '''
    def __del__(self):
        super().__del__()
