import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3plus.inverter_g3p":
    from app.src.inverter_base import InverterBase
    from app.src.async_stream import StreamPtr
    from app.src.async_stream import AsyncStreamServer
    from app.src.gen3plus.solarman_v5 import SolarmanV5
else:  # pragma: no cover
    from inverter_base import InverterBase
    from async_stream import StreamPtr
    from async_stream import AsyncStreamServer
    from gen3plus.solarman_v5 import SolarmanV5


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
            SolarmanV5(addr, ifc, True, client_mode), ifc
        )

    async def async_create_remote(self) -> None:
        await InverterBase.async_create_remote(
            self, 'solarman', SolarmanV5)
