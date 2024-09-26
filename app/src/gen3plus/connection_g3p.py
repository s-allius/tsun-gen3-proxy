import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3plus.connection_g3p":
    from app.src.async_stream import AsyncStreamServer
    from app.src.async_stream import AsyncStreamClient, StreamPtr
    from app.src.gen3plus.solarman_v5 import SolarmanV5
else:  # pragma: no cover
    from async_stream import AsyncStreamServer
    from async_stream import AsyncStreamClient, StreamPtr
    from gen3plus.solarman_v5 import SolarmanV5

logger = logging.getLogger('conn')


class ConnectionG3P(SolarmanV5):
    async def async_create_remote(self) -> None:
        pass  # virtual interface # pragma: no cover

    async def async_publ_mqtt(self) -> None:
        pass  # virtual interface # pragma: no cover

    def healthy(self) -> bool:
        logger.debug('ConnectionG3P healthy()')
        return self._ifc.healthy()

    def close(self):
        self._ifc.close()
        SolarmanV5.close(self)
        #  logger.info(f'AsyncStream refs: {gc.get_referrers(self)}')


class ConnectionG3PServer(ConnectionG3P):

    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 addr, rstream: 'ConnectionG3PClient',
                 client_mode: bool) -> None:

        server_side = True
        self.remote = StreamPtr(rstream)
        self._ifc = AsyncStreamServer(reader, writer, addr,
                                      self.async_publ_mqtt,
                                      self.async_create_remote,
                                      self.remote)
        self.conn_no = self._ifc.get_conn_no()
        self.addr = addr
        SolarmanV5.__init__(self, server_side, client_mode, self._ifc)


class ConnectionG3PClient(ConnectionG3P):

    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 addr, rstream: 'ConnectionG3PServer') -> None:

        server_side = False
        client_mode = False
        self.remote = StreamPtr(rstream)
        self._ifc = AsyncStreamClient(reader, writer, addr, self.remote)
        self.conn_no = self._ifc.get_conn_no()
        self.addr = addr
        SolarmanV5.__init__(self, server_side, client_mode, self._ifc)
