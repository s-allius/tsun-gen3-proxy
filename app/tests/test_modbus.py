# test_with_pytest.py
import pytest
import asyncio
from app.src.modbus import Modbus
from app.src.infos import Infos

pytest_plugins = ('pytest_asyncio',)
pytestmark = pytest.mark.asyncio(scope="module")

class TestHelper(Modbus):
    def __init__(self):
        super().__init__(self.send_cb)
        self.db = Infos()
        self.pdu = None
        self.send_calls = 0
    def send_cb(self, pdu: bytearray):
        self.pdu = pdu
        self.send_calls += 1

def test_modbus_crc():
    mb = Modbus(None)
    assert 0x0b02 == mb._Modbus__calc_crc(b'\x01\x06\x20\x08\x00\x04')
    assert 0 == mb._Modbus__calc_crc(b'\x01\x06\x20\x08\x00\x04\x02\x0b')
    assert mb.check_crc(b'\x01\x06\x20\x08\x00\x04\x02\x0b')

    assert 0xc803 == mb._Modbus__calc_crc(b'\x01\x06\x20\x08\x00\x00')
    assert 0 == mb._Modbus__calc_crc(b'\x01\x06\x20\x08\x00\x00\x03\xc8')
    assert mb.check_crc(b'\x01\x06\x20\x08\x00\x00\x03\xc8')

    assert 0x5c75 == mb._Modbus__calc_crc(b'\x01\x03\x08\x01\x2c\x00\x2c\x02\x2c\x2c\x46')
def test_build_modbus_pdu():
    mb = TestHelper()
    mb.build_msg(1,6,0x2000,0x12)
    mb.get_next_req()
    assert mb.pdu == b'\x01\x06\x20\x00\x00\x12\x02\x07'
    assert mb.check_crc(mb.pdu)

def test_recv_req_crc():
    mb = TestHelper()
    mb.recv_req(b'\x01\x06\x20\x00\x00\x12\x02\x08')
    mb.get_next_req()
    assert mb.last_fcode == 0   
    assert mb.last_reg == 0
    assert mb.last_len == 0
    assert mb.err == 1

def test_recv_req_addr():
    mb = TestHelper()
    mb.recv_req(b'\x02\x06\x20\x00\x00\x12\x02\x34')
    mb.get_next_req()
    assert mb.last_addr == 2
    assert mb.last_fcode == 6
    assert mb.last_reg == 0x2000
    assert mb.last_len == 18

def test_recv_req():
    mb = TestHelper()
    mb.recv_req(b'\x01\x06\x20\x00\x00\x12\x02\x07')
    mb.get_next_req()
    assert mb.last_fcode == 6
    assert mb.last_reg == 0x2000
    assert mb.last_len == 0x12
    assert mb.err == 0

def test_recv_recv_crc():
    mb = TestHelper()
    mb.req_pend = True
    mb.last_fcode = 3   
    mb.last_reg == 0x300e
    mb.last_len == 2

    call = 0
    for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x04\x01\x2c\x00\x46\xbb\xf3', 'test'):
        call += 1
    assert mb.err == 1
    assert 0 == call

def test_recv_recv_addr():
    mb = TestHelper()
    mb.req_pend = True
    mb.last_fcode = 3   
    mb.last_reg == 0x300e
    mb.last_len == 2

    call = 0
    for key, update in mb.recv_resp(mb.db, b'\x02\x03\x04\x01\x2c\x00\x46\x88\xf4', 'test'):
        call += 1
    assert mb.err == 2
    assert 0 == call
    assert mb.que.qsize() == 0
    mb.stop_timer()
    assert not mb.req_pend

def test_recv_recv_fcode():
    mb = TestHelper()
    mb.build_msg(1,4,0x300e,2)
    assert mb.que.qsize() == 0
    assert mb.req_pend
   
    call = 0
    for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x04\x01\x2c\x00\x46\xbb\xf4', 'test'):
        call += 1

    assert mb.err == 3
    assert 0 == call
    assert mb.que.qsize() == 0
    mb.stop_timer()
    assert not mb.req_pend

def test_recv_recv_len():
    mb = TestHelper()
    mb.build_msg(1,3,0x300e,3)
    assert mb.que.qsize() == 0
    assert mb.req_pend
    assert mb.last_len == 3
    call = 0
    for key, update, _ in mb.recv_resp(mb.db, b'\x01\x03\x04\x01\x2c\x00\x46\xbb\xf4', 'test'):
        call += 1

    assert mb.err == 4
    assert 0 == call
    assert mb.que.qsize() == 0
    mb.stop_timer()
    assert not mb.req_pend

def test_build_recv():
    mb = TestHelper()
    mb.build_msg(1,3,0x3007,6)
    assert mb.que.qsize() == 0
    assert mb.req_pend

    call = 0
    exp_result = ['V0.0.212', 4.4, 0.7, 0.7, 30]
    for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x0c\x01\x2c\x00\x2c\x00\x2c\x00\x46\x00\x46\x00\x46\x32\xc8', 'test'):
        if key == 'grid':
            assert update == True
        elif key == 'inverter':
            assert update == True
        elif key == 'env':
            assert update == True
        else:
            assert False
        assert exp_result[call] == val
        call += 1
    assert 0 == mb.err
    assert 5 == call
            
    mb.req_pend = True
    call = 0
    for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x0c\x01\x2c\x00\x2c\x00\x2c\x00\x46\x00\x46\x00\x46\x32\xc8', 'test'):
        if key == 'grid':
            assert update == False
        elif key == 'inverter':
            assert update == False
        elif key == 'env':
            assert update == False
        else:
            assert False
        assert exp_result[call] == val
        call += 1

    assert 0 == mb.err
    assert 5 == call
    assert mb.que.qsize() == 0
    mb.stop_timer()
    assert not mb.req_pend

def test_build_long():
    mb = TestHelper()
    mb.build_msg(1,3,0x3022,4)
    assert mb.que.qsize() == 0
    assert mb.req_pend
    assert mb.last_addr == 1
    assert mb.last_fcode == 3
    assert mb.err == 0
    call = 0
    exp_result = [3.0, 28841.4, 113.34]
    for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x08\x01\x2c\x00\x2c\x02\x2c\x2c\x46\x75\x5c', 'test'):
        if key == 'input':
            assert update == True
            assert exp_result[call] == val
        else:
            assert False
        call += 1

    assert 0 == mb.err
    assert 3 == call
    assert mb.que.qsize() == 0
    mb.stop_timer()
    assert not mb.req_pend

def test_queue():
    mb = TestHelper()
    mb.build_msg(1,3,0x3022,4)
    assert mb.que.qsize() == 0
    assert mb.req_pend

    assert mb.send_calls == 1
    assert mb.pdu == b'\x01\x030"\x00\x04\xeb\x03'
    mb.pdu = None
    mb.get_next_req()
    assert mb.send_calls == 1
    assert mb.pdu == None

    assert mb.que.qsize() == 0
    mb.stop_timer()
    assert not mb.req_pend

def test_queue2():
    mb = TestHelper()
    mb.build_msg(1,3,0x3007,6)
    mb.build_msg(1,6,0x2008,4)
    assert mb.que.qsize() == 1
    assert mb.req_pend

    assert mb.send_calls == 1
    assert mb.pdu == b'\x01\x030\x07\x00\x06{\t'
    mb.get_next_req()
    assert mb.send_calls == 1
    call = 0
    exp_result = ['V0.0.212', 4.4, 0.7, 0.7, 30]
    for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x0c\x01\x2c\x00\x2c\x00\x2c\x00\x46\x00\x46\x00\x46\x32\xc8', 'test'):
        if key == 'grid':
            assert update == True
        elif key == 'inverter':
            assert update == True
        elif key == 'env':
            assert update == True
        else:
            assert False
        assert exp_result[call] == val
        call += 1
    assert 0 == mb.err
    assert 5 == call

    assert mb.send_calls == 2
    assert mb.pdu == b'\x01\x06\x20\x08\x00\x04\x02\x0b'

    for key, update, val in mb.recv_resp(mb.db, b'\x01\x06\x20\x08\x00\x04\x02\x0b', 'test'):
        pass

    assert mb.que.qsize() == 0
    assert not mb.req_pend


@pytest.mark.asyncio
async def test_timeout():
    assert asyncio.get_running_loop()
    mb = TestHelper()
    assert asyncio.get_running_loop() == mb.loop
    mb.build_msg(1,3,0x3007,6)
    mb.build_msg(1,6,0x2008,4)
    assert mb.que.qsize() == 1
    assert mb.req_pend

    assert mb.send_calls == 1
    assert mb.pdu == b'\x01\x030\x07\x00\x06{\t'
    await asyncio.sleep(1.1)    # wait for first timeout and next pdu
    assert mb.req_pend
    assert mb.send_calls == 2
    assert mb.pdu == b'\x01\x06\x20\x08\x00\x04\x02\x0b'
    await asyncio.sleep(1.1)    # wait for second timout

    assert not mb.req_pend
    assert mb.que.qsize() == 0
