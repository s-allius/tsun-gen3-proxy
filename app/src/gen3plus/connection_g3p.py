import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3plus.connection_g3p":
    from app.src.async_ifc import AsyncIfc
    from app.src.async_stream import AsyncStream
    from app.src.gen3plus.solarman_v5 import SolarmanV5
else:  # pragma: no cover
    from async_ifc import AsyncIfc
    from async_stream import AsyncStream
    from gen3plus.solarman_v5 import SolarmanV5

logger = logging.getLogger('conn')


class ConnectionG3P(AsyncStream, SolarmanV5):

    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 addr, remote_stream: 'ConnectionG3P',
                 server_side: bool,
                 client_mode: bool) -> None:
        self._ifc = AsyncIfc()
        AsyncStream.__init__(self, reader, writer, addr, self._ifc)
        SolarmanV5.__init__(self, server_side, client_mode, self._ifc)

        self.remote_stream: 'ConnectionG3P' = remote_stream

    '''
    Our puplic methods
    '''
    def close(self):
        AsyncStream.close(self)
        SolarmanV5.close(self)
        #  logger.info(f'AsyncStream refs: {gc.get_referrers(self)}')

    async def async_create_remote(self) -> None:
        pass  # virtual interface # pragma: no cover

    async def async_publ_mqtt(self) -> None:
        pass  # virtual interface # pragma: no cover

    def healthy(self) -> bool:
        logger.debug('ConnectionG3P healthy()')
        return AsyncStream.healthy(self)

    '''
    Our private methods
    '''
    def __del__(self):
        super().__del__()
