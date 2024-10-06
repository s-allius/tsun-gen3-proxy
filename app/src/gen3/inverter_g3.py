from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3.inverter_g3":
    from app.src.inverter_base import InverterBase
    from app.src.gen3.talent import Talent
else:  # pragma: no cover
    from inverter_base import InverterBase
    from gen3.talent import Talent


class InverterG3(InverterBase):
    def __init__(self, reader: StreamReader, writer: StreamWriter):
        super().__init__(reader, writer, 'tsun', Talent)
