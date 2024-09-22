import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3.connection_g3":
    from app.src.async_ifc import AsyncIfc
    from app.src.async_stream import AsyncStream
    from app.src.gen3.talent import Talent
else:  # pragma: no cover
    from async_ifc import AsyncIfc
    from async_stream import AsyncStream
    from gen3.talent import Talent

logger = logging.getLogger('conn')


class ConnectionG3(AsyncStream, Talent):

    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 addr, remote_stream: 'ConnectionG3', server_side: bool,
                 id_str=b'') -> None:
        self._ifc = AsyncIfc()
        AsyncStream.__init__(self, reader, writer, addr, self._ifc)
        Talent.__init__(self, server_side, self._ifc, id_str)

        self.remote_stream: 'ConnectionG3' = remote_stream

    '''
    Our puplic methods
    '''
    def close(self):
        AsyncStream.close(self)
        Talent.close(self)
        # logger.info(f'AsyncStream refs: {gc.get_referrers(self)}')

    async def async_create_remote(self) -> None:
        pass  # virtual interface # pragma: no cover

    async def async_publ_mqtt(self) -> None:
        pass  # virtual interface # pragma: no cover

    def healthy(self) -> bool:
        logger.debug('ConnectionG3 healthy()')
        return AsyncStream.healthy(self)

    '''
    Our private methods
    '''
    def __del__(self):
        super().__del__()
