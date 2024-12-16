import logging
import struct

from async_ifc import AsyncIfc
from gen3plus.solarman_v5 import SolarmanBase
from my_timer import Timer
from infos import Register

logger = logging.getLogger('msg')


class SolarmanEmu(SolarmanBase):
    def __init__(self, addr, ifc: "AsyncIfc",
                 server_side: bool, client_mode: bool):
        super().__init__(addr, ifc, server_side=False,
                         _send_modbus_cb=None,
                         mb_timeout=8)
        logging.debug('SolarmanEmu.init()')
        self.db = ifc.remote.stream.db
        self.snr = ifc.remote.stream.snr
        self.hb_timeout = 60
        '''actual heatbeat timeout from the last response message'''
        self.data_up_inv = self.db.get_db_value(Register.DATA_UP_INTERVAL)
        '''time interval for getting new MQTT data messages'''
        self.hb_timer = Timer(self.send_heartbeat_cb, self.node_id)
        self.data_timer = Timer(self.send_data_cb, self.node_id)
        self.last_sync = self._emu_timestamp()
        '''timestamp when we send the last sync message (4110)'''
        self.pkt_cnt = 0
        '''last sent packet number'''

        self.switch = {

            0x4210: 'msg_data_ind',      # real time data
            0x1210: self.msg_response,   # at least every 5 minutes

            0x4710: 'msg_hbeat_ind',     # heatbeat
            0x1710: self.msg_response,   # every 2 minutes

            0x4110: 'msg_dev_ind',        # device data, sync start
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
        self.hb_timer.close()
        self.data_timer.close()
        self.db = None
        super().close()

    def _set_serial_no(self, snr: int):
        logging.debug(f'SolarmanEmu._set_serial_no, snr: {snr}')
        self.unique_id = str(snr)

    def _init_new_client_conn(self) -> bool:
        logging.debug('SolarmanEmu.init_new()')
        self.data_timer.start(self.data_up_inv)
        return False

    def next_pkt_cnt(self):
        '''get the next packet number'''
        self.pkt_cnt = (self.pkt_cnt + 1) & 0xffffffff
        return self.pkt_cnt

    def seconds_since_last_sync(self):
        '''get seconds since last 0x4110 message was sent'''
        return self._emu_timestamp() - self.last_sync

    def send_heartbeat_cb(self, exp_cnt):
        '''send a heartbeat to the TSUN cloud'''
        self._build_header(0x4710)
        self.ifc.tx_add(struct.pack('<B', 0))
        self._finish_send_msg()
        log_lvl = self.log_lvl.get(0x4710, logging.WARNING)
        self.ifc.tx_log(log_lvl, 'Send heartbeat:')
        self.ifc.tx_flush()

    def send_data_cb(self, exp_cnt):
        '''send a inverter data message to the TSUN cloud'''
        self.hb_timer.start(self.hb_timeout)
        self.data_timer.start(self.data_up_inv)
        _len = 420
        ftype = 1
        build_msg = self.db.build(_len, 0x42, ftype)

        self._build_header(0x4210)
        self.ifc.tx_add(
            struct.pack(
                '<BHLLLHL', ftype, 0x02b0,
                self._emu_timestamp(),
                self.seconds_since_last_sync(),
                self.time_ofs,
                1,  # offset 0x1a
                self.next_pkt_cnt()))
        self.ifc.tx_add(build_msg[0x20:])
        self._finish_send_msg()
        log_lvl = self.log_lvl.get(0x4210, logging.WARNING)
        self.ifc.tx_log(log_lvl, 'Send inv-data:')
        self.ifc.tx_flush()

    '''
    Message handler methods
    '''
    def msg_response(self):
        '''handle a received response from the TSUN cloud'''
        logger.debug("EMU received rsp:")
        _, _, ts, hb = super().msg_response()
        logger.debug(f"EMU ts:{ts} hb:{hb}")
        self.hb_timeout = hb
        self.time_ofs = ts - self._emu_timestamp()
        self.hb_timer.start(self.hb_timeout)

    def msg_unknown(self):
        '''counts a unknown or unexpected message from the TSUN cloud'''
        logger.warning(f"EMU Unknow Msg: ID:{int(self.control):#04x}")
        self.inc_counter('Unknown_Msg')
