# test_with_pytest.py
# import pytest, logging
from app.src.modbus import Modbus


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

