# test_with_pytest.py
# import pytest, logging
from app.src.modbus import Modbus
from app.src.infos import Infos

class TestHelper(Modbus):
    def __init__(self):
        super().__init__()
        self.db = Infos()

def test_modbus_crc():
    mb = Modbus()
    assert 0x0b02 == mb._Modbus__calc_crc(b'\x01\x06\x20\x08\x00\x04')
    assert 0 == mb._Modbus__calc_crc(b'\x01\x06\x20\x08\x00\x04\x02\x0b')
    assert mb.check_crc(b'\x01\x06\x20\x08\x00\x04\x02\x0b')

    assert 0xc803 == mb._Modbus__calc_crc(b'\x01\x06\x20\x08\x00\x00')
    assert 0 == mb._Modbus__calc_crc(b'\x01\x06\x20\x08\x00\x00\x03\xc8')
    assert mb.check_crc(b'\x01\x06\x20\x08\x00\x00\x03\xc8')

    assert 0x5c75 == mb._Modbus__calc_crc(b'\x01\x03\x08\x01\x2c\x00\x2c\x02\x2c\x2c\x46')
def test_build_modbus_pdu():
    mb = Modbus()
    pdu = mb.build_msg(1,6,0x2000,0x12)
    assert pdu == b'\x01\x06\x20\x00\x00\x12\x02\x07'
    assert mb.check_crc(pdu)

def test_recv_req_crc():
    mb = Modbus()
    res = mb.recv_req(b'\x01\x06\x20\x00\x00\x12\x02\x08')
    assert not res
    assert mb.last_fcode == 0   
    assert mb.last_reg == 0
    assert mb.last_len == 0
    assert mb.err == 1

def test_recv_req_addr():
    mb = Modbus()
    res = mb.recv_req(b'\x02\x06\x20\x00\x00\x12\x02\x34')
    assert not res
    assert mb.last_fcode == 0   
    assert mb.last_reg == 0
    assert mb.last_len == 0
    assert mb.err == 2

def test_recv_req():
    mb = Modbus()
    res = mb.recv_req(b'\x01\x06\x20\x00\x00\x12\x02\x07')
    assert res
    assert mb.last_fcode == 6
    assert mb.last_reg == 0x2000
    assert mb.last_len == 0x12
    assert mb.err == 0

def test_recv_recv_crc():
    mb = TestHelper()
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
    mb.last_fcode = 3   
    mb.last_reg == 0x300e
    mb.last_len == 2

    call = 0
    for key, update in mb.recv_resp(mb.db, b'\x02\x03\x04\x01\x2c\x00\x46\x88\xf4', 'test'):
        call += 1
    assert mb.err == 2
    assert 0 == call

def test_recv_recv_fcode():
    mb = TestHelper()
    mb.last_fcode = 4   
    mb.last_reg == 0x300e
    mb.last_len == 2

    call = 0
    for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x04\x01\x2c\x00\x46\xbb\xf4', 'test'):
        call += 1
    assert mb.err == 3
    assert 0 == call

def test_recv_recv_len():
    mb = TestHelper()
    mb.last_fcode = 3   
    mb.last_reg == 0x300e
    mb.last_len == 2

    call = 0
    for key, update, _ in mb.recv_resp(mb.db, b'\x01\x03\x04\x01\x2c\x00\x46\xbb\xf4', 'test'):
        call += 1
    assert mb.err == 4
    assert 0 == call

def test_build_recv():
    mb = TestHelper()
    pdu = mb.build_msg(1,3,0x3007,6)
    assert mb.check_crc(pdu)
    assert mb.err == 0
    call = 0
    exp_result = ['v0.0.212', 4.4, 0.7, 0.7, 30]
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

def test_build_long():
    mb = TestHelper()
    pdu = mb.build_msg(1,3,0x3022,4)
    assert mb.check_crc(pdu)
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
