import pytest, json
from app.src.v2.solarman_v5 import SolarmanV5

class MemoryStream(SolarmanV5):
    def __init__(self, msg, chunks = (0,), server_side: bool = True):
        super().__init__(server_side)
        self.__msg = msg
        self.__msg_len = len(msg)
        self.__chunks = chunks
        self.__offs = 0
        self.__chunk_idx = 0
        self.msg_count = 0
        self.addr = 'Test: SrvSide'

    def append_msg(self, msg):
        self.__msg += msg
        self.__msg_len += len(msg)    

    def _read(self) -> int:
        copied_bytes = 0
        try:    
            if (self.__offs < self.__msg_len):
                len = self.__chunks[self.__chunk_idx]
                self.__chunk_idx += 1
                if len!=0:
                    self._recv_buffer += self.__msg[self.__offs:len]
                    copied_bytes = len - self.__offs
                    self.__offs = len
                else:
                    self._recv_buffer += self.__msg[self.__offs:]
                    copied_bytes = self.__msg_len - self.__offs
                    self.__offs = self.__msg_len
        except:
            pass     
        return copied_bytes
    
    def _timestamp(self):
        return 1700260990000
    
    def _SolarmanV5__flush_recv_msg(self) -> None:
        super()._SolarmanV5__flush_recv_msg()
        self.msg_count += 1
        return


def get_sn() -> bytes:
    return b'\xc8\x1e\x4d\x7b'

def get_inv_no() -> bytes:
    return b'T170000000000001'

def get_invalid_sn():
    return b'R170000000000002'


@pytest.fixture
def TestMsg(): # Contact Info message
    msg  = b'\xa5\xd4\x00\x10\x41\x00\x01' +get_sn()  +b'\x02\xba\xd2\x00\x00'
    msg += b'\x19\x00\x00\x00\x00\x00\x00\x00\x05\x3c\x78\x01\x64\x01\x4c\x53'
    msg += b'\x57\x35\x42\x4c\x45\x5f\x31\x37\x5f\x30\x32\x42\x30\x5f\x31\x2e'
    msg += b'\x30\x35\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x40\x2a\x8f\x4f\x51\x54\x31\x39\x32\x2e'
    msg += b'\x31\x36\x38\x2e\x38\x30\x2e\x34\x39\x00\x00\x00\x0f\x00\x01\xb0'
    msg += b'\x02\x0f\x00\xff\x56\x31\x2e\x31\x2e\x30\x30\x2e\x30\x42\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfe\xfe\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x41\x6c\x6c\x69\x75\x73\x2d\x48\x6f'
    msg += b'\x6d\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3c'
    msg += b'\x15'
    return msg

def test_read_message(TestMsg):
    m = MemoryStream(TestMsg, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    # assert m.id_str == b"R170000000000001" 
    assert m.snr == 2068651720
    # assert m.unique_id == None
    # assert int(m.ctrl)==145
    # assert m.msg_id==0 
    assert m.control == 0x4110
    assert m.serial == 0x0100
    assert m.data_len == 0xd4
    assert m._forward_buffer==b''
    m.close()


def test_parse_header(TestMsg):
    i = SolarmanV5(True)
    cnt = 0
    for ctrl, buf in i.parse_header(TestMsg, len(TestMsg)):
        cnt += 1
        assert ctrl == 0x4110
        assert buf == TestMsg[11:-2]
        pass

    assert cnt == 1
    assert i.data_len == 0xd4
    assert i.control == 0x4110
    assert i.serial == 0x0100
    assert i.snr == 2068651720
    assert i.crc == 0x3c
    assert i.stop == 0x15

