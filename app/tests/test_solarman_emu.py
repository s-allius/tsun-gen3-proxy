import pytest
import struct
import time
import asyncio
import logging
import random
from math import isclose
from app.src.async_stream import AsyncIfcImpl, StreamPtr
from app.src.gen3plus.solarman_v5 import SolarmanV5, SolarmanBase
from app.src.gen3plus.solarman_emu import SolarmanEmu
from app.src.config import Config
from app.src.infos import Infos, Register
from app.src.modbus import Modbus
from app.src.messages import State, Message
from app.tests.test_solarman import get_sn_int, get_sn, correct_checksum, config_tsun_inv1
from app.tests.test_infos_g3p import str_test_ip, bytes_test_ip

timestamp = 0x3224c8bc

class FakeIfc(AsyncIfcImpl):
    def __init__(self):
        super().__init__()
        self.remote = StreamPtr(None)

    async def create_remote(self):
        await asyncio.sleep(0)

class InvStream(SolarmanV5):
    def __init__(self):
        _ifc = FakeIfc()
        super().__init__(('test.local', 1234), _ifc, server_side=True, client_mode=False)

    def _emu_timestamp(self):
        return timestamp

class CldStream(SolarmanEmu):
    def __init__(self, inv: InvStream):
        _ifc = FakeIfc()
        _ifc.remote.stream = inv
        super().__init__(('test.local', 1234), _ifc, server_side=False, client_mode=False)

    def _emu_timestamp(self):
        return timestamp

@pytest.fixture
def device_ind_msg(bytes_test_ip): # 0x4110
    msg  = b'\xa5\xd4\x00\x10\x41\x00\x01' +get_sn()  +b'\x02\xbc\xc8\x24\x32'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x05\x3c\x78\x01\x00\x01\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + bytes_test_ip
    msg += b'\x0f\x00\x01\xb0'
    msg += b'\x02\x0f\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfe\xfe\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def inverter_ind_msg():  # 0x4210
    msg  = b'\xa5\x99\x01\x10\x42\x00\x01' +get_sn()  +b'\x01\xb0\x02\xbc\xc8'
    msg += b'\x24\x32\x3c\x00\x00\x00\xa0\x47\xe4\x33\x01\x00\x03\x08\x00\x00'
    msg += b'\x59\x31\x37\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x31'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x01\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x40\x10\x08\xc8\x00\x49\x13\x8d\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00'
    msg += b'\x04\x00\x00\x01\xff\xff\x00\x01\x00\x06\x00\x68\x00\x68\x05\x00'
    msg += b'\x09\xcd\x07\xb6\x13\x9c\x13\x24\x00\x01\x07\xae\x04\x0f\x00\x41'
    msg += b'\x00\x0f\x0a\x64\x0a\x64\x00\x06\x00\x06\x09\xf6\x12\x8c\x12\x8c'
    msg += b'\x00\x10\x00\x10\x14\x52\x14\x52\x00\x10\x00\x10\x01\x51\x00\x05'
    msg += b'\x00\x00\x00\x01\x13\x9c\x0f\xa0\x00\x4e\x00\x66\x03\xe8\x04\x00'
    msg += b'\x09\xce\x07\xa8\x13\x9c\x13\x26\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x04\x00\x04\x00\x00\x00\x00\x00\xff\xff\x00\x00'
    msg += b'\x00\x00\x00\x00'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def heartbeat_ind():
    msg  = b'\xa5\x01\x00\x10G\x00\x01\x00\x00\x00\x00\x00Y\x15'
    return msg

def test_emu_init_close():
    # received a message with wrong start byte plus an valid message
    # the complete receive buffer must be cleared to 
    # find the next valid message
    inv = InvStream()
    cld = CldStream(inv)
    cld.close()


@pytest.mark.asyncio
async def test_emu_start(config_tsun_inv1, str_test_ip, device_ind_msg):
    _ = config_tsun_inv1
    assert asyncio.get_running_loop()
    inv = InvStream()

    assert asyncio.get_running_loop() == inv.mb_timer.loop
    await inv.send_start_cmd(get_sn_int(), str_test_ip, False, inv.mb_first_timeout)
    inv.establish_emu()

    cld = CldStream(inv)
    cld.ifc.update_header_cb(inv.ifc.fwd_fifo.peek())
    assert inv.ifc.fwd_fifo.peek() == device_ind_msg
    cld.close()

def test_snd_hb(config_tsun_inv1, heartbeat_ind):
    _ = config_tsun_inv1
    inv = InvStream()
    cld = CldStream(inv)

    # await inv.send_start_cmd(get_sn_int(), str_test_ip, False, inv.mb_first_timeout)
    cld.send_heartbeat_cb(0)
    assert cld.ifc.tx_fifo.peek() == heartbeat_ind
    cld.close()

@pytest.mark.asyncio
async def test_snd_inv_data(config_tsun_inv1, inverter_ind_msg):
    _ = config_tsun_inv1
    inv = InvStream()
    inv.db.set_db_def_value(Register.INVERTER_STATUS, 1)
    inv.db.set_db_def_value(Register.DETECT_STATUS_1, 2)
    inv.db.set_db_def_value(Register.VERSION, 'V4.0.10')
    inv.db.set_db_def_value(Register.GRID_VOLTAGE, 224.8)
    inv.db.set_db_def_value(Register.GRID_CURRENT, 0.73)
    inv.db.set_db_def_value(Register.GRID_FREQUENCY, 50.05)
    assert asyncio.get_running_loop() == inv.mb_timer.loop
    await inv.send_start_cmd(get_sn_int(), str_test_ip, False, inv.mb_first_timeout)
    # inv.db.set_db_def_value(Register.DATA_UP_INTERVAL, 0.1)

    cld = CldStream(inv)
    cld.time_ofs = 0x33e447a0
    cld.pkt_cnt = 0x802
    cld.send_data_cb(0)
    assert cld.ifc.tx_fifo.peek() == inverter_ind_msg
    cld.close()
