from asyncio import StreamReader, StreamWriter

from inverter_base import InverterBase
from gen3plus.solarman_v5 import SolarmanV5
from gen3plus.solarman_emu import SolarmanEmu


class InverterG3P(InverterBase):
    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 client_mode: bool = False):
        remote_prot = None
        self.forward_at_cmd_resp = False
        if client_mode:
            remote_prot = SolarmanEmu
        super().__init__(reader, writer, 'solarman',
                         SolarmanV5, client_mode, remote_prot)
