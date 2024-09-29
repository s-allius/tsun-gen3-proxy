import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3plus.connection_g3p":
    from app.src.async_stream import AsyncStreamServer
    from app.src.async_stream import AsyncStreamClient
    from app.src.inverter import Inverter
    from app.src.gen3plus.solarman_v5 import SolarmanV5
else:  # pragma: no cover
    from async_stream import AsyncStreamServer
    from async_stream import AsyncStreamClient
    from inverter import Inverter
    from gen3plus.solarman_v5 import SolarmanV5

logger = logging.getLogger('conn')


class ConnectionG3P(SolarmanV5):
    def healthy(self) -> bool:
        logger.debug('ConnectionG3P healthy()')
        return self._ifc.healthy()

    def close(self):
        self._ifc.close()
        SolarmanV5.close(self)
        #  logger.info(f'AsyncStream refs: {gc.get_referrers(self)}')


class ConnectionG3PServer(ConnectionG3P):

    def __init__(self, inverter: "Inverter",
                 reader: StreamReader, writer: StreamWriter,
                 addr, client_mode: bool) -> None:

        server_side = True
        self._ifc = AsyncStreamServer(reader, writer,
                                      inverter.async_publ_mqtt,
                                      inverter.async_create_remote,
                                      inverter.remote)
        self.conn_no = self._ifc.get_conn_no()
        self.addr = addr
        SolarmanV5.__init__(self, server_side, client_mode, self._ifc)


class ConnectionG3PClient(ConnectionG3P):

    def __init__(self, inverter: "Inverter",
                 reader: StreamReader, writer: StreamWriter,
                 addr) -> None:

        server_side = False
        client_mode = False
        self._ifc = AsyncStreamClient(reader, writer, inverter.remote)
        self.conn_no = self._ifc.get_conn_no()
        self.addr = addr
        SolarmanV5.__init__(self, server_side, client_mode, self._ifc)
