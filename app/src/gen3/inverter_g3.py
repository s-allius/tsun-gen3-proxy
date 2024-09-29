import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3.inverter_g3":
    from app.src.inverter import Inverter
    from app.src.async_stream import StreamPtr
    from app.src.gen3.connection_g3 import ConnectionG3Server
    from app.src.gen3.connection_g3 import ConnectionG3Client
else:  # pragma: no cover
    from inverter import Inverter
    from async_stream import StreamPtr
    from gen3.connection_g3 import ConnectionG3Server
    from gen3.connection_g3 import ConnectionG3Client


logger_mqtt = logging.getLogger('mqtt')


class InverterG3(Inverter):
    def __init__(self, reader: StreamReader, writer: StreamWriter, addr):
        super().__init__()
        self.addr = addr
        self.remote = StreamPtr(None)
        self.local = StreamPtr(
            ConnectionG3Server(self, reader, writer, addr)
        )

    async def async_create_remote(self) -> None:
        await Inverter.async_create_remote(
            self, 'tsun', ConnectionG3Client)

    def close(self) -> None:
        logging.debug(f'InverterG3.close() {self.addr}')
        self.local.stream.close()
#         logging.info(f'Inverter refs: {gc.get_referrers(self)}')
