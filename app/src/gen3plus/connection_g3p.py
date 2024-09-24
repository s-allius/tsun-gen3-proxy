import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3plus.connection_g3p":
    from app.src.async_stream import AsyncStream, StreamPtr
    from app.src.gen3plus.solarman_v5 import SolarmanV5
else:  # pragma: no cover
    from async_stream import AsyncStream, StreamPtr
    from gen3plus.solarman_v5 import SolarmanV5

logger = logging.getLogger('conn')


class ConnectionG3P(SolarmanV5):

    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 addr, rstream: 'ConnectionG3P',
                 server_side: bool,
                 client_mode: bool) -> None:

        self.remote = StreamPtr(rstream)
        self._ifc = AsyncStream(reader, writer, addr,
                                self.async_publ_mqtt,
                                self.async_create_remote,
                                self.remote)
        SolarmanV5.__init__(self, server_side, client_mode, self._ifc)

        self.conn_no = self._ifc.get_conn_no()
        self.addr = addr

    '''
    Our puplic methods
    '''
    def close(self):
        self._ifc.close()
        SolarmanV5.close(self)
        #  logger.info(f'AsyncStream refs: {gc.get_referrers(self)}')

    async def async_create_remote(self) -> None:
        pass  # virtual interface # pragma: no cover

    async def async_publ_mqtt(self) -> None:
        pass  # virtual interface # pragma: no cover

    def healthy(self) -> bool:
        logger.debug('ConnectionG3P healthy()')
        return self._ifc.healthy()
