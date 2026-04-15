import pytest
import asyncio

from async_stream import AsyncIfcImpl, StreamPtr
from gen3plus.solarman_v5 import SolarmanV5, SolarmanBase
from gen3plus.solarman_emu import SolarmanEmu
from infos import Infos, Register

from test_solarman import FakeIfc, FakeInverter, MemoryStream, get_sn_int, get_sn, correct_checksum, config_tsun_inv1, msg_modbus_rsp
from test_infos_g3p import str_test_ip, bytes_test_ip


pytest_plugins = ('pytest_asyncio',)

timestamp = 0x3224c8bc

class InvStream(MemoryStream):
    def __init__(self, msg=b''):
        super().__init__(msg)

    def _emu_timestamp(self):
        return timestamp

class CldStream(SolarmanEmu):
    def __init__(self, inv: InvStream, inverter=FakeInverter()):
        _ifc = FakeIfc()
        _ifc.remote.stream = inv
        super().__init__(inverter, ('test.local', 1234), _ifc, server_side=False, client_mode=False)
        self.__msg = b''
        self.__msg_len = 0
        self.__offs = 0
        self.msg_count = 0
        self.msg_recvd = []

    def _emu_timestamp(self):
        return timestamp
    
    def append_msg(self, msg):
        self.__msg += msg
        self.__msg_len += len(msg)    

    def _read(self) -> int:
        copied_bytes = 0
        try:    
            if (self.__offs < self.__msg_len):
                self.ifc.rx_fifo += self.__msg[self.__offs:]
                copied_bytes = self.__msg_len - self.__offs
                self.__offs = self.__msg_len
        except Exception:
            pass   # ignore exceptions here
        return copied_bytes

    def _SolarmanBase__flush_recv_msg(self) -> None:
        self.msg_recvd.append(
            {
                'control': self.control,
                'seq': str(self.seq),
                'data_len': self.data_len
            }
        )
        super()._SolarmanBase__flush_recv_msg()
        self.msg_count += 1

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
def inverter_rsp_msg():  # 0x1210
    msg  = b'\xa5\x0a\x00\x10\x12\x02\02' +get_sn()  +b'\x01\x01'
    msg += b'\x00\x00\x00\x00'
    msg += b'\x3c\x00\x00\x00'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def heartbeat_ind():
    msg  = b'\xa5\x01\x00\x10G\x00\x01\x00\x00\x00\x00\x00Y\x15'
    return msg

@pytest.mark.asyncio(loop_scope="session")
async def test_emu_init_close(my_loop, config_tsun_inv1):
    _ = config_tsun_inv1
    assert asyncio.get_running_loop()
    inv = InvStream()
    cld = CldStream(inv)
    cld.close()


@pytest.mark.asyncio(loop_scope="session")
async def test_emu_start(my_loop, config_tsun_inv1, msg_modbus_rsp, str_test_ip, device_ind_msg):
    _ = config_tsun_inv1
    assert asyncio.get_running_loop()
    inv = InvStream(msg_modbus_rsp)

    assert asyncio.get_running_loop() == inv.mb_timer.loop
    inv.send_start_cmd(get_sn_int(), str_test_ip, True, inv.mb_first_timeout)
    inv.read()         # read complete msg, and dispatch msg
    assert not inv.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert inv.msg_count == 1
    assert inv.control == 0x1510

    cld = CldStream(inv)
    cld.ifc.update_header_cb(inv.ifc.fwd_fifo.peek())
    assert inv.ifc.fwd_fifo.peek() == device_ind_msg
    cld.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_snd_hb(my_loop, config_tsun_inv1, heartbeat_ind):
    _ = config_tsun_inv1
    inv = InvStream()
    cld = CldStream(inv)

    # inv.send_start_cmd(get_sn_int(), str_test_ip, False, inv.mb_first_timeout)
    cld.send_heartbeat_cb(0)
    assert cld.ifc.tx_fifo.peek() == heartbeat_ind
    cld.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_snd_inv_data(my_loop, config_tsun_inv1, inverter_ind_msg, inverter_rsp_msg):
    _ = config_tsun_inv1
    inv = InvStream()
    inv.db.set_db_def_value(Register.INVERTER_STATUS, 1)
    inv.db.set_db_def_value(Register.DETECT_STATUS_1, 2)
    inv.db.set_db_def_value(Register.VERSION, 'V4.0.10')
    inv.db.set_db_def_value(Register.GRID_VOLTAGE, 224.8)
    inv.db.set_db_def_value(Register.GRID_CURRENT, 0.73)
    inv.db.set_db_def_value(Register.GRID_FREQUENCY, 50.05)
    inv.db.set_db_def_value(Register.PROD_COMPL_TYPE, 6)
    assert asyncio.get_running_loop() == inv.mb_timer.loop
    inv.send_start_cmd(get_sn_int(), str_test_ip, False, inv.mb_first_timeout)
    inv.db.set_db_def_value(Register.DATA_UP_INTERVAL, 17)  # set test value

    cld = CldStream(inv)
    cld.time_ofs = 0x33e447a0
    cld.last_sync = cld._emu_timestamp() - 60
    cld.pkt_cnt = 0x802
    assert cld.data_up_inv == 17  # check test value
    cld.data_up_inv = 0.1         # speedup test first data msg
    cld._init_new_client_conn()
    cld.data_up_inv = 0.5         # timeout for second data msg
    await asyncio.sleep(0.2)
    assert cld.ifc.tx_fifo.get() == inverter_ind_msg

    cld.append_msg(inverter_rsp_msg)
    cld.read()         # read complete msg, and dispatch msg

    assert not cld.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert cld.msg_count == 1
    assert cld.header_len==11
    assert cld.snr == 2070233889
    assert cld.unique_id == '2070233889'
    assert cld.msg_recvd[0]['control']==0x1210
    assert cld.msg_recvd[0]['seq']=='02:02'
    assert cld.msg_recvd[0]['data_len']==0x0a
    assert '02b0' == cld.db.get_db_value(Register.SENSOR_LIST, None)
    assert cld.db.stat['proxy']['Unknown_Msg'] == 0

    cld.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_rcv_invalid(my_loop, config_tsun_inv1, inverter_ind_msg, inverter_rsp_msg):
    _ = config_tsun_inv1
    inv = InvStream()
    assert asyncio.get_running_loop() == inv.mb_timer.loop
    inv.send_start_cmd(get_sn_int(), str_test_ip, False, inv.mb_first_timeout)
    inv.db.set_db_def_value(Register.DATA_UP_INTERVAL, 17)  # set test value

    cld = CldStream(inv)
    cld._init_new_client_conn()

    cld.append_msg(inverter_ind_msg)
    cld.read()         # read complete msg, and dispatch msg

    assert not cld.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert cld.msg_count == 1
    assert cld.header_len==11
    assert cld.snr == 2070233889
    assert cld.unique_id == '2070233889'
    assert cld.msg_recvd[0]['control']==0x4210
    assert cld.msg_recvd[0]['seq']=='00:01'
    assert cld.msg_recvd[0]['data_len']==0x199
    assert '02b0' == cld.db.get_db_value(Register.SENSOR_LIST, None)
    assert cld.db.stat['proxy']['Unknown_Msg'] == 1


    cld.close()
