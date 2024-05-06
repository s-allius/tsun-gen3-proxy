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

def test_build_modbus_pdu():
    mb = Modbus()
    pdu = mb.build_msg(1,6,0x2000,0x12)
    assert pdu == b'\x01\x06\x20\x00\x00\x12\x02\x07'
    assert mb.check_crc(pdu)

def test_build_recv():
    mb = TestHelper()
    pdu = mb.build_msg(1,3,0x300e,0x2)
    assert pdu == b'\x01\x03\x30\x0e\x00\x02\xaa\xc8'
    assert mb.check_crc(pdu)
    call = 0
    for key, update in mb.recv_resp(mb.db, b'\x01\x03\x04\x01\x2c\x00\x46\xbb\xf4', 'test'):
        if key == 'grid':
            assert update == True
        elif key == 'inverter':
            assert update == True
        else:
            assert False
        call += 1
    assert 2 == call
