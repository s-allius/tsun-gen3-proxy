import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3plus.inverter_g3p":
    from app.src.inverter import Inverter
    from app.src.async_stream import StreamPtr
    from app.src.gen3plus.connection_g3p import ConnectionG3PServer
    from app.src.gen3plus.connection_g3p import ConnectionG3PClient
else:  # pragma: no cover
    from inverter import Inverter
    from async_stream import StreamPtr
    from gen3plus.connection_g3p import ConnectionG3PServer
    from gen3plus.connection_g3p import ConnectionG3PClient


logger_mqtt = logging.getLogger('mqtt')


class InverterG3P(Inverter):
    def __init__(self, reader: StreamReader, writer: StreamWriter, addr,
                 client_mode: bool = False):
        super().__init__()
        self.addr = addr
        self.remote = StreamPtr(None)
        self.local = StreamPtr(
            ConnectionG3PServer(self, reader, writer, addr, client_mode)
        )

    async def async_create_remote(self) -> None:
        await Inverter.async_create_remote(
            self, 'solarman', ConnectionG3PClient)

    def close(self) -> None:
        logging.debug(f'InverterG3P.close() {self.addr}')
        self.local.stream.close()
#        logger.debug (f'Inverter refs: {gc.get_referrers(self)}')
