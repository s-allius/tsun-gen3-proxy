import pytest, json
from app.src.gen3plus.solarman_v5 import SolarmanV5
from app.src.config import Config
from app.src.infos import Infos

# initialize the proxy statistics
Infos.static_init()

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
        self.db.stat['proxy']['Invalid_Msg_Format'] = 0


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
    return b'\x21\x43\x65\x7b'

def get_inv_no() -> bytes:
    return b'T170000000000001'

def get_invalid_sn():
    return b'R170000000000002'

def correct_checksum(buf):
    checksum = sum(buf[1:]) & 0xff
    return checksum.to_bytes(length=1)

def incorrect_checksum(buf):
    checksum = (sum(buf[1:])+1) & 0xff
    return checksum.to_bytes(length=1)

@pytest.fixture
def DeviceIndMsg(): # 0x4110
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
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' 
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def InvalidStartByte(): # 0x4110
    msg  = b'\xa4\xd4\x00\x10\x41\x00\x01' +get_sn()  +b'\x02\xba\xd2\x00\x00'
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
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def InvalidStopByte(): # 0x4110
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
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += correct_checksum(msg)
    msg += b'\x14'
    return msg

@pytest.fixture
def InvalidChecksum(): # 0x4110
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
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += incorrect_checksum(msg)
    msg += b'\x15'
    return msg


@pytest.fixture
def ConfigTsunAllowAll():
    Config.config = {'solarman':{'enabled': True}, 'inverters':{'allow_all':True}}

@pytest.fixture
def ConfigNoTsunInv1():
    Config.config = {'solarman':{'enabled': False},'inverters':{'Y170000000000001':{'monitor_sn': 2070233889,'node_id':'inv1','suggested_area':'roof'}}}

@pytest.fixture
def ConfigTsunInv1():
    Config.config = {'solarman':{'enabled': True},'inverters':{'R170000000000001':{'node_id':'inv1','suggested_area':'roof'}}}

def test_read_message(DeviceIndMsg):
    m = MemoryStream(DeviceIndMsg, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == None
    assert m.control == 0x4110
    assert m.serial == 0x0100
    assert m.data_len == 0xd4
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_invalid_start_byte(InvalidStartByte):
    m = MemoryStream(InvalidStartByte, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since start byte is wrong
    assert m.msg_count == 0
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == 0
    assert m.control == 0x4110
    assert m.serial == 0x0100
    assert m.data_len == 0xd4
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 1

    m.close()

def test_invalid_stop_byte(InvalidStopByte):
    m = MemoryStream(InvalidStopByte, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since start byte is wrong
    assert m.msg_count == 1     # msg flush was called
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == 0
    assert m.control == 0x4110
    assert m.serial == 0x0100
    assert m.data_len == 0xd4
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 1
    m.close()

def test_invalid_checksum(InvalidChecksum):
    m = MemoryStream(InvalidChecksum, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since start byte is wrong
    assert m.msg_count == 1     # msg flush was called
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == 0
    assert m.control == 0x4110
    assert m.serial == 0x0100
    assert m.data_len == 0xd4
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 1
    m.close()

def test_read_message_twice(ConfigNoTsunInv1, DeviceIndMsg):
    ConfigNoTsunInv1
    m = MemoryStream(DeviceIndMsg, (0,))
    m.append_msg(DeviceIndMsg)
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == '2070233889'
    assert m.control == 0x4110
    assert m.serial == 0x0100
    assert m.data_len == 0xd4
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 2
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == '2070233889'
    assert m.control == 0x4110
    assert m.serial == 0x0100
    assert m.data_len == 0xd4
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_read_message_in_chunks(DeviceIndMsg):
    m = MemoryStream(DeviceIndMsg, (4,11,0))
    m.read()        # read 4 bytes, header incomplere
    assert not m.header_valid  # must be invalid, since header not complete
    assert m.msg_count == 0
    m.read()        # read missing bytes for complete header
    assert m.header_valid      # must be valid, since header is complete but not the msg
    assert m.msg_count == 0
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == 0 # should be None ?
    assert m.control == 0x4110
    assert m.serial == 0x0100
    assert m.data_len == 0xd4
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.read()    # read rest of message
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_read_message_in_chunks2(DeviceIndMsg):
    m = MemoryStream(DeviceIndMsg, (4,10,0))
    m.read()        # read 4 bytes, header incomplere
    assert not m.header_valid
    assert m.msg_count == 0
    m.read()        # read 6 more bytes, header incomplere
    assert not m.header_valid
    assert m.msg_count == 0
    m.read()        # read rest of message
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == '2070233889'
    assert m.control == 0x4110
    assert m.serial == 0x0100
    assert m.data_len == 0xd4
    assert m.msg_count == 1
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    while m.read(): # read rest of message
        pass
    assert m.msg_count == 1
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()
