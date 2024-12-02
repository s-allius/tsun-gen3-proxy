from asyncio import StreamReader, StreamWriter

from inverter_base import InverterBase
from gen3.talent import Talent


class InverterG3(InverterBase):
    def __init__(self, reader: StreamReader, writer: StreamWriter):
        super().__init__(reader, writer, 'tsun', Talent)
