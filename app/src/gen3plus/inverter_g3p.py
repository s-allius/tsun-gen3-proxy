from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3plus.inverter_g3p":
    from app.src.inverter_base import InverterBase
    from app.src.gen3plus.solarman_v5 import SolarmanV5
else:  # pragma: no cover
    from inverter_base import InverterBase
    from gen3plus.solarman_v5 import SolarmanV5


class InverterG3P(InverterBase):
    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 client_mode: bool = False):
        super().__init__(reader, writer, 'solarman',
                         SolarmanV5, client_mode)
