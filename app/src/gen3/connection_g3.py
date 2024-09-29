import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3.connection_g3":
    from app.src.async_stream import AsyncStreamServer
    from app.src.async_stream import AsyncStreamClient
    from app.src.inverter import Inverter
    from app.src.gen3.talent import Talent
else:  # pragma: no cover
    from async_stream import AsyncStreamServer
    from async_stream import AsyncStreamClient
    from inverter import Inverter
    from gen3.talent import Talent

logger = logging.getLogger('conn')


class ConnectionG3(Talent):
    def healthy(self) -> bool:
        logger.debug('ConnectionG3 healthy()')
        return self._ifc.healthy()

    def close(self):
        self._ifc.close()
        Talent.close(self)
        # logger.info(f'AsyncStream refs: {gc.get_referrers(self)}')


class ConnectionG3Server(ConnectionG3):

    def __init__(self, inverter: "Inverter",
                 reader: StreamReader, writer: StreamWriter,
                 addr, id_str=b'') -> None:

        server_side = True
        self._ifc = AsyncStreamServer(reader, writer,
                                      inverter.async_publ_mqtt,
                                      inverter.async_create_remote,
                                      inverter.remote)
        self.conn_no = self._ifc.get_conn_no()
        self.addr = addr
        Talent.__init__(self, server_side, self._ifc, id_str)


class ConnectionG3Client(ConnectionG3):

    def __init__(self, inverter: "Inverter",
                 reader: StreamReader, writer: StreamWriter,
                 addr, id_str=b'') -> None:
        server_side = False
        self._ifc = AsyncStreamClient(reader, writer,
                                      inverter.remote)
        self.conn_no = self._ifc.get_conn_no()
        self.addr = addr
        Talent.__init__(self, server_side, self._ifc, id_str)
