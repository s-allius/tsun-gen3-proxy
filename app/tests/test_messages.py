# test_with_pytest.py
import pytest
from app.src.messages import Message, Control
from app.src.config import Config
from app.src.infos import Infos

# initialize the proxy statistics
Infos.static_init()

class MemoryStream(Message):
    def __init__(self, msg, chunks = (0,)):
        super().__init__()
        self.__msg = msg
        self.__msg_len = len(msg)
        self.__chunks = chunks
        self.__offs = 0
        self.__chunk_idx = 0
        self.msg_count = 0
        self.server_side = False
        self.addr = 'Test: SrvSide'

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
    
    
    def _Message__flush_recv_msg(self) -> None:
        super()._Message__flush_recv_msg()
        self.msg_count += 1
        return
    
    def __del__ (self):
        super().__del__()


@pytest.fixture
def MsgContactInfo(): # Contact Info message
    Config.config = {'tsun':{'enabled': True}}
    return b'\x00\x00\x00\x2c\x10R170000000000001\x91\x00\x08solarhub\x0fsolarhub\x40123456'

@pytest.fixture
def MsgContactInfo_LongId():  # Contact Info message with longer ID
    Config.config = {'tsun':{'enabled': True}}
    return b'\x00\x00\x00\x2d\x11R1700000000000011\x91\x00\x08solarhub\x0fsolarhub\x40123456'

@pytest.fixture
def Msg2ContactInfo(): # two Contact Info messages
    Config.config = {'tsun':{'enabled': True}}
    return b'\x00\x00\x00\x2c\x10R170000000000001\x91\x00\x08solarhub\x0fsolarhub\x40123456\x00\x00\x00\x2c\x10R170000000000002\x91\x00\x08solarhub\x0fsolarhub\x40123456'




def test_read_message(MsgContactInfo):
    m = MemoryStream(MsgContactInfo, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==23
    assert m.data_len==25

 
def test_read_message_long_id(MsgContactInfo_LongId):
    m = MemoryStream(MsgContactInfo_LongId, (23,24))
    m.read()        # read 23 bytes, one is missing
    assert not m.header_valid  # must be invalid, since header not complete
    assert m.msg_count == 0
    m.read()        # read the missing byte
    assert m.header_valid      # must be valid, since header is complete but not the msg
    assert m.msg_count == 0
    assert m.id_str == b"R1700000000000011" 
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==24
    assert m.data_len==25
    m.read()        # try to read rest of message, but there is no chunk available
    assert m.header_valid      # must be valid, since header is complete but not the msg
    assert m.msg_count == 0
    

def test_read_message_in_chunks(MsgContactInfo):
    m = MemoryStream(MsgContactInfo, (4,23,0))
    m.read()        # read 4 bytes, header incomplere
    assert not m.header_valid  # must be invalid, since header not complete
    assert m.msg_count == 0
    m.read()        # read missing bytes for complete header
    assert m.header_valid      # must be valid, since header is complete but not the msg
    assert m.msg_count == 0
    assert m.id_str == b"R170000000000001" 
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==23
    assert m.data_len==25
    m.read()    # read rest of message
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    
def test_read_message_in_chunks2(MsgContactInfo):
    m = MemoryStream(MsgContactInfo, (4,10,0))
    m.read()        # read 4 bytes, header incomplere
    assert not m.header_valid
    assert m.msg_count == 0
    m.read()        # read 6 more bytes, header incomplere
    assert not m.header_valid
    assert m.msg_count == 0
    m.read()        # read rest of message
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.header_len==23
    assert m.data_len==25
    assert m.id_str == b"R170000000000001" 
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.msg_count == 1
    while m.read(): # read rest of message
        pass
    assert m.msg_count == 1
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed

def test_read_two_messages(Msg2ContactInfo):
    m = MemoryStream(Msg2ContactInfo, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==23
    assert m.data_len==25
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 2
    assert m.id_str == b"R170000000000002" 
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==23
    assert m.data_len==25

def test_ctrl_byte():
    c = Control(0x91)
    assert c.is_ind()
    assert not c.is_resp()    
    c = Control(0x99)
    assert not c.is_ind()
    assert c.is_resp()    

    
