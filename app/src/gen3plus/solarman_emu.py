import logging

if __name__ == "app.src.gen3plus.solarman_emu":
    from app.src.async_ifc import AsyncIfc
    from app.src.gen3plus.solarman_v5 import SolarmanBase
else:  # pragma: no cover
    from async_ifc import AsyncIfc
    from gen3plus.solarman_v5 import SolarmanBase

logger = logging.getLogger('msg')


class SolarmanEmu(SolarmanBase):
    def __init__(self, addr, ifc: "AsyncIfc",
                 server_side: bool, client_mode: bool):
        super().__init__(addr, ifc, server_side,
                         self.send_modbus_cb,
                         mb_timeout=8)
        logging.info('SolarmanEmu.init()')
        self.db = ifc.remote.stream.db

        self.switch = {

            # 0x4210: self.msg_data_ind,   # real time data
            0x1210: self.msg_response,   # at least every 5 minutes

            # 0x4710: self.msg_hbeat_ind,  # heatbeat
            0x1710: self.msg_response,   # every 2 minutes

            # 0x4110: self.msg_dev_ind,     # device data, sync start
            0x1110: self.msg_response,    # every 3 hours

        }

        self.log_lvl = {

            0x4110: logging.INFO,   # device data, sync start
            0x1110: logging.INFO,   # every 3 hours

            0x4210: logging.INFO,   # real time data
            0x1210: logging.INFO,   # at least every 5 minutes

            0x4710: logging.DEBUG,  # heatbeat
            0x1710: logging.DEBUG,  # every 2 minutes

        }

    '''
    Our puplic methods
    '''
    def close(self) -> None:
        logging.info('SolarmanEmu.close()')
        # we have references to methods of this class in self.switch
        # so we have to erase self.switch, otherwise this instance can't be
        # deallocated by the garbage collector ==> we get a memory leak
        self.switch.clear()
        self.log_lvl.clear()
        self.db = None
        super().close()

    def _set_serial_no(self, snr: int):
        logging.info(f'SolarmanEmu._set_serial_no, snr: {snr}')

    def _init_new_client_conn(self) -> bool:
        logging.info('SolarmanEmu.init_new()')
        return False

    '''
    Message handler methods
    '''
    def msg_unknown(self):
        logger.warning(f"Unknow Msg: ID:{int(self.control):#04x}")
        self.inc_counter('Unknown_Msg')

    def send_modbus_cb(self, pdu: bytearray, log_lvl: int, state: str):
        logger.warning(f'[{self.node_id}] ignore MODBUS cmd,'
                       ' cause we are in EMU mode')
