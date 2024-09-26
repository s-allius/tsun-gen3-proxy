import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3.connection_g3":
    from app.src.async_stream import AsyncStreamServer
    from app.src.async_stream import AsyncStreamClient, StreamPtr
    from app.src.gen3.talent import Talent
else:  # pragma: no cover
    from async_stream import AsyncStreamServer
    from async_stream import AsyncStreamClient, StreamPtr
    from gen3.talent import Talent

logger = logging.getLogger('conn')


class ConnectionG3(Talent):
    async def async_create_remote(self) -> None:
        pass  # virtual interface # pragma: no cover

    async def async_publ_mqtt(self) -> None:
        pass  # virtual interface # pragma: no cover

    def healthy(self) -> bool:
        logger.debug('ConnectionG3 healthy()')
        return self._ifc.healthy()

    def close(self):
        self._ifc.close()
        Talent.close(self)
        # logger.info(f'AsyncStream refs: {gc.get_referrers(self)}')


class ConnectionG3Server(ConnectionG3):

    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 addr, rstream: 'ConnectionG3Client',
                 id_str=b'') -> None:

        server_side = True
        self.remote = StreamPtr(rstream)
        self._ifc = AsyncStreamServer(reader, writer, addr,
                                      self.async_publ_mqtt,
                                      self.async_create_remote,
                                      self.remote)
        self.conn_no = self._ifc.get_conn_no()
        self.addr = addr
        Talent.__init__(self, server_side, self._ifc, id_str)


class ConnectionG3Client(ConnectionG3):

    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 addr, rstream: 'ConnectionG3Server',
                 id_str=b'') -> None:
        server_side = False
        self.remote = StreamPtr(rstream)
        self._ifc = AsyncStreamClient(reader, writer, addr,
                                      self.remote)
        self.conn_no = self._ifc.get_conn_no()
        self.addr = addr
        Talent.__init__(self, server_side, self._ifc, id_str)
