import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3.inverter_g3":
    from app.src.inverter_base import InverterBase
    from app.src.async_stream import StreamPtr
    from app.src.async_stream import AsyncStreamServer
    from app.src.gen3.connection_g3 import ConnectionG3
else:  # pragma: no cover
    from inverter_base import InverterBase
    from async_stream import StreamPtr
    from async_stream import AsyncStreamServer
    from gen3.connection_g3 import ConnectionG3


logger_mqtt = logging.getLogger('mqtt')


class InverterG3(InverterBase):
    def __init__(self, reader: StreamReader, writer: StreamWriter, addr):
        super().__init__()
        self.addr = addr
        self.remote = StreamPtr(None)
        ifc = AsyncStreamServer(reader, writer,
                                self.async_publ_mqtt,
                                self.async_create_remote,
                                self.remote)

        self.local = StreamPtr(
            ConnectionG3(addr, ifc, True)
        )

    async def async_create_remote(self) -> None:
        await InverterBase.async_create_remote(
            self, 'tsun', ConnectionG3)
