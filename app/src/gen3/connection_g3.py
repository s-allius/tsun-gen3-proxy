import logging
# import gc
from asyncio import StreamReader, StreamWriter
from async_stream import AsyncStream
from gen3.talent import Talent

logger = logging.getLogger('conn')


class ConnectionG3(AsyncStream, Talent):

    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 addr, remote_stream: 'ConnectionG3', server_side: bool,
                 id_str=b'') -> None:
        AsyncStream.__init__(self, reader, writer, addr)
        Talent.__init__(self, server_side, id_str)

        self.remoteStream: 'ConnectionG3' = remote_stream

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

    def healthy(self) -> bool:
        logger.debug('ConnectionG3 healthy()')
        return AsyncStream.healthy(self)

    '''
    Our private methods
    '''
    def __del__(self):
        super().__del__()
