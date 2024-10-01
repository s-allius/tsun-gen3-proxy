import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3plus.inverter_g3p":
    from app.src.inverter_base import InverterBase
    from app.src.async_stream import StreamPtr
    from app.src.async_stream import AsyncStreamServer
    from app.src.gen3plus.connection_g3p import ConnectionG3P
else:  # pragma: no cover
    from inverter_base import InverterBase
    from async_stream import StreamPtr
    from async_stream import AsyncStreamServer
    from gen3plus.connection_g3p import ConnectionG3P


logger_mqtt = logging.getLogger('mqtt')


class InverterG3P(InverterBase):
    def __init__(self, reader: StreamReader, writer: StreamWriter, addr,
                 client_mode: bool = False):
        super().__init__()
        self.addr = addr
        self.remote = StreamPtr(None)
        ifc = AsyncStreamServer(reader, writer,
                                self.async_publ_mqtt,
                                self.async_create_remote,
                                self.remote)

        self.local = StreamPtr(
            ConnectionG3P(addr, ifc, True, client_mode)
        )

    async def async_create_remote(self) -> None:
        await InverterBase.async_create_remote(
            self, 'solarman', ConnectionG3P)
