# test_with_pytest.py
import pytest, logging
from app.src.gen3.talent import Talent, Control
from app.src.config import Config
from app.src.infos import Infos, Register
from app.src.modbus import Modbus
from app.src.messages import State

 
pytest_plugins = ('pytest_asyncio',)

# initialize the proxy statistics
Infos.static_init()

tracer = logging.getLogger('tracer')


class Writer():
    def __init__(self):
        self.sent_pdu = b''

    def write(self, pdu: bytearray):
        self.sent_pdu = pdu

class MemoryStream(Talent):
    def __init__(self, msg, chunks = (0,), server_side: bool = True):
        super().__init__(server_side)
        if server_side:
            self.mb.timeout = 1   # overwrite for faster testing
        self.writer = Writer()
        self.__msg = msg
        self.__msg_len = len(msg)
        self.__chunks = chunks
        self.__offs = 0
        self.__chunk_idx = 0
        self.msg_count = 0
        self.addr = 'Test: SrvSide'
        self.send_msg_ofs = 0
        self.test_exception_async_write = False

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
        # return 1700260990000
        return 1691246944000
    
    def createClientStream(self, msg, chunks = (0,)):
        c = MemoryStream(msg, chunks, False)
        self.remoteStream = c
        c. remoteStream = self
        return c

    def _Talent__flush_recv_msg(self) -> None:
        super()._Talent__flush_recv_msg()
        self.msg_count += 1
        return
    
    async def async_write(self, headline=''):
        if self.test_exception_async_write:
            raise RuntimeError("Peer closed.")

    

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
    return b'\x00\x00\x00\x14\x10R170000000000001\x91\x00\x01'

@pytest.fixture
def MsgContactResp2(): # Contact Response message
    return b'\x00\x00\x00\x14\x10R170000000000002\x91\x00\x01'

@pytest.fixture
def MsgContactInvalid(): # Contact Response message
    return b'\x00\x00\x00\x14\x10R170000000000001\x93\x00\x01'

@pytest.fixture
def MsgGetTime(): # Get Time Request message
    return b'\x00\x00\x00\x13\x10R170000000000001\x91\x22'           

@pytest.fixture
def MsgTimeResp(): # Get Time Resonse message
    return b'\x00\x00\x00\x1b\x10R170000000000001\x91\x22\x00\x00\x01\x89\xc6\x63\x4d\x80'

@pytest.fixture
def MsgTimeRespInv(): # Get Time Resonse message
    return b'\x00\x00\x00\x17\x10R170000000000001\x91\x22\x00\x00\x01\x89'

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
def MsgControllerIndTsOffs(): # Data indication from the controller - offset 0x1000
    msg  =  b'\x00\x00\x01\x2f\x10R170000000000001\x91\x71\x0e\x10\x00\x00\x10R170000000000001'
    msg +=  b'\x01\x00\x00\x01\x89\xc6\x63\x45\x50'
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
    msg +=  b'\x54\x10T170000000000001\x00\x00\x00\x32\x54\x0a\x54\x53\x4f\x4c\x2d\x4d\x53\x36\x30\x30\x00\x00\x00\x3c\x54\x05\x41\x2c\x42\x2c\x43'
    return msg

@pytest.fixture
def MsgInverterIndTsOffs(): # Data indication from the controller + offset 256
    msg  =  b'\x00\x00\x00\x8b\x10R170000000000001\x91\x04\x01\x90\x00\x01\x10R170000000000001'
    msg +=  b'\x01\x00\x00\x01\x89\xc6\x63\x62\x08'
    msg +=  b'\x00\x00\x00\x06\x00\x00\x00\x0a\x54\x08\x4d\x69\x63\x72\x6f\x69\x6e\x76\x00\x00\x00\x14\x54\x04\x54\x53\x55\x4e\x00\x00\x00\x1E\x54\x07\x56\x35\x2e\x30\x2e\x31\x31\x00\x00\x00\x28'
    msg +=  b'\x54\x10T170000000000001\x00\x00\x00\x32\x54\x0a\x54\x53\x4f\x4c\x2d\x4d\x53\x36\x30\x30\x00\x00\x00\x3c\x54\x05\x41\x2c\x42\x2c\x43'
    return msg

@pytest.fixture
def MsgInverterIndNew(): # Data indication from DSP V5.0.17
    msg =  b'\x00\x00\x04\xa0\x10R170000000000001\x91\x04\x01\x90\x00\x01\x10R170000000000001'
    msg += b'\x01\x00\x00\x01'
    msg += b'\x90\x31\x4d\x68\x78\x00\x00\x00\xa3\x00\x00\x00\x00\x53\x00\x00'
    msg += b'\x00\x00\x00\x80\x53\x00\x00\x00\x00\x01\x04\x53\x00\x00\x00\x00'
    msg += b'\x01\x90\x41\x00\x00\x01\x91\x53\x00\x00\x00\x00\x01\x90\x53\x00'
    msg += b'\x00\x00\x00\x01\x91\x53\x00\x00\x00\x00\x01\x90\x53\x00\x00\x00'
    msg += b'\x00\x01\x91\x53\x00\x00\x00\x00\x01\x94\x53\x00\x00\x00\x00\x01'
    msg += b'\x95\x53\x00\x00\x00\x00\x01\x98\x53\x00\x00\x00\x00\x01\x99\x53'
    msg += b'\x00\x00\x00\x00\x01\x80\x53\x00\x00\x00\x00\x01\x90\x41\x00\x00'
    msg += b'\x01\x94\x53\x00\x00\x00\x00\x01\x94\x53\x00\x00\x00\x00\x01\x96'
    msg += b'\x53\x00\x00\x00\x00\x01\x98\x53\x00\x00\x00\x00\x01\xa0\x53\x00'
    msg += b'\x00\x00\x00\x01\xf0\x41\x00\x00\x01\xf1\x53\x00\x00\x00\x00\x01'
    msg += b'\xf4\x53\x00\x00\x00\x00\x01\xf5\x53\x00\x00\x00\x00\x01\xf8\x53'
    msg += b'\x00\x00\x00\x00\x01\xf9\x53\x00\x00\x00\x00\x00\x00\x53\x00\x00'
    msg += b'\x00\x00\x00\x01\x53\x00\x00\x00\x00\x00\x00\x53\x00\x00\x00\x00'
    msg += b'\x00\x01\x53\x00\x00\x00\x00\x00\x04\x53\x00\x00\x00\x00\x00\x58'
    msg += b'\x41\x00\x00\x02\x00\x53\x00\x00\x00\x00\x02\x00\x53\x00\x00\x00'
    msg += b'\x00\x02\x02\x53\x00\x00\x00\x00\x02\x00\x53\x00\x00\x00\x00\x02'
    msg += b'\x04\x53\x00\x00\x00\x00\x02\x58\x41\x00\x00\x02\x59\x53\x00\x00'
    msg += b'\x00\x00\x02\x40\x53\x00\x00\x00\x00\x02\x41\x53\x00\x00\x00\x00'
    msg += b'\x02\x40\x53\x00\x00\x00\x00\x02\x41\x53\x00\x00\x00\x00\x02\x44'
    msg += b'\x53\x00\x00\x00\x00\x02\x45\x53\x00\x00\x00\x00\x02\x60\x53\x00'
    msg += b'\x00\x00\x00\x02\x61\x53\x00\x00\x00\x00\x02\x60\x53\x00\x00\x00'
    msg += b'\x00\x02\x20\x41\x00\x00\x02\x24\x53\x00\x00\x00\x00\x02\x24\x53'
    msg += b'\x00\x00\x00\x00\x02\x26\x53\x00\x00\x00\x00\x02\x40\x53\x00\x00'
    msg += b'\x00\x00\x02\x40\x53\x00\x00\x00\x00\x02\x80\x41\x00\x00\x02\x81'
    msg += b'\x53\x00\x00\x00\x00\x02\x84\x53\x00\x00\x00\x00\x02\x85\x53\x00'
    msg += b'\x00\x00\x00\x02\xc0\x53\x00\x00\x00\x00\x02\xc1\x53\x00\x00\x00'
    msg += b'\x00\x02\xc0\x53\x00\x00\x00\x00\x02\xc1\x53\x00\x00\x00\x00\x02'
    msg += b'\xc0\x53\x00\x00\x00\x00\x02\xc1\x53\x00\x00\x00\x00\x02\xc4\x53'
    msg += b'\x00\x00\x00\x00\x02\x00\x53\x00\x00\x00\x00\x02\x80\x53\x00\x00'
    msg += b'\x00\x00\x02\xc8\x42\x00\x00\x00\x00\x48\x42\x00\x00\x00\x00\x80'
    msg += b'\x42\x00\x00\x00\x00\x04\x53\x00\x00\x00\x00\x01\x20\x53\x00\x00'
    msg += b'\x00\x00\x01\x84\x53\x00\x10\x00\x00\x02\x40\x46\x00\x00\x00\x00'
    msg += b'\x00\x00\x04\x04\x46\x02\x00\x46\x02\x00\x00\x04\x00\x46\x00\x00'
    msg += b'\x00\x00\x00\x00\x05\x04\x42\x00\x00\x00\x05\x50\x42\x00\x00\x00'
    msg += b'\x00\x14\x42\x00\x00\x00\x00\x00\x46\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\xa4\x46\x00\x00\x00\x00\x00\x00\x01\x00\x46\x00\x00\x00\x00\x00'
    msg += b'\x00\x01\x44\x46\x00\x00\x00\x00\x00\x00\x02\x00\x46\x00\x00\x00'
    msg += b'\x00\x00\x00\x08\x04\x46\x00\x00\x00\x00\x00\x00\x08\x90\x46\x00'
    msg += b'\x00\x00\x00\x00\x00\x08\x54\x46\x00\x00\x00\x00\x00\x00\x09\x20'
    msg += b'\x46\x00\x00\x00\x00\x00\x00\x08\x04\x46\x00\x00\x00\x00\x00\x00'
    msg += b'\x08\x00\x46\x00\x00\x00\x00\x00\x00\x08\x84\x46\x00\x00\x00\x00'
    msg += b'\x00\x00\x08\x40\x46\x00\x00\x00\x00\x00\x00\x09\x04\x46\x00\x00'
    msg += b'\x00\x00\x00\x00\x0a\x10\x46\x00\x00\x00\x00\x00\x00\x0c\x14\x46'
    msg += b'\x00\x00\x00\x00\x00\x00\x0c\x80\x46\x00\x00\x00\x00\x00\x00\x0c'
    msg += b'\x24\x42\x00\x00\x00\x0d\x00\x42\x00\x00\x00\x00\x04\x42\x00\x00'
    msg += b'\x00\x00\x00\x42\x00\x00\x00\x00\x44\x42\x00\x00\x00\x00\x10\x42'
    msg += b'\x00\x00\x00\x01\x14\x53\x00\x00\x00\x00\x01\xa0\x53\x00\x00\x00'
    msg += b'\x00\x10\x04\x53\x55\xaa\x00\x00\x10\x40\x53\x00\x00\x00\x00\x10'
    msg += b'\x04\x53\x00\x00\x00\x00\x11\x00\x53\x00\x00\x00\x00\x11\x84\x53'
    msg += b'\x00\x00\x00\x00\x10\x50\x53\xff\xff\x00\x00\x10\x14\x53\x03\x20'
    msg += b'\x00\x00\x10\x00\x53\x00\x00\x00\x00\x11\x24\x53\x00\x00\x00\x00'
    msg += b'\x03\x00\x53\x00\x00\x00\x00\x03\x64\x53\x00\x00\x00\x00\x04\x50'
    msg += b'\x53\x00\x00\x00\x00\x00\x34\x53\x00\x00\x00\x00\x00\x00\x42\x02'
    msg += b'\x00\x00\x01\x04\x42\x00\x00\x00\x21\x00\x42\x00\x00\x00\x21\x44'
    msg += b'\x42\x00\x00\x00\x22\x10\x53\x00\x00\x00\x00\x28\x14\x42\x01\x00'
    msg += b'\x00\x28\xa0\x46\x42\x48\x00\x00\x00\x00\x29\x04\x42\x00\x00\x00'
    msg += b'\x29\x40\x42\x00\x00\x00\x28\x04\x46\x42\x10\x00\x00\x00\x00\x28'
    msg += b'\x00\x42\x00\x00\x00\x28\x84\x42\x00\x00\x00\x28\x50\x42\x00\x00'
    msg += b'\x00\x29\x14\x42\x00\x00\x00\x2a\x00\x42\x00\x00\x00\x2c\x24\x46'
    msg += b'\x42\x10\x00\x00\x00\x00\x2c\x80\x42\x00\x00\x00\x2c\x44\x53\x00'
    msg += b'\x02\x00\x00\x2d\x00\x42\x00\x00\x00\x20\x04\x46\x42\x4d\x00\x00'
    msg += b'\x00\x00\x20\x10\x42\x00\x00\x00\x20\x54\x42\x00\x00\x00\x20\x20'
    msg += b'\x42\x00\x00\x00\x21\x04\x53\x00\x01\x00\x00\x22\x00\x42\x00\x00'
    msg += b'\x00\x30\x04\x42\x00\x00\x00\x30\x40\x53\x00\x00\x00\x00\x30\x04'
    msg += b'\x53\x00\x00\x00\x00\x31\x10\x42\x00\x00\x00\x31\x94\x53\x00\x04'
    msg += b'\x00\x00\x30\x00\x53\x00\x00\x00\x00\x30\x24\x53\x00\x00\x00\x00'
    msg += b'\x30\x00\x53\x00\x00\x00\x00\x31\x04\x53\x00\x00\x00\x00\x31\x80'
    msg += b'\x53\x00\x00\x00\x00\x32\x44\x53\x00\x00\x00\x00\x30\x00\x53\x00'
    msg += b'\x00\x00\x00\x30\x80\x53\x00\x00\x00\x00\x30\x00\x53\x00\x00\x00'
    msg += b'\x00\x30\x80\x53\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x03\x00'
    msg += b'\x00\x00\x00\x00'
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
def ConfigTsunAllowAll():
    Config.config = {'tsun':{'enabled': True}, 'inverters':{'allow_all':True}}

@pytest.fixture
def ConfigNoTsunInv1():
    Config.config = {'tsun':{'enabled': False},'inverters':{'R170000000000001':{'node_id':'inv1','suggested_area':'roof'}}}

@pytest.fixture
def ConfigTsunInv1():
    Config.config = {'tsun':{'enabled': True},'inverters':{'R170000000000001':{'node_id':'inv1','suggested_area':'roof'}}}

@pytest.fixture
def MsgOtaReq(): # Over the air update rewuest from tsun cloud
    msg  =  b'\x00\x00\x01\x16\x10R170000000000001\x70\x13\x01\x02\x76\x35\x70\x68\x74\x74\x70'
    msg +=  b'\x3a\x2f\x2f\x77\x77\x77\x2e\x74\x61\x6c\x65\x6e\x74\x2d\x6d\x6f'
    msg +=  b'\x6e\x69\x74\x6f\x72\x69\x6e\x67\x2e\x63\x6f\x6d\x3a\x39\x30\x30'
    msg +=  b'\x32\x2f\x70\x72\x6f\x64\x2d\x61\x70\x69\x2f\x72\x6f\x6d\x2f\x75'
    msg +=  b'\x70\x64\x61\x74\x65\x2f\x64\x6f\x77\x6e\x6c\x6f\x61\x64\x3f\x76'
    msg +=  b'\x65\x72\x3d\x56\x31\x2e\x30\x30\x2e\x31\x37\x26\x6e\x61\x6d\x65'
    msg +=  b'\x3d\x47\x33\x2d\x57\x69\x46\x69\x2b\x2d\x56\x31\x2e\x30\x30\x2e'
    msg +=  b'\x31\x37\x2d\x4f\x54\x41\x26\x65\x78\x74\x3d\x30\x60\x68\x74\x74'
    msg +=  b'\x70\x3a\x2f\x2f\x77\x77\x77\x2e\x74\x61\x6c\x65\x6e\x74\x2d\x6d'
    msg +=  b'\x6f\x6e\x69\x74\x6f\x72\x69\x6e\x67\x2e\x63\x6f\x6d\x3a\x39\x30'
    msg +=  b'\x30\x32\x2f\x70\x72\x6f\x64\x2d\x61\x70\x69\x2f\x72\x6f\x6d\x2f'
    msg +=  b'\x75\x70\x64\x61\x74\x65\x2f\x63\x61\x6c\x6c\x62\x61\x63\x6b\x3f'
    msg +=  b'\x71\x69\x64\x3d\x31\x35\x30\x33\x36\x32\x26\x72\x69\x64\x3d\x32'
    msg +=  b'\x32\x39\x26\x64\x69\x64\x3d\x31\x33\x34\x32\x32\x35\x20\x36\x35'
    msg +=  b'\x66\x30\x64\x37\x34\x34\x62\x66\x33\x39\x61\x62\x38\x32\x34\x64'
    msg +=  b'\x32\x38\x62\x38\x34\x64\x31\x39\x65\x64\x33\x31\x31\x63\x06\x34'
    msg +=  b'\x36\x38\x36\x33\x33\x01\x31\x01\x30\x00'  
    return msg    

@pytest.fixture
def MsgOtaAck(): # Over the air update rewuest from tsun cloud
    return b'\x00\x00\x00\x14\x10R170000000000001\x91\x13\x01'

@pytest.fixture
def MsgOtaInvalid(): # Get Time Request message
    return b'\x00\x00\x00\x14\x10R170000000000001\x99\x13\x01'

@pytest.fixture
def MsgModbusCmd():
    msg  = b'\x00\x00\x00\x20\x10R170000000000001'
    msg += b'\x70\x77\x00\x01\xa3\x28\x08\x01\x06\x20\x08'
    msg += b'\x00\x00\x03\xc8'
    return msg

@pytest.fixture
def MsgModbusCmdCrcErr():
    msg  = b'\x00\x00\x00\x20\x10R170000000000001'
    msg += b'\x70\x77\x00\x01\xa3\x28\x08\x01\x06\x20\x08'
    msg += b'\x00\x00\x04\xc8'
    return msg

@pytest.fixture
def MsgModbusRsp():
    msg  = b'\x00\x00\x00\x20\x10R170000000000001'
    msg += b'\x91\x77\x17\x18\x19\x1a\x08\x01\x06\x20\x08'
    msg += b'\x00\x00\x03\xc8'
    return msg

@pytest.fixture
def MsgModbusInv():
    msg  = b'\x00\x00\x00\x20\x10R170000000000001'
    msg += b'\x99\x77\x17\x18\x19\x1a\x08\x01\x06\x20\x08'
    msg += b'\x00\x00\x03\xc8'
    return msg

@pytest.fixture
def MsgModbusResp20():
    msg  = b'\x00\x00\x00\x45\x10R170000000000001'
    msg += b'\x91\x77\x17\x18\x19\x1a\x2d\x01\x03\x28\x51'
    msg += b'\x09\x08\xd3\x00\x29\x13\x87\x00\x3e\x00\x00\x01\x2c\x03\xb4\x00'
    msg += b'\x08\x00\x00\x00\x00\x01\x59\x01\x21\x03\xe6\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\xdb\x6b'
    return msg

@pytest.fixture
def MsgModbusResp21():
    msg  = b'\x00\x00\x00\x45\x10R170000000000001'
    msg += b'\x91\x77\x17\x18\x19\x1a\x2d\x01\x03\x28\x51'
    msg += b'\x0e\x08\xd3\x00\x29\x13\x87\x00\x3e\x00\x00\x01\x2c\x03\xb4\x00'
    msg += b'\x08\x00\x00\x00\x00\x01\x59\x01\x21\x03\xe6\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\xe6\xef'
    return msg

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
    m.read()         # read rest of message
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
    m.contact_name = b'solarhub'
    m.contact_mail = b'solarhub@123456'
    m._init_new_client_conn()
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
    m.contact_name = b'solarhub'
    m.contact_mail = b'solarhub@123456'
    m._init_new_client_conn()
    assert m._send_buffer==b'\x00\x00\x00,\x10R170000000000002\x91\x00\x08solarhub\x0fsolarhub@123456'
    m.close()

def test_msg_contact_resp(ConfigTsunInv1, MsgContactResp):
    ConfigTsunInv1
    m = MemoryStream(MsgContactResp, (0,), False)
    m.await_conn_resp_cnt = 1
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.await_conn_resp_cnt == 0
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==0
    assert m.header_len==23
    assert m.data_len==1
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_contact_resp_2(ConfigTsunInv1, MsgContactResp):
    ConfigTsunInv1
    m = MemoryStream(MsgContactResp, (0,), False)
    m.await_conn_resp_cnt = 0
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.await_conn_resp_cnt == 0
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==0
    assert m.header_len==23
    assert m.data_len==1
    assert m._forward_buffer==MsgContactResp
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_contact_resp_3(ConfigTsunInv1, MsgContactResp):
    ConfigTsunInv1
    m = MemoryStream(MsgContactResp, (0,), True)
    m.await_conn_resp_cnt = 0
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.await_conn_resp_cnt == 0
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==0
    assert m.header_len==23
    assert m.data_len==1
    assert m._forward_buffer==MsgContactResp
    assert m._send_buffer==b''
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
    assert m.ts_offset==0
    assert m.data_len==0
    assert m._forward_buffer==MsgGetTime
    assert m._send_buffer==b'\x00\x00\x00\x1b\x10R170000000000001\x91"\x00\x00\x01\x89\xc6,_\x00'
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_get_time_autark(ConfigNoTsunInv1, MsgGetTime):
    ConfigNoTsunInv1
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
    assert m.ts_offset==0
    assert m.data_len==0
    assert m._forward_buffer==b''
    assert m._send_buffer==bytearray(b'\x00\x00\x00\x1b\x10R170000000000001\x91"\x00\x00\x01\x89\xc6,_\x00')
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_time_resp(ConfigTsunInv1, MsgTimeResp):
    ConfigTsunInv1
    m = MemoryStream(MsgTimeResp, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==34
    assert m.header_len==23
    assert m.ts_offset==3600000
    assert m.data_len==8
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_time_resp_autark(ConfigNoTsunInv1, MsgTimeResp):
    ConfigNoTsunInv1
    m = MemoryStream(MsgTimeResp, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==34
    assert m.header_len==23
    assert m.ts_offset==3600000
    assert m.data_len==8
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_time_inv_resp(ConfigTsunInv1, MsgTimeRespInv):
    ConfigTsunInv1
    m = MemoryStream(MsgTimeRespInv, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==34
    assert m.header_len==23
    assert m.ts_offset==0
    assert m.data_len==4
    assert m._forward_buffer==MsgTimeRespInv
    assert m._send_buffer==b''
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
    assert m.ts_offset==0
    assert m.data_len==0
    assert m._forward_buffer==MsgTimeInvalid
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()

def test_msg_time_invalid_autark(ConfigNoTsunInv1, MsgTimeInvalid):
    ConfigNoTsunInv1
    m = MemoryStream(MsgTimeInvalid, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==148
    assert m.msg_id==34
    assert m.ts_offset==0
    assert m.header_len==23
    assert m.data_len==0
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()

def test_msg_cntrl_ind(ConfigTsunInv1, MsgControllerInd, MsgControllerIndTsOffs, MsgControllerAck):
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
    m.ts_offset = 0
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgControllerInd
    m.ts_offset = -4096
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgControllerIndTsOffs
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
    m.ts_offset = 0
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgControllerInvalid
    m.ts_offset = -4096
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgControllerInvalid
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()

def test_msg_inv_ind(ConfigTsunInv1, MsgInverterInd, MsgInverterIndTsOffs, MsgInverterAck):
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
    m.ts_offset = 0
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgInverterInd
    m.ts_offset = +256
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgInverterIndTsOffs
    assert m._send_buffer==MsgInverterAck
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_inv_ind2(ConfigTsunInv1, MsgInverterIndNew, MsgInverterIndTsOffs, MsgInverterAck):
    ConfigTsunInv1
    tracer.setLevel(logging.DEBUG)
    m = MemoryStream(MsgInverterIndNew, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Invalid_Data_Type'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Invalid_Data_Type'] == 0
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==4
    assert m.header_len==23
    assert m.data_len==1165
    m.ts_offset = 0
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgInverterIndNew
    assert m._send_buffer==MsgInverterAck
    m.close()

def test_msg_inv_ind2(ConfigTsunInv1, MsgInverterIndNew, MsgInverterIndTsOffs, MsgInverterAck):
    ConfigTsunInv1
    tracer.setLevel(logging.DEBUG)
    m = MemoryStream(MsgInverterIndNew, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Invalid_Data_Type'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Invalid_Data_Type'] == 0
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==4
    assert m.header_len==23
    assert m.data_len==1165
    m.ts_offset = 0
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgInverterIndNew
    assert m._send_buffer==MsgInverterAck
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
    m.ts_offset = 0
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgInverterInvalid
    m.ts_offset = 256
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgInverterInvalid
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()

def test_msg_ota_req(ConfigTsunInv1, MsgOtaReq):
    ConfigTsunInv1
    m = MemoryStream(MsgOtaReq, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['OTA_Start_Msg'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==112
    assert m.msg_id==19
    assert m.header_len==23
    assert m.data_len==259
    m.ts_offset = 0
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgOtaReq
    m.ts_offset = 4096
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgOtaReq
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['OTA_Start_Msg'] == 1
    m.close()

def test_msg_ota_ack(ConfigTsunInv1, MsgOtaAck):
    ConfigTsunInv1
    tracer.setLevel(logging.ERROR)

    m = MemoryStream(MsgOtaAck, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['OTA_Start_Msg'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==19
    assert m.header_len==23
    assert m.data_len==1
    m.ts_offset = 0
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgOtaAck
    m.ts_offset = 256
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgOtaAck
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['OTA_Start_Msg'] == 0
    m.close()

def test_msg_ota_invalid(ConfigTsunInv1, MsgOtaInvalid):
    ConfigTsunInv1
    m = MemoryStream(MsgOtaInvalid, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['OTA_Start_Msg'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==153
    assert m.msg_id==19
    assert m.header_len==23
    assert m.data_len==1
    m.ts_offset = 0
    m._update_header(m._forward_buffer)
    assert m._forward_buffer==MsgOtaInvalid
    m.ts_offset = 4096
    assert m._forward_buffer==MsgOtaInvalid
    m._update_header(m._forward_buffer)
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    assert m.db.stat['proxy']['OTA_Start_Msg'] == 0
    m.close()

def test_msg_unknown(ConfigTsunInv1, MsgUnknown):
    ConfigTsunInv1
    m = MemoryStream(MsgUnknown, (0,), False)
    m.db.stat['proxy']['Unknown_Msg'] = 0
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
    c = Control(0x70)
    assert not c.is_ind()
    assert not c.is_resp()    
    assert c.is_req()
    c = Control(0x91)
    assert not c.is_req()
    assert c.is_ind()
    assert not c.is_resp()    
    c = Control(0x99)
    assert not c.is_req()
    assert not c.is_ind()
    assert c.is_resp()    

    
def test_msg_iterator():
    m1 = Talent(server_side=True)
    m2 = Talent(server_side=True)
    m3 = Talent(server_side=True)
    m3.close()
    del m3
    test1 = 0
    test2 = 0
    for key in Talent:
        if key == m1:
            test1+=1
        elif key == m2:
            test2+=1
        elif type(key) != Talent:
            continue
        else:
            assert False
    assert test1 == 1
    assert test2 == 1

def test_proxy_counter():
    # m = MemoryStream(b'')
    # m.close()
    Infos.stat['proxy']['Modbus_Command'] = 1
 
    m = MemoryStream(b'')
    m.id_str = b"R170000000000001" 
    c = m.createClientStream(b'')

    assert m.new_data == {}
    m.db.stat['proxy']['Unknown_Msg'] = 0
    c.db.stat['proxy']['Unknown_Msg'] = 0
    Infos.new_stat_data['proxy'] =  False

    m.inc_counter('Unknown_Msg')
    m.close()
    m = MemoryStream(b'')
   
    assert m.new_data == {}
    assert Infos.new_stat_data == {'proxy': True}
    assert m.db.new_stat_data == {'proxy': True}
    assert c.db.new_stat_data == {'proxy': True}
    assert 1 == m.db.stat['proxy']['Unknown_Msg']
    assert 1 == c.db.stat['proxy']['Unknown_Msg']
    Infos.new_stat_data['proxy'] =  False

    c.inc_counter('Unknown_Msg')
    assert m.new_data == {}
    assert Infos.new_stat_data == {'proxy': True}
    assert m.db.new_stat_data == {'proxy': True}
    assert c.db.new_stat_data == {'proxy': True}
    assert 2 == m.db.stat['proxy']['Unknown_Msg']
    assert 2 == c.db.stat['proxy']['Unknown_Msg']
    Infos.new_stat_data['proxy'] =  False

    c.inc_counter('Modbus_Command')
    assert m.new_data == {}
    assert Infos.new_stat_data == {'proxy': True}
    assert m.db.new_stat_data == {'proxy': True}
    assert c.db.new_stat_data == {'proxy': True}
    assert 2 == m.db.stat['proxy']['Modbus_Command']
    assert 2 == c.db.stat['proxy']['Modbus_Command']

    Infos.new_stat_data['proxy'] =  False
    m.dec_counter('Unknown_Msg')
    assert m.new_data == {}
    assert Infos.new_stat_data == {'proxy': True}
    assert 1 == m.db.stat['proxy']['Unknown_Msg']
    m.close()

def test_msg_modbus_req(ConfigTsunInv1, MsgModbusCmd):
    ConfigTsunInv1
    m = MemoryStream(b'')
    m.id_str = b"R170000000000001" 
    m.state = State.up

    c = m.createClientStream(MsgModbusCmd)
    
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.db.stat['proxy']['Invalid_Msg_Format'] = 0
    c.read()         # read complete msg, and dispatch msg
    assert not c.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert c.msg_count == 1
    assert c.id_str == b"R170000000000001" 
    assert c.unique_id == 'R170000000000001'
    assert int(c.ctrl)==112
    assert c.msg_id==119
    assert c.header_len==23
    assert c.data_len==13
    assert c._forward_buffer==b''
    assert c._send_buffer==b''
    assert m.id_str == b"R170000000000001" 
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.writer.sent_pdu == MsgModbusCmd
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 1
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_msg_modbus_req2(ConfigTsunInv1, MsgModbusCmd):
    ConfigTsunInv1
    m = MemoryStream(b'')
    m.id_str = b"R170000000000001" 

    c = m.createClientStream(MsgModbusCmd)
    
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.db.stat['proxy']['Invalid_Msg_Format'] = 0
    c.read()         # read complete msg, and dispatch msg
    assert not c.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert c.msg_count == 1
    assert c.id_str == b"R170000000000001" 
    assert c.unique_id == 'R170000000000001'
    assert int(c.ctrl)==112
    assert c.msg_id==119
    assert c.header_len==23
    assert c.data_len==13
    assert c._forward_buffer==b''
    assert c._send_buffer==b''
    assert m.id_str == b"R170000000000001" 
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.writer.sent_pdu == b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 1
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_msg_modbus_req3(ConfigTsunInv1, MsgModbusCmdCrcErr):
    ConfigTsunInv1
    m = MemoryStream(b'')
    m.id_str = b"R170000000000001" 
    c = m.createClientStream(MsgModbusCmdCrcErr)
    
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.db.stat['proxy']['Invalid_Msg_Format'] = 0
    c.read()         # read complete msg, and dispatch msg
    assert not c.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert c.msg_count == 1
    assert c.id_str == b"R170000000000001" 
    assert c.unique_id == 'R170000000000001'
    assert int(c.ctrl)==112
    assert c.msg_id==119
    assert c.header_len==23
    assert c.data_len==13
    assert c._forward_buffer==b''
    assert c._send_buffer==b''
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.writer.sent_pdu ==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 1
    m.close()

def test_msg_modbus_rsp1(ConfigTsunInv1, MsgModbusRsp):
    '''Modbus response without a valid Modbus request must be dropped'''
    ConfigTsunInv1
    m = MemoryStream(MsgModbusRsp)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==119
    assert m.header_len==23
    assert m.data_len==13
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_msg_modbus_cloud_rsp(ConfigTsunInv1, MsgModbusRsp):
    '''Modbus response from TSUN without a valid Modbus request must be dropped'''
    ConfigTsunInv1
    m = MemoryStream(MsgModbusRsp, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Unknown_Msg'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==119
    assert m.header_len==23
    assert m.data_len==13
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Msg'] == 1
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_msg_modbus_rsp2(ConfigTsunInv1, MsgModbusResp20):
    '''Modbus response with a valid Modbus request must be forwarded'''
    ConfigTsunInv1
    m = MemoryStream(MsgModbusResp20)
    m.append_msg(MsgModbusResp20)

    m.mb.rsp_handler = m.msg_forward
    m.mb.last_addr = 1
    m.mb.last_fcode = 3
    m.mb.last_len = 20
    m.mb.last_reg = 0x3008
    m.mb.req_pend = True
    m.mb.err = 0

    assert m.db.db == {}
    m.new_data['inverter'] = False

    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.mb.err == 0
    assert m.msg_count == 1
    assert m._forward_buffer==MsgModbusResp20
    assert m._send_buffer==b''
    assert m.db.db == {'inverter': {'Version': 'V5.1.09', 'Rated_Power': 300}, 'grid': {'Voltage': 225.9, 'Current': 0.41, 'Frequency': 49.99, 'Output_Power': 94.8}, 'env': {'Inverter_Temp': 22}, 'input': {'pv1': {'Voltage': 0.8, 'Current': 0.0, 'Power': 0.0}, 'pv2': {'Voltage': 34.5, 'Current': 2.89, 'Power': 99.8}, 'pv3': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}, 'pv4': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}}}
    assert m.db.get_db_value(Register.VERSION) == 'V5.1.09'
    assert m.new_data['inverter'] == True

    m.new_data['inverter'] = False    
    m.mb.req_pend = True
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.mb.err == 0
    assert m.msg_count == 2
    assert m._forward_buffer==MsgModbusResp20
    assert m._send_buffer==b''
    assert m.db.db == {'inverter': {'Version': 'V5.1.09', 'Rated_Power': 300}, 'grid': {'Voltage': 225.9, 'Current': 0.41, 'Frequency': 49.99, 'Output_Power': 94.8}, 'env': {'Inverter_Temp': 22}, 'input': {'pv1': {'Voltage': 0.8, 'Current': 0.0, 'Power': 0.0}, 'pv2': {'Voltage': 34.5, 'Current': 2.89, 'Power': 99.8}, 'pv3': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}, 'pv4': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}}}
    assert m.db.get_db_value(Register.VERSION) == 'V5.1.09'
    assert m.new_data['inverter'] == False

    m.close()

def test_msg_modbus_rsp3(ConfigTsunInv1, MsgModbusResp21):
    '''Modbus response with a valid Modbus request must be forwarded'''
    ConfigTsunInv1
    m = MemoryStream(MsgModbusResp21)
    m.append_msg(MsgModbusResp21)

    m.mb.rsp_handler = m.msg_forward
    m.mb.last_addr = 1
    m.mb.last_fcode = 3
    m.mb.last_len = 20
    m.mb.last_reg = 0x3008
    m.mb.req_pend = True
    m.mb.err = 0

    assert m.db.db == {}
    m.new_data['inverter'] = False

    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.mb.err == 0
    assert m.msg_count == 1
    assert m._forward_buffer==MsgModbusResp21
    assert m._send_buffer==b''
    assert m.db.db == {'inverter': {'Version': 'V5.1.0E', 'Rated_Power': 300}, 'grid': {'Voltage': 225.9, 'Current': 0.41, 'Frequency': 49.99, 'Output_Power': 94.8}, 'env': {'Inverter_Temp': 22}, 'input': {'pv1': {'Voltage': 0.8, 'Current': 0.0, 'Power': 0.0}, 'pv2': {'Voltage': 34.5, 'Current': 2.89, 'Power': 99.8}, 'pv3': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}, 'pv4': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}}}
    assert m.db.get_db_value(Register.VERSION) == 'V5.1.0E'
    assert m.new_data['inverter'] == True
    m.new_data['inverter'] = False
    assert m.mb.req_pend == False

    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.mb.err == 5
    assert m.msg_count == 2
    assert m._forward_buffer==MsgModbusResp21
    assert m._send_buffer==b''
    assert m.db.db == {'inverter': {'Version': 'V5.1.0E', 'Rated_Power': 300}, 'grid': {'Voltage': 225.9, 'Current': 0.41, 'Frequency': 49.99, 'Output_Power': 94.8}, 'env': {'Inverter_Temp': 22}, 'input': {'pv1': {'Voltage': 0.8, 'Current': 0.0, 'Power': 0.0}, 'pv2': {'Voltage': 34.5, 'Current': 2.89, 'Power': 99.8}, 'pv3': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}, 'pv4': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}}}
    assert m.db.get_db_value(Register.VERSION) == 'V5.1.0E'
    assert m.new_data['inverter'] == False

    m.close()

def test_msg_modbus_invalid(ConfigTsunInv1, MsgModbusInv):
    ConfigTsunInv1
    m = MemoryStream(MsgModbusInv, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==153
    assert m.msg_id==119
    assert m.header_len==23
    assert m.data_len==13
    assert m._forward_buffer==MsgModbusInv
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_msg_modbus_fragment(ConfigTsunInv1, MsgModbusResp20):
    ConfigTsunInv1
    # receive more bytes than expected (7 bytes from the next msg)
    m = MemoryStream(MsgModbusResp20+b'\x00\x00\x00\x45\x10\x52\x31', (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.mb.rsp_handler = m.msg_forward
    m.mb.last_addr = 1
    m.mb.last_fcode = 3
    m.mb.last_len = 20
    m.mb.last_reg = 0x3008
    m.mb.req_pend = True
    m.mb.err = 0

    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl) == 0x91
    assert m.msg_id == 119
    assert m.header_len == 23
    assert m.data_len == 50
    assert m._forward_buffer==MsgModbusResp20
    assert m._send_buffer == b''
    assert m.mb.err == 0
    assert m.modbus_elms == 20-1  # register 0x300d is unknown, so one value can't be mapped
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

@pytest.mark.asyncio
async def test_msg_build_modbus_req(ConfigTsunInv1, MsgModbusCmd):
    ConfigTsunInv1
    m = MemoryStream(b'', (0,), True)
    m.id_str = b"R170000000000001" 
    await m.send_modbus_cmd(Modbus.WRITE_SINGLE_REG, 0x2008, 0, logging.DEBUG)
    assert 0 == m.send_msg_ofs
    assert m._forward_buffer == b''
    assert m._send_buffer == b''
    assert m.writer.sent_pdu == b''

    m.state = State.up
    await m.send_modbus_cmd(Modbus.WRITE_SINGLE_REG, 0x2008, 0, logging.DEBUG)
    assert 0 == m.send_msg_ofs
    assert m._forward_buffer == b''
    assert m._send_buffer == b''
    assert m.writer.sent_pdu == MsgModbusCmd

    m.writer.sent_pdu = bytearray(0) # clear send buffer for next test    
    m.test_exception_async_write = True
    await m.send_modbus_cmd(Modbus.WRITE_SINGLE_REG, 0x2008, 0, logging.DEBUG)
    assert 0 == m.send_msg_ofs
    assert m._forward_buffer == b''
    assert m._send_buffer == b''
    assert m.writer.sent_pdu == b''
    m.close()
'''
def test_zombie_conn(ConfigTsunInv1, MsgInverterInd):
    ConfigTsunInv1
    tracer.setLevel(logging.DEBUG)
    start_val = MemoryStream._RefNo

    m1 = MemoryStream(MsgInverterInd, (0,))
    assert MemoryStream._RefNo == 1 + start_val
    assert m1.RefNo == 1 + start_val
    m2 = MemoryStream(MsgInverterInd, (0,))
    assert MemoryStream._RefNo == 2 + start_val
    assert m2.RefNo == 2 + start_val
    m3 = MemoryStream(MsgInverterInd, (0,))
    assert MemoryStream._RefNo == 3 + start_val
    assert m3.RefNo == 3 + start_val
    assert m1.state == m1.State.init
    assert m2.state == m2.State.init
    assert m3.state == m3.State.init
    m1.read()         # read complete msg, and set unique_id
    assert m1.state == m1.State.up
    assert m2.state == m2.State.init
    assert m3.state == m3.State.init
    m2.read()         # read complete msg, and set unique_id
    assert m1.state == m1.State.closed
    assert m2.state == m2.State.up
    assert m3.state == m3.State.init
    m3.read()         # read complete msg, and set unique_id
    assert m1.state == m1.State.closed
    assert m2.state == m2.State.closed
    assert m3.state == m3.State.up
    m1.close()
    m2.close()
    m3.close()
'''