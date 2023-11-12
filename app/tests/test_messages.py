# test_with_pytest.py
import pytest, logging
from app.src.messages import Message, Control
from app.src.config import Config
from app.src.infos import Infos

# initialize the proxy statistics
Infos.static_init()

tracer = logging.getLogger('tracer')
    
class MemoryStream(Message):
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
    
    
    def _Message__flush_recv_msg(self) -> None:
        super()._Message__flush_recv_msg()
        self.msg_count += 1
        return
    

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
    return b'\x00\x00\x00\x2c\x10R170000000000001\x91\x00\x08solarhub\x0fsolarhub\x40123456\x00\x00\x00\x2c\x10R170000000000002\x91\x00\x08solarhub\x0fsolarhub\x40123456'

@pytest.fixture
def MsgContactResp(): # Contact Response message
    return b'\x00\x00\x00\x14\x10R170000000000001\x99\x00\x01'

@pytest.fixture
def MsgContactResp2(): # Contact Response message
    return b'\x00\x00\x00\x14\x10R170000000000002\x99\x00\x01'

@pytest.fixture
def MsgContactInvalid(): # Contact Response message
    return b'\x00\x00\x00\x14\x10R170000000000001\x93\x00\x01'

@pytest.fixture
def MsgGetTime(): # Get Time Request message
    return b'\x00\x00\x00\x13\x10R170000000000001\x91\x22'           

@pytest.fixture
def MsgTimeResp(): # Get Time Resonse message
    return b'\x00\x00\x00\x1b\x10R170000000000001\x99\x22\x00\x00\x01\x89\xc6\x63\x4d\x80'

@pytest.fixture
def MsgTimeInvalid(): # Get Time Request message
    return b'\x00\x00\x00\x13\x10R170000000000001\x94\x22'           

@pytest.fixture
def MsgControllerInd(): # Data indication from the controller
    msg  =  b'\x00\x00\x01\x2f\x10R170000000000001\x91\x71\x0e\x10\x00\x00\x10R170000000000001'
    msg +=  b'\x01\x00\x00\x01\x89\xc6\x63\x55\x50'
    msg +=  b'\x00\x00\x00\x15\x00\x09\x2b\xa8\x54\x10\x52\x53\x57\x5f\x34\x30\x30\x5f\x56\x31\x2e\x30\x30\x2e\x30\x36\x00\x09\x27\xc0\x54\x06\x52\x61\x79\x6d\x6f'
    msg +=  b'\x6e\x00\x09\x2f\x90\x54\x0b\x52\x53\x57\x2d\x31\x2d\x31\x30\x30\x30\x31\x00\x09\x5a\x88\x54\x0f\x74\x2e\x72\x61\x79\x6d\x6f\x6e\x69\x6f\x74\x2e\x63\x6f\x6d\x00\x09\x5a\xec\x54'
    msg +=  b'\x1c\x6c\x6f\x67\x67\x65\x72\x2e\x74\x61\x6c\x65\x6e\x74\x2d\x6d\x6f\x6e\x69\x74\x6f\x72\x69\x6e\x67\x2e\x63\x6f\x6d\x00\x0d\x00\x20\x49\x00\x00\x00\x01\x00\x0c\x35\x00\x49\x00'
    msg +=  b'\x00\x00\x64\x00\x0c\x96\xa8\x49\x00\x00\x00\x1d\x00\x0c\x7f\x38\x49\x00\x00\x00\x01\x00\x0c\xfc\x38\x49\x00\x00\x00\x01\x00\x0c\xf8\x50\x49\x00\x00\x01\x2c\x00\x0c\x63\xe0\x49'
    msg +=  b'\x00\x00\x00\x00\x00\x0c\x67\xc8\x49\x00\x00\x00\x00\x00\x0c\x50\x58\x49\x00\x00\x00\x01\x00\x09\x5e\x70\x49\x00\x00\x13\x8d\x00\x09\x5e\xd4\x49\x00\x00\x13\x8d\x00\x09\x5b\x50'
    msg +=  b'\x49\x00\x00\x00\x02\x00\x0d\x04\x08\x49\x00\x00\x00\x00\x00\x07\xa1\x84\x49\x00\x00\x00\x01\x00\x0c\x50\x59\x49\x00\x00\x00\x4c\x00\x0d\x1f\x60\x49\x00\x00\x00\x00'
    return msg

@pytest.fixture
def MsgControllerAck(): # Get Time Request message
    return b'\x00\x00\x00\x14\x10R170000000000001\x99\x71\x01'

@pytest.fixture
def MsgControllerInvalid(): # Get Time Request message
    return b'\x00\x00\x00\x14\x10R170000000000001\x92\x71\x01'

@pytest.fixture
def MsgInverterInd(): # Data indication from the controller
    msg  =  b'\x00\x00\x00\x8b\x10R170000000000001\x91\x04\x01\x90\x00\x01\x10R170000000000001'
    msg +=  b'\x01\x00\x00\x01\x89\xc6\x63\x61\x08'
    msg +=  b'\x00\x00\x00\x06\x00\x00\x00\x0a\x54\x08\x4d\x69\x63\x72\x6f\x69\x6e\x76\x00\x00\x00\x14\x54\x04\x54\x53\x55\x4e\x00\x00\x00\x1E\x54\x07\x56\x35\x2e\x30\x2e\x31\x31\x00\x00\x00\x28'
    msg +=  b'\x54\x10\x54\x31\x37\x45\x37\x33\x30\x37\x30\x32\x31\x44\x30\x30\x36\x41\x00\x00\x00\x32\x54\x0a\x54\x53\x4f\x4c\x2d\x4d\x53\x36\x30\x30\x00\x00\x00\x3c\x54\x05\x41\x2c\x42\x2c\x43'
    return msg

@pytest.fixture
def MsgInverterAck(): # Get Time Request message
    return b'\x00\x00\x00\x14\x10R170000000000001\x99\x04\x01'

@pytest.fixture
def MsgInverterInvalid(): # Get Time Request message
    return b'\x00\x00\x00\x14\x10R170000000000001\x92\x04\x01'

@pytest.fixture
def MsgUnknown(): # Get Time Request message
    return b'\x00\x00\x00\x17\x10R170000000000001\x91\x17\x01\x02\x03\x04'

@pytest.fixture
def MsgGetTime(): # Get Time Request message
    return b'\x00\x00\x00\x13\x10R170000000000001\x91\x22'           


@pytest.fixture
def MsgTimeResp(): # Get Time Resonse message
    return b'\x00\x00\x00\x1b\x10R170000000000001\x99\x22\x00\x00\x01\x89\xc6\x63\x4d\x80'

@pytest.fixture
def ConfigTsunAllowAll():
    Config.config = {'tsun':{'enabled': True}, 'inverters':{'allow_all':True}}

@pytest.fixture
def ConfigNoTsunInv1():
    Config.config = {'tsun':{'enabled': False},'inverters':{'R170000000000001':{'node_id':'inv1','suggested_area':'roof'}}}

@pytest.fixture
def ConfigTsunInv1():
    Config.config = {'tsun':{'enabled': True},'inverters':{'R170000000000001':{'node_id':'inv1','suggested_area':'roof'}}}

def test_read_message(MsgContactInfo):
    m = MemoryStream(MsgContactInfo, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == None
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==23
    assert m.data_len==25
    assert m._forward_buffer==b''
    m.close()

def test_read_message_twice(ConfigNoTsunInv1, MsgInverterInd):
    ConfigNoTsunInv1
    m = MemoryStream(MsgInverterInd, (0,))
    m.append_msg(MsgInverterInd)
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==4
    assert m.header_len==23
    assert m.data_len==120
    assert m._forward_buffer==b''
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 2
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==4
    assert m.header_len==23
    assert m.data_len==120
    assert m._forward_buffer==b''
    m.close()
 
def test_read_message_long_id(MsgContactInfo_LongId):
    m = MemoryStream(MsgContactInfo_LongId, (23,24))
    m.read()        # read 23 bytes, one is missing
    assert not m.header_valid  # must be invalid, since header not complete
    assert m.msg_count == 0
    m.read()        # read the missing byte
    assert m.header_valid      # must be valid, since header is complete but not the msg
    assert m.msg_count == 0
    assert m.id_str == b"R1700000000000011" 
    assert m.unique_id == 0
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==24
    assert m.data_len==25
    m.read()        # try to read rest of message, but there is no chunk available
    assert m.header_valid      # must be valid, since header is complete but not the msg
    assert m.msg_count == 0
    m.close()
    

def test_read_message_in_chunks(MsgContactInfo):
    m = MemoryStream(MsgContactInfo, (4,23,0))
    m.read()        # read 4 bytes, header incomplere
    assert not m.header_valid  # must be invalid, since header not complete
    assert m.msg_count == 0
    m.read()        # read missing bytes for complete header
    assert m.header_valid      # must be valid, since header is complete but not the msg
    assert m.msg_count == 0
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 0
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==23
    assert m.data_len==25
    m.read()    # read rest of message
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    m.close()
    
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
    assert m.unique_id == None
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.msg_count == 1
    while m.read(): # read rest of message
        pass
    assert m.msg_count == 1
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    m.close()

def test_read_two_messages(ConfigTsunAllowAll, Msg2ContactInfo,MsgContactResp,MsgContactResp2):
    ConfigTsunAllowAll
    m = MemoryStream(Msg2ContactInfo, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==23
    assert m.data_len==25
    assert m._forward_buffer==b''
    assert m._send_buffer==MsgContactResp
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0

    m._send_buffer = bytearray(0) # clear send buffer for next test
    m._init_new_client_conn(b'solarhub', b'solarhub@123456')
    assert m._send_buffer==b'\x00\x00\x00,\x10R170000000000001\x91\x00\x08solarhub\x0fsolarhub@123456'

    m._send_buffer = bytearray(0) # clear send buffer for next test
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 2
    assert m.id_str == b"R170000000000002" 
    assert m.unique_id == 'R170000000000002'
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==23
    assert m.data_len==25
    assert m._forward_buffer==b''
    assert m._send_buffer==MsgContactResp2
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0

    m._send_buffer = bytearray(0) # clear send buffer for next test
    m._init_new_client_conn(b'solarhub', b'solarhub@123456')
    assert m._send_buffer==b'\x00\x00\x00,\x10R170000000000002\x91\x00\x08solarhub\x0fsolarhub@123456'
    m.close()

def test_msg_contact_resp(ConfigTsunInv1, MsgContactResp):
    ConfigTsunInv1
    m = MemoryStream(MsgContactResp, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==153
    assert m.msg_id==0
    assert m.header_len==23
    assert m.data_len==1
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_contact_invalid(ConfigTsunInv1, MsgContactInvalid):
    ConfigTsunInv1
    m = MemoryStream(MsgContactInvalid, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==147
    assert m.msg_id==0
    assert m.header_len==23
    assert m.data_len==1
    assert m._forward_buffer==MsgContactInvalid
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()

def test_msg_get_time(ConfigTsunInv1, MsgGetTime):
    ConfigTsunInv1
    m = MemoryStream(MsgGetTime, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==34
    assert m.header_len==23
    assert m.data_len==0
    assert m._forward_buffer==MsgGetTime
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_time_resp(ConfigNoTsunInv1, MsgTimeResp):
    ConfigNoTsunInv1
    m = MemoryStream(MsgTimeResp, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==153
    assert m.msg_id==34
    assert m.header_len==23
    assert m.data_len==8
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_time_invalid(ConfigTsunInv1, MsgTimeInvalid):
    ConfigTsunInv1
    m = MemoryStream(MsgTimeInvalid, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==148
    assert m.msg_id==34
    assert m.header_len==23
    assert m.data_len==0
    assert m._forward_buffer==MsgTimeInvalid
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()


def test_msg_cntrl_ind(ConfigTsunInv1, MsgControllerInd, MsgControllerAck):
    ConfigTsunInv1
    m = MemoryStream(MsgControllerInd, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==113
    assert m.header_len==23
    assert m.data_len==284
    assert m._forward_buffer==MsgControllerInd
    assert m._send_buffer==MsgControllerAck
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_cntrl_ack(ConfigTsunInv1, MsgControllerAck):
    ConfigTsunInv1
    m = MemoryStream(MsgControllerAck, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==153
    assert m.msg_id==113
    assert m.header_len==23
    assert m.data_len==1
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_cntrl_invalid(ConfigTsunInv1, MsgControllerInvalid):
    ConfigTsunInv1
    m = MemoryStream(MsgControllerInvalid, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==146
    assert m.msg_id==113
    assert m.header_len==23
    assert m.data_len==1
    assert m._forward_buffer==MsgControllerInvalid
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()

def test_msg_inv_ind(ConfigTsunInv1, MsgInverterInd, MsgInverterAck):
    ConfigTsunInv1
    tracer.setLevel(logging.DEBUG)
    m = MemoryStream(MsgInverterInd, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==4
    assert m.header_len==23
    assert m.data_len==120
    assert m._forward_buffer==MsgInverterInd
    assert m._send_buffer==MsgInverterAck
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()
        
def test_msg_inv_ack(ConfigTsunInv1, MsgInverterAck):
    ConfigTsunInv1
    tracer.setLevel(logging.ERROR)

    m = MemoryStream(MsgInverterAck, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==153
    assert m.msg_id==4
    assert m.header_len==23
    assert m.data_len==1
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_inv_invalid(ConfigTsunInv1, MsgInverterInvalid):
    ConfigTsunInv1
    m = MemoryStream(MsgInverterInvalid, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==146
    assert m.msg_id==4
    assert m.header_len==23
    assert m.data_len==1
    assert m._forward_buffer==MsgInverterInvalid
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()

def test_msg_unknown(ConfigTsunInv1, MsgUnknown):
    ConfigTsunInv1
    m = MemoryStream(MsgUnknown, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==23
    assert m.header_len==23
    assert m.data_len==4
    assert m._forward_buffer==MsgUnknown
    assert m._send_buffer==b''
    assert 1 == m.db.stat['proxy']['Unknown_Msg']
    m.close()

def test_ctrl_byte():
    c = Control(0x91)
    assert c.is_ind()
    assert not c.is_resp()    
    c = Control(0x99)
    assert not c.is_ind()
    assert c.is_resp()    

    
def test_msg_iterator():
    m1 = Message(server_side=True)
    m2 = Message(server_side=True)
    m3 = Message(server_side=True)
    m3.close()
    del m3
    test1 = 0
    test2 = 0
    for key in Message:
        if key == m1:
            test1+=1
        elif key == m2:
            test2+=1
        else:
            assert False
    assert test1 == 1
    assert test2 == 1

def test_proxy_counter():
    m = Message(server_side=True)
    assert m.new_data == {}
    m.db.stat['proxy']['Unknown_Msg'] = 0
    m.new_stat_data['proxy'] =  False

    m.inc_counter('Unknown_Msg')
    assert m.new_data == {}
    assert m.new_stat_data == {'proxy': True}
    assert 1 == m.db.stat['proxy']['Unknown_Msg']

    m.new_stat_data['proxy'] =  False
    m.dec_counter('Unknown_Msg')
    assert m.new_data == {}
    assert m.new_stat_data == {'proxy': True}
    assert 0 == m.db.stat['proxy']['Unknown_Msg']
    m.close()
