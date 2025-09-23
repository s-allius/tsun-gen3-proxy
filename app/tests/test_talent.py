# test_with_pytest.py
import pytest, logging, asyncio
from math import isclose
from async_stream import AsyncIfcImpl, StreamPtr
from gen3.talent import Talent, Control
from cnf.config import Config
from infos import Infos, Register
from modbus import Modbus
from messages import State
from mock import patch

 
pytest_plugins = ('pytest_asyncio',)

# initialize the proxy statistics
Infos.static_init()

tracer = logging.getLogger('tracer')

class FakeIfc(AsyncIfcImpl):
    def __init__(self):
        super().__init__()
        self.remote = StreamPtr(None)

class MemoryStream(Talent):
    def __init__(self, msg, chunks = (0,), server_side: bool = True):
        self.ifc = FakeIfc()
        super().__init__(None, ('test.local', 1234), self.ifc, server_side)
        if server_side:
            self.mb.timeout = 0.4   # overwrite for faster testing
        self.mb_first_timeout = 0.5
        self.mb_timeout = 0.5
        self.sent_pdu = b''
        self.ifc.tx_fifo.reg_trigger(self.write_cb)
        self.__msg = msg
        self.__msg_len = len(msg)
        self.__chunks = chunks
        self.__offs = 0
        self.__chunk_idx = 0
        self.msg_count = 0
        self.addr = 'Test: SrvSide'
        self.send_msg_ofs = 0
        self.msg_recvd = []

    def write_cb(self):
        self.sent_pdu = self.ifc.tx_fifo.get()


    def append_msg(self, msg):
        self.__msg += msg
        self.__msg_len += len(msg)    

    def _read(self) -> int:
        copied_bytes = 0
        try:    
            if (self.__offs < self.__msg_len):
                chunk_len = self.__chunks[self.__chunk_idx]
                self.__chunk_idx += 1
                if chunk_len!=0:
                    self.ifc.rx_fifo += self.__msg[self.__offs:chunk_len]
                    copied_bytes = chunk_len - self.__offs
                    self.__offs = chunk_len
                else:
                    self.ifc.rx_fifo += self.__msg[self.__offs:]
                    copied_bytes = self.__msg_len - self.__offs
                    self.__offs = self.__msg_len
        except Exception:
            pass   # ignore exceptions here
        return copied_bytes
    
    def _timestamp(self):
        return 1691246944000

    def _utc(self):
        return 1691239744.0
    
    def createClientStream(self, msg, chunks = (0,)):
        c = MemoryStream(msg, chunks, False)
        self.ifc.remote.stream = c
        c.ifc.remote.stream = self
        return c

    def _Talent__flush_recv_msg(self) -> None:
        self.msg_recvd.append(
            {
                'ctrl': int(self.ctrl),
                'msg_id': self.msg_id,
                'header_len': self.header_len,
                'data_len': self.data_len
            }
        )

        super()._Talent__flush_recv_msg()

        self.msg_count += 1
    
    

@pytest.fixture
def msg_contact_info(): # Contact Info message
    return b'\x00\x00\x00\x2c\x10R170000000000001\x91\x00\x08solarhub\x0fsolarhub\x40123456'

@pytest.fixture
def msg_contact_info_empty(): # Contact Info message with empty string
    return b'\x00\x00\x00\x15\x10R170000000000001\x91\x00\x00\x00'

@pytest.fixture
def msg_contact_info_long_id():  # Contact Info message with longer ID
    Config.act_config = {'tsun':{'enabled': True}}
    return b'\x00\x00\x00\x2d\x11R1700000000000011\x91\x00\x08solarhub\x0fsolarhub\x40123456'


@pytest.fixture
def msg_contact_info_broken():  # Contact Info message with invalid string coding
    return b'\x00\x00\x00\x2a\x10R170000000000001\x91\x00solarhubsolarhub\x40123456'

@pytest.fixture
def msg2_contact_info(): # two Contact Info messages
    return b'\x00\x00\x00\x2c\x10R170000000000001\x91\x00\x08solarhub\x0fsolarhub\x40123456\x00\x00\x00\x2c\x10R170000000000002\x91\x00\x08solarhub\x0fsolarhub\x40123456'

@pytest.fixture
def msg_contact_rsp(): # Contact Response message
    return b'\x00\x00\x00\x14\x10R170000000000001\x91\x00\x01'

@pytest.fixture
def msg_contact_rsp2(): # Contact Response message
    return b'\x00\x00\x00\x14\x10R170000000000002\x91\x00\x01'

@pytest.fixture
def msg_contact_invalid(): # Contact Response message
    return b'\x00\x00\x00\x14\x10R170000000000001\x93\x00\x01'

@pytest.fixture
def msg_get_time(): # Get Time Request message
    return b'\x00\x00\x00\x13\x10R170000000000001\x91\x22'           

@pytest.fixture
def msg_time_rsp(): # Get Time Resonse message
    return b'\x00\x00\x00\x1b\x10R170000000000001\x91\x22\x00\x00\x01\x89\xc6\x63\x4d\x80'

@pytest.fixture
def msg_time_rsp_inv(): # Get Time Resonse message
    return b'\x00\x00\x00\x17\x10R170000000000001\x91\x22\x00\x00\x01\x89'

@pytest.fixture
def msg_time_invalid(): # Get Time Request message
    return b'\x00\x00\x00\x13\x10R170000000000001\x94\x22'           

@pytest.fixture
def msg_act_time(): # Act Time Indication message
    return b'\x00\x00\x00\x1c\x10R170000000000001\x91\x99\x01\x00\x00\x01\x89\xc6\x53\x4d\x80'           

@pytest.fixture
def msg_act_time_ofs(): # Act Time Indication message withoffset 3600
    return b'\x00\x00\x00\x1c\x10R170000000000001\x91\x99\x01\x00\x00\x01\x89\xc6\x53\x5b\x90'           

@pytest.fixture
def msg_act_time_ack(): # Act Time Response message
    return b'\x00\x00\x00\x14\x10R170000000000001\x99\x99\x02'

@pytest.fixture
def msg_act_time_cmd(): # Act Time Response message
    return b'\x00\x00\x00\x14\x10R170000000000001\x70\x99\x02'

@pytest.fixture
def msg_act_time_inv(): # Act Time Indication message withoffset 3600
    return b'\x00\x00\x00\x1b\x10R170000000000001\x91\x99\x00\x00\x01\x89\xc6\x53\x5b\x90'           

@pytest.fixture
def msg_controller_ind(): # Data indication from the controller
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
def msg_controller_ind_ts_offs(): # Data indication from the controller - offset 0x1000
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
def msg_controller_ack(): # Get Time Request message
    return b'\x00\x00\x00\x14\x10R170000000000001\x99\x71\x01'

@pytest.fixture
def msg_controller_invalid(): # Get Time Request message
    return b'\x00\x00\x00\x14\x10R170000000000001\x92\x71\x01'

@pytest.fixture
def msg_inverter_ind(): # Data indication from the controller
    msg  =  b'\x00\x00\x00\x8b\x10R170000000000001\x91\x04\x01\x90\x00\x01\x10R170000000000001'
    msg +=  b'\x01\x00\x00\x01\x89\xc6\x63\x61\x08'
    msg +=  b'\x00\x00\x00\x06\x00\x00\x00\x0a\x54\x08\x4d\x69\x63\x72\x6f\x69\x6e\x76\x00\x00\x00\x14\x54\x04\x54\x53\x55\x4e\x00\x00\x00\x1E\x54\x07\x56\x35\x2e\x30\x2e\x31\x31\x00\x00\x00\x28'
    msg +=  b'\x54\x10T170000000000001\x00\x00\x00\x32\x54\x0a\x54\x53\x4f\x4c\x2d\x4d\x53\x36\x30\x30\x00\x00\x00\x3c\x54\x05\x41\x2c\x42\x2c\x43'
    return msg

@pytest.fixture
def msg_inverter_ind_ts_offs(): # Data indication from the controller + offset 256
    msg  =  b'\x00\x00\x00\x8b\x10R170000000000001\x91\x04\x01\x90\x00\x01\x10R170000000000001'
    msg +=  b'\x01\x00\x00\x01\x89\xc6\x63\x62\x08'
    msg +=  b'\x00\x00\x00\x06\x00\x00\x00\x0a\x54\x08\x4d\x69\x63\x72\x6f\x69\x6e\x76\x00\x00\x00\x14\x54\x04\x54\x53\x55\x4e\x00\x00\x00\x1E\x54\x07\x56\x35\x2e\x30\x2e\x31\x31\x00\x00\x00\x28'
    msg +=  b'\x54\x10T170000000000001\x00\x00\x00\x32\x54\x0a\x54\x53\x4f\x4c\x2d\x4d\x53\x36\x30\x30\x00\x00\x00\x3c\x54\x05\x41\x2c\x42\x2c\x43'
    return msg

@pytest.fixture
def msg_inverter_ind2(): # Data indication from the controller
    msg  =  b'\x00\x00\x05\x02\x10R170000000000001\x91\x04\x01\x90\x00\x01\x10R170000000000001'
    msg +=  b'\x01\x00\x00\x01\x89\xc6\x63\x61\x08'
    msg +=  b'\x00\x00\x00\xa3\x00\x00\x00\x64\x53\x00\x01\x00\x00\x00\xc8\x53\x00\x02\x00\x00\x01\x2c\x53\x00\x00\x00\x00\x01\x90\x49\x00\x00\x00\x00\x00\x00\x01\x91\x53\x00\x00'
    msg +=  b'\x00\x00\x01\x92\x53\x00\x00\x00\x00\x01\x93\x53\x00\x00\x00\x00\x01\x94\x53\x00\x00\x00\x00\x01\x95\x53\x00\x00\x00\x00\x01\x96\x53\x00\x00\x00\x00\x01\x97\x53\x00'
    msg +=  b'\x00\x00\x00\x01\x98\x53\x00\x00\x00\x00\x01\x99\x53\x00\x00\x00\x00\x01\x9a\x53\x00\x00\x00\x00\x01\x9b\x53\x00\x00\x00\x00\x01\x9c\x53\x00\x00\x00\x00\x01\x9d\x53'
    msg +=  b'\x00\x00\x00\x00\x01\x9e\x53\x00\x00\x00\x00\x01\x9f\x53\x00\x00\x00\x00\x01\xa0\x53\x00\x00\x00\x00\x01\xf4\x49\x00\x00\x00\x00\x00\x00\x01\xf5\x53\x00\x00\x00\x00'
    msg +=  b'\x01\xf6\x53\x00\x00\x00\x00\x01\xf7\x53\x00\x00\x00\x00\x01\xf8\x53\x00\x00\x00\x00\x01\xf9\x53\x00\x00\x00\x00\x01\xfa\x53\x00\x00\x00\x00\x01\xfb\x53\x00\x00\x00'
    msg +=  b'\x00\x01\xfc\x53\x00\x00\x00\x00\x01\xfd\x53\x00\x00\x00\x00\x01\xfe\x53\x00\x00\x00\x00\x01\xff\x53\x00\x00\x00\x00\x02\x00\x53\x00\x00\x00\x00\x02\x01\x53\x00\x00'
    msg +=  b'\x00\x00\x02\x02\x53\x00\x00\x00\x00\x02\x03\x53\x00\x00\x00\x00\x02\x04\x53\x00\x00\x00\x00\x02\x58\x49\x00\x00\x00\x00\x00\x00\x02\x59\x53\x00\x00\x00\x00\x02\x5a'
    msg +=  b'\x53\x00\x00\x00\x00\x02\x5b\x53\x00\x00\x00\x00\x02\x5c\x53\x00\x00\x00\x00\x02\x5d\x53\x00\x00\x00\x00\x02\x5e\x53\x00\x00\x00\x00\x02\x5f\x53\x00\x00\x00\x00\x02'
    msg +=  b'\x60\x53\x00\x00\x00\x00\x02\x61\x53\x00\x00\x00\x00\x02\x62\x53\x00\x00\x00\x00\x02\x63\x53\x00\x00\x00\x00\x02\x64\x53\x00\x00\x00\x00\x02\x65\x53\x00\x00\x00\x00'
    msg +=  b'\x02\x66\x53\x00\x00\x00\x00\x02\x67\x53\x00\x00\x00\x00\x02\x68\x53\x00\x00\x00\x00\x02\xbc\x49\x00\x00\x00\x00\x00\x00\x02\xbd\x53\x00\x00\x00\x00\x02\xbe\x53\x00'
    msg +=  b'\x00\x00\x00\x02\xbf\x53\x00\x00\x00\x00\x02\xc0\x53\x00\x00\x00\x00\x02\xc1\x53\x00\x00\x00\x00\x02\xc2\x53\x00\x00\x00\x00\x02\xc3\x53\x00\x00\x00\x00\x02\xc4\x53'
    msg +=  b'\x00\x00\x00\x00\x02\xc5\x53\x00\x00\x00\x00\x02\xc6\x53\x00\x00\x00\x00\x02\xc7\x53\x00\x00\x00\x00\x02\xc8\x53\x00\x00\x00\x00\x02\xc9\x53\x00\x00\x00\x00\x02\xca'
    msg +=  b'\x53\x00\x00\x00\x00\x02\xcb\x53\x00\x00\x00\x00\x02\xcc\x53\x00\x00\x00\x00\x03\x20\x53\x00\x00\x00\x00\x03\x84\x53\x50\x11\x00\x00\x03\xe8\x46\x43\x61\x66\x66\x00'
    msg +=  b'\x00\x04\x4c\x46\x3e\xeb\x85\x1f\x00\x00\x04\xb0\x46\x42\x48\x14\x7b\x00\x00\x05\x14\x53\x00\x17\x00\x00\x05\x78\x53\x00\x00\x00\x00\x05\xdc\x53\x02\x58\x00\x00\x06'
    msg +=  b'\x40\x46\x42\xd3\x66\x66\x00\x00\x06\xa4\x46\x42\x06\x66\x66\x00\x00\x07\x08\x46\x3f\xf4\x7a\xe1\x00\x00\x07\x6c\x46\x42\x81\x00\x00\x00\x00\x07\xd0\x46\x42\x06\x00'
    msg +=  b'\x00\x00\x00\x08\x34\x46\x3f\xae\x14\x7b\x00\x00\x08\x98\x46\x42\x36\xcc\xcd\x00\x00\x08\xfc\x46\x00\x00\x00\x00\x00\x00\x09\x60\x46\x00\x00\x00\x00\x00\x00\x09\xc4'
    msg +=  b'\x46\x00\x00\x00\x00\x00\x00\x0a\x28\x46\x00\x00\x00\x00\x00\x00\x0a\x8c\x46\x00\x00\x00\x00\x00\x00\x0a\xf0\x46\x00\x00\x00\x00\x00\x00\x0b\x54\x46\x3f\xd9\x99\x9a'
    msg +=  b'\x00\x00\x0b\xb8\x46\x41\x8a\xe1\x48\x00\x00\x0c\x1c\x46\x3f\x8a\x3d\x71\x00\x00\x0c\x80\x46\x41\x1b\xd7\x0a\x00\x00\x0c\xe4\x46\x3f\x1e\xb8\x52\x00\x00\x0d\x48\x46'
    msg +=  b'\x40\xf3\xd7\x0a\x00\x00\x0d\xac\x46\x00\x00\x00\x00\x00\x00\x0e\x10\x46\x00\x00\x00\x00\x00\x00\x0e\x74\x46\x00\x00\x00\x00\x00\x00\x0e\xd8\x46\x00\x00\x00\x00\x00'
    msg +=  b'\x00\x0f\x3c\x53\x00\x00\x00\x00\x0f\xa0\x53\x00\x00\x00\x00\x10\x04\x53\x55\xaa\x00\x00\x10\x68\x53\x00\x00\x00\x00\x10\xcc\x53\x00\x00\x00\x00\x11\x30\x53\x00\x00'
    msg +=  b'\x00\x00\x11\x94\x53\x00\x00\x00\x00\x11\xf8\x53\xff\xff\x00\x00\x12\x5c\x53\xff\xff\x00\x00\x12\xc0\x53\x00\x02\x00\x00\x13\x24\x53\xff\xff\x00\x00\x13\x88\x53\xff'
    msg +=  b'\xff\x00\x00\x13\xec\x53\xff\xff\x00\x00\x14\x50\x53\xff\xff\x00\x00\x14\xb4\x53\xff\xff\x00\x00\x15\x18\x53\xff\xff\x00\x00\x15\x7c\x53\x00\x00\x00\x00\x27\x10\x53'
    msg +=  b'\x00\x02\x00\x00\x27\x74\x53\x00\x3c\x00\x00\x27\xd8\x53\x00\x68\x00\x00\x28\x3c\x53\x05\x00\x00\x00\x28\xa0\x46\x43\x79\x00\x00\x00\x00\x29\x04\x46\x43\x48\x00\x00'
    msg +=  b'\x00\x00\x29\x68\x46\x42\x48\x33\x33\x00\x00\x29\xcc\x46\x42\x3e\x3d\x71\x00\x00\x2a\x30\x53\x00\x01\x00\x00\x2a\x94\x46\x43\x37\x00\x00\x00\x00\x2a\xf8\x46\x42\xce'
    msg +=  b'\x00\x00\x00\x00\x2b\x5c\x53\x00\x96\x00\x00\x2b\xc0\x53\x00\x10\x00\x00\x2c\x24\x46\x43\x90\x00\x00\x00\x00\x2c\x88\x46\x43\x95\x00\x00\x00\x00\x2c\xec\x53\x00\x06'
    msg +=  b'\x00\x00\x2d\x50\x53\x00\x06\x00\x00\x2d\xb4\x46\x43\x7d\x00\x00\x00\x00\x2e\x18\x46\x42\x3d\xeb\x85\x00\x00\x2e\x7c\x46\x42\x3d\xeb\x85\x00\x00\x2e\xe0\x53\x00\x03'
    msg +=  b'\x00\x00\x2f\x44\x53\x00\x03\x00\x00\x2f\xa8\x46\x42\x4d\xeb\x85\x00\x00\x30\x0c\x46\x42\x4d\xeb\x85\x00\x00\x30\x70\x53\x00\x03\x00\x00\x30\xd4\x53\x00\x03\x00\x00'
    msg +=  b'\x31\x38\x46\x42\x08\x00\x00\x00\x00\x31\x9c\x53\x00\x05\x00\x00\x32\x00\x53\x04\x00\x00\x00\x32\x64\x53\x00\x01\x00\x00\x32\xc8\x53\x13\x9c\x00\x00\x33\x2c\x53\x0f'
    msg +=  b'\xa0\x00\x00\x33\x90\x53\x00\x4f\x00\x00\x33\xf4\x53\x00\x66\x00\x00\x34\x58\x53\x03\xe8\x00\x00\x34\xbc\x53\x04\x00\x00\x00\x35\x20\x53\x00\x00\x00\x00\x35\x84\x53'
    msg +=  b'\x00\x00\x00\x00\x35\xe8\x53\x00\x00\x00\x00\x36\x4c\x53\x00\x00\x00\x01\x38\x80\x53\x00\x02\x00\x01\x38\x81\x53\x00\x01\x00\x01\x38\x82\x53\x00\x01\x00\x01\x38\x83'
    msg +=  b'\x53\x00\x00'  
    return msg

@pytest.fixture
def msg_inverter_ind_new(): # Data indication from DSP V5.0.17
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
def msg_inverter_ind_new2(): # Data indication from DSP V5.0.17
    msg =  b'\x00\x00\x04\xf4\x10R170000000000001\x91\x04\x01\x90\x00\x01\x10R170000000000001'
    msg += b'\x01\x00\x00\x01'
    msg += b'\x86\x98\x55\xe7\x48\x00\x00\x00\xa3\x00\x00\x01\x93\x53\x00\x00'
    msg += b'\x00\x00\x01\x94\x53\x00\x00\x00\x00\x01\x95\x53\x00\x00\x00\x00'
    msg += b'\x01\x96\x53\x00\x00\x00\x00\x01\x97\x53\x00\x00\x00\x00\x01\x98'
    msg += b'\x53\x00\x00\x00\x00\x01\x99\x53\x00\x00\x00\x00\x01\x9a\x53\x00'
    msg += b'\x00\x00\x00\x01\x9b\x53\x00\x00\x00\x00\x01\x9c\x53\x00\x00\x00'
    msg += b'\x00\x01\x9d\x53\x00\x00\x00\x00\x01\x9e\x53\x00\x00\x00\x00\x01'
    msg += b'\x9f\x53\x00\x00\x00\x00\x01\xa0\x53\x00\x00\x00\x00\x01\xf4\x49'
    msg += b'\x00\x00\x00\x00\x00\x00\x01\xf5\x53\x00\x00\x00\x00\x01\xf6\x53'
    msg += b'\x00\x00\x00\x00\x01\xf7\x53\x00\x00\x00\x00\x01\xf8\x53\x00\x00'
    msg += b'\x00\x00\x01\xf9\x53\x00\x00\x00\x00\x01\xfa\x53\x00\x00\x00\x00'
    msg += b'\x01\xfb\x53\x00\x00\x00\x00\x01\xfc\x53\x00\x00\x00\x00\x01\xfd'
    msg += b'\x53\x00\x00\x00\x00\x01\xfe\x53\x00\x00\x00\x00\x01\xff\x53\x00'
    msg += b'\x00\x00\x00\x02\x00\x53\x00\x00\x00\x00\x02\x01\x53\x00\x00\x00'
    msg += b'\x00\x02\x02\x53\x00\x00\x00\x00\x02\x03\x53\x00\x00\x00\x00\x02'
    msg += b'\x04\x53\x00\x00\x00\x00\x02\x58\x49\x00\x00\x00\x00\x00\x00\x02'
    msg += b'\x59\x53\x00\x00\x00\x00\x02\x5a\x53\x00\x00\x00\x00\x02\x5b\x53'
    msg += b'\x00\x00\x00\x00\x02\x5c\x53\x00\x00\x00\x00\x02\x5d\x53\x00\x00'
    msg += b'\x00\x00\x02\x5e\x53\x00\x00\x00\x00\x02\x5f\x53\x00\x00\x00\x00'
    msg += b'\x02\x60\x53\x00\x00\x00\x00\x02\x61\x53\x00\x00\x00\x00\x02\x62'
    msg += b'\x53\x00\x00\x00\x00\x02\x63\x53\x00\x00\x00\x00\x02\x64\x53\x00'
    msg += b'\x00\x00\x00\x02\x65\x53\x00\x00\x00\x00\x02\x66\x53\x00\x00\x00'
    msg += b'\x00\x02\x67\x53\x00\x00\x00\x00\x02\x68\x53\x00\x00\x00\x00\x02'
    msg += b'\xbc\x49\x00\x00\x00\x00\x00\x00\x02\xbd\x53\x00\x00\x00\x00\x02'
    msg += b'\xbe\x53\x00\x00\x00\x00\x02\xbf\x53\x00\x00\x00\x00\x02\xc0\x53'
    msg += b'\x00\x00\x00\x00\x02\xc1\x53\x00\x00\x00\x00\x02\xc2\x53\x00\x00'
    msg += b'\x00\x00\x02\xc3\x53\x00\x00\x00\x00\x02\xc4\x53\x00\x00\x00\x00'
    msg += b'\x02\xc5\x53\x00\x00\x00\x00\x02\xc6\x53\x00\x00\x00\x00\x02\xc7'
    msg += b'\x53\x00\x00\x00\x00\x02\xc8\x53\x00\x00\x00\x00\x02\xc9\x53\x00'
    msg += b'\x00\x00\x00\x02\xca\x53\x00\x00\x00\x00\x02\xcb\x53\x00\x00\x00'
    msg += b'\x00\x02\xcc\x53\x00\x00\x00\x00\x03\x20\x53\x00\x00\x00\x00\x03'
    msg += b'\x84\x53\x50\x11\x00\x00\x03\xe8\x46\x43\x65\xcc\xcd\x00\x00\x04'
    msg += b'\x4c\x46\x40\x0c\xcc\xcd\x00\x00\x04\xb0\x46\x42\x47\xd7\x0a\x00'
    msg += b'\x00\x05\x14\x53\x00\x35\x00\x00\x05\x78\x53\x00\x00\x00\x00\x05'
    msg += b'\xdc\x53\x03\x20\x00\x00\x06\x40\x46\x43\xfd\x4c\xcd\x00\x00\x06'
    msg += b'\xa4\x46\x42\x18\x00\x00\x00\x00\x07\x08\x46\x40\xde\x14\x7b\x00'
    msg += b'\x00\x07\x6c\x46\x43\x84\x33\x33\x00\x00\x07\xd0\x46\x42\x1a\x00'
    msg += b'\x00\x00\x00\x08\x34\x46\x40\xda\x8f\x5c\x00\x00\x08\x98\x46\x43'
    msg += b'\x83\xb3\x33\x00\x00\x08\xfc\x46\x00\x00\x00\x00\x00\x00\x09\x60'
    msg += b'\x46\x00\x00\x00\x00\x00\x00\x09\xc4\x46\x00\x00\x00\x00\x00\x00'
    msg += b'\x0a\x28\x46\x00\x00\x00\x00\x00\x00\x0a\x8c\x46\x00\x00\x00\x00'
    msg += b'\x00\x00\x0a\xf0\x46\x00\x00\x00\x00\x00\x00\x0b\x54\x46\x40\x9c'
    msg += b'\xcc\xcd\x00\x00\x0b\xb8\x46\x43\xea\xb5\xc3\x00\x00\x0c\x1c\x46'
    msg += b'\x40\x1e\xb8\x52\x00\x00\x0c\x80\x46\x43\x6d\x2b\x85\x00\x00\x0c'
    msg += b'\xe4\x46\x40\x1a\xe1\x48\x00\x00\x0d\x48\x46\x43\x68\x40\x00\x00'
    msg += b'\x00\x0d\xac\x46\x00\x00\x00\x00\x00\x00\x0e\x10\x46\x00\x00\x00'
    msg += b'\x00\x00\x00\x0e\x74\x46\x00\x00\x00\x00\x00\x00\x0e\xd8\x46\x00'
    msg += b'\x00\x00\x00\x00\x00\x0f\x3c\x53\x00\x00\x00\x00\x0f\xa0\x53\x00'
    msg += b'\x00\x00\x00\x10\x04\x53\x55\xaa\x00\x00\x10\x68\x53\x00\x01\x00'
    msg += b'\x00\x10\xcc\x53\x00\x00\x00\x00\x11\x30\x53\x00\x00\x00\x00\x11'
    msg += b'\x94\x53\x00\x00\x00\x00\x11\xf8\x53\xff\xff\x00\x00\x12\x5c\x53'
    msg += b'\xff\xff\x00\x00\x12\xc0\x53\x00\x00\x00\x00\x13\x24\x53\xff\xff'
    msg += b'\x00\x00\x13\x88\x53\xff\xff\x00\x00\x13\xec\x53\xff\xff\x00\x00'
    msg += b'\x14\x50\x53\xff\xff\x00\x00\x14\xb4\x53\xff\xff\x00\x00\x15\x18'
    msg += b'\x53\xff\xff\x00\x00\x15\x7c\x53\x00\x00\x00\x00\x27\x10\x53\x00'
    msg += b'\x02\x00\x00\x27\x74\x53\x00\x3c\x00\x00\x27\xd8\x53\x00\x68\x00'
    msg += b'\x00\x28\x3c\x53\x05\x00\x00\x00\x28\xa0\x46\x43\x79\x00\x00\x00'
    msg += b'\x00\x29\x04\x46\x43\x48\x00\x00\x00\x00\x29\x68\x46\x42\x48\x33'
    msg += b'\x33\x00\x00\x29\xcc\x46\x42\x3e\x3d\x71\x00\x00\x2a\x30\x53\x00'
    msg += b'\x01\x00\x00\x2a\x94\x46\x43\x37\x00\x00\x00\x00\x2a\xf8\x46\x42'
    msg += b'\xce\x00\x00\x00\x00\x2b\x5c\x53\x00\x96\x00\x00\x2b\xc0\x53\x00'
    msg += b'\x10\x00\x00\x2c\x24\x46\x43\x90\x00\x00\x00\x00\x2c\x88\x46\x43'
    msg += b'\x95\x00\x00\x00\x00\x2c\xec\x53\x00\x06\x00\x00\x2d\x50\x53\x00'
    msg += b'\x06\x00\x00\x2d\xb4\x46\x43\x7d\x00\x00\x00\x00\x2e\x18\x46\x42'
    msg += b'\x3d\xeb\x85\x00\x00\x2e\x7c\x46\x42\x3d\xeb\x85\x00\x00\x2e\xe0'
    msg += b'\x53\x00\x03\x00\x00\x2f\x44\x53\x00\x03\x00\x00\x2f\xa8\x46\x42'
    msg += b'\x4d\xeb\x85\x00\x00\x30\x0c\x46\x42\x4d\xeb\x85\x00\x00\x30\x70'
    msg += b'\x53\x00\x03\x00\x00\x30\xd4\x53\x00\x03\x00\x00\x31\x38\x46\x42'
    msg += b'\x08\x00\x00\x00\x00\x31\x9c\x53\x00\x05\x00\x00\x32\x00\x53\x04'
    msg += b'\x00\x00\x00\x32\x64\x53\x00\x01\x00\x00\x32\xc8\x53\x13\x9c\x00'
    msg += b'\x00\x33\x2c\x53\x0f\xa0\x00\x00\x33\x90\x53\x00\x4f\x00\x00\x33'
    msg += b'\xf4\x53\x00\x66\x00\x00\x34\x58\x53\x03\xe8\x00\x00\x34\xbc\x53'
    msg += b'\x04\x00\x00\x00\x35\x20\x53\x00\x00\x00\x00\x35\x84\x53\x00\x00'
    msg += b'\x00\x00\x35\xe8\x53\x00\x00\x00\x00\x36\x4c\x53\x00\x00\x00\x01'
    msg += b'\x38\x80\x53\x00\x02\x00\x01\x38\x81\x53\x00\x01\x00\x01\x38\x82'
    msg += b'\x53\x00\x01\x00\x01\x38\x83\x53\x00\x00\x00\x00\x00\x0a\x08\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x14\x04\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x1e\x07\x00\x00\x00\x00\x00'
    return msg


@pytest.fixture
def msg_inverter_ind_0w(): # Data indication with 0.5W grid output
    msg =  b'\x00\x00\x05\x02\x10R170000000000001\x91\x04\x01\x90\x00\x01\x10R170000000000001'
    msg += b'\x01\x00\x00\x01'
    msg += b'\x90\x31\x4d\x68\x78'
    msg +=  b'\x00\x00\x00\xa3\x00\x00\x00\x64\x53\x00\x01\x00\x00\x00\xc8\x53\x00\x02\x00\x00\x01\x2c\x53\x00\x00\x00\x00\x01\x90\x49\x00\x00\x00\x00\x00\x00\x01\x91\x53\x00\x00'
    msg +=  b'\x00\x00\x01\x92\x53\x00\x00\x00\x00\x01\x93\x53\x00\x00\x00\x00\x01\x94\x53\x00\x00\x00\x00\x01\x95\x53\x00\x00\x00\x00\x01\x96\x53\x00\x00\x00\x00\x01\x97\x53\x00'
    msg +=  b'\x00\x00\x00\x01\x98\x53\x00\x00\x00\x00\x01\x99\x53\x00\x00\x00\x00\x01\x9a\x53\x00\x00\x00\x00\x01\x9b\x53\x00\x00\x00\x00\x01\x9c\x53\x00\x00\x00\x00\x01\x9d\x53'
    msg +=  b'\x00\x00\x00\x00\x01\x9e\x53\x00\x00\x00\x00\x01\x9f\x53\x00\x00\x00\x00\x01\xa0\x53\x00\x00\x00\x00\x01\xf4\x49\x00\x00\x00\x00\x00\x00\x01\xf5\x53\x00\x00\x00\x00'
    msg +=  b'\x01\xf6\x53\x00\x00\x00\x00\x01\xf7\x53\x00\x00\x00\x00\x01\xf8\x53\x00\x00\x00\x00\x01\xf9\x53\x00\x00\x00\x00\x01\xfa\x53\x00\x00\x00\x00\x01\xfb\x53\x00\x00\x00'
    msg +=  b'\x00\x01\xfc\x53\x00\x00\x00\x00\x01\xfd\x53\x00\x00\x00\x00\x01\xfe\x53\x00\x00\x00\x00\x01\xff\x53\x00\x00\x00\x00\x02\x00\x53\x00\x00\x00\x00\x02\x01\x53\x00\x00'
    msg +=  b'\x00\x00\x02\x02\x53\x00\x00\x00\x00\x02\x03\x53\x00\x00\x00\x00\x02\x04\x53\x00\x00\x00\x00\x02\x58\x49\x00\x00\x00\x00\x00\x00\x02\x59\x53\x00\x00\x00\x00\x02\x5a'
    msg +=  b'\x53\x00\x00\x00\x00\x02\x5b\x53\x00\x00\x00\x00\x02\x5c\x53\x00\x00\x00\x00\x02\x5d\x53\x00\x00\x00\x00\x02\x5e\x53\x00\x00\x00\x00\x02\x5f\x53\x00\x00\x00\x00\x02'
    msg +=  b'\x60\x53\x00\x00\x00\x00\x02\x61\x53\x00\x00\x00\x00\x02\x62\x53\x00\x00\x00\x00\x02\x63\x53\x00\x00\x00\x00\x02\x64\x53\x00\x00\x00\x00\x02\x65\x53\x00\x00\x00\x00'
    msg +=  b'\x02\x66\x53\x00\x00\x00\x00\x02\x67\x53\x00\x00\x00\x00\x02\x68\x53\x00\x00\x00\x00\x02\xbc\x49\x00\x00\x00\x00\x00\x00\x02\xbd\x53\x00\x00\x00\x00\x02\xbe\x53\x00'
    msg +=  b'\x00\x00\x00\x02\xbf\x53\x00\x00\x00\x00\x02\xc0\x53\x00\x00\x00\x00\x02\xc1\x53\x00\x00\x00\x00\x02\xc2\x53\x00\x00\x00\x00\x02\xc3\x53\x00\x00\x00\x00\x02\xc4\x53'
    msg +=  b'\x00\x00\x00\x00\x02\xc5\x53\x00\x00\x00\x00\x02\xc6\x53\x00\x00\x00\x00\x02\xc7\x53\x00\x00\x00\x00\x02\xc8\x53\x00\x00\x00\x00\x02\xc9\x53\x00\x00\x00\x00\x02\xca'
    msg +=  b'\x53\x00\x00\x00\x00\x02\xcb\x53\x00\x00\x00\x00\x02\xcc\x53\x00\x00\x00\x00\x03\x20\x53\x00\x00\x00\x00\x03\x84\x53\x50\x11\x00\x00\x03\xe8\x46\x43\x61\x66\x66\x00'
    msg +=  b'\x00\x04\x4c\x46\x3e\xeb\x85\x1f\x00\x00\x04\xb0\x46\x42\x48\x14\x7b\x00\x00\x05\x14\x53\x00\x17\x00\x00\x05\x78\x53\x00\x00\x00\x00\x05\xdc\x53\x02\x58\x00\x00\x06'
    msg += b'\x40\x46\x3f\x00\x00\x00\x00\x00\x06\xa4\x46\x42\x06\x66\x66\x00\x00\x07\x08\x46\x3f\xf4\x7a\xe1\x00\x00\x07\x6c\x46\x42\x81\x00\x00\x00\x00\x07\xd0\x46\x42\x06\x00'
    msg +=  b'\x00\x00\x00\x08\x34\x46\x3f\xae\x14\x7b\x00\x00\x08\x98\x46\x42\x36\xcc\xcd\x00\x00\x08\xfc\x46\x00\x00\x00\x00\x00\x00\x09\x60\x46\x00\x00\x00\x00\x00\x00\x09\xc4'
    msg +=  b'\x46\x00\x00\x00\x00\x00\x00\x0a\x28\x46\x00\x00\x00\x00\x00\x00\x0a\x8c\x46\x00\x00\x00\x00\x00\x00\x0a\xf0\x46\x00\x00\x00\x00\x00\x00\x0b\x54\x46\x3f\xd9\x99\x9a'
    msg +=  b'\x00\x00\x0b\xb8\x46\x41\x8a\xe1\x48\x00\x00\x0c\x1c\x46\x3f\x8a\x3d\x71\x00\x00\x0c\x80\x46\x41\x1b\xd7\x0a\x00\x00\x0c\xe4\x46\x3f\x1e\xb8\x52\x00\x00\x0d\x48\x46'
    msg +=  b'\x40\xf3\xd7\x0a\x00\x00\x0d\xac\x46\x00\x00\x00\x00\x00\x00\x0e\x10\x46\x00\x00\x00\x00\x00\x00\x0e\x74\x46\x00\x00\x00\x00\x00\x00\x0e\xd8\x46\x00\x00\x00\x00\x00'
    msg +=  b'\x00\x0f\x3c\x53\x00\x00\x00\x00\x0f\xa0\x53\x00\x00\x00\x00\x10\x04\x53\x55\xaa\x00\x00\x10\x68\x53\x00\x00\x00\x00\x10\xcc\x53\x00\x00\x00\x00\x11\x30\x53\x00\x00'
    msg +=  b'\x00\x00\x11\x94\x53\x00\x00\x00\x00\x11\xf8\x53\xff\xff\x00\x00\x12\x5c\x53\xff\xff\x00\x00\x12\xc0\x53\x00\x02\x00\x00\x13\x24\x53\xff\xff\x00\x00\x13\x88\x53\xff'
    msg +=  b'\xff\x00\x00\x13\xec\x53\xff\xff\x00\x00\x14\x50\x53\xff\xff\x00\x00\x14\xb4\x53\xff\xff\x00\x00\x15\x18\x53\xff\xff\x00\x00\x15\x7c\x53\x00\x00\x00\x00\x27\x10\x53'
    msg +=  b'\x00\x02\x00\x00\x27\x74\x53\x00\x3c\x00\x00\x27\xd8\x53\x00\x68\x00\x00\x28\x3c\x53\x05\x00\x00\x00\x28\xa0\x46\x43\x79\x00\x00\x00\x00\x29\x04\x46\x43\x48\x00\x00'
    msg +=  b'\x00\x00\x29\x68\x46\x42\x48\x33\x33\x00\x00\x29\xcc\x46\x42\x3e\x3d\x71\x00\x00\x2a\x30\x53\x00\x01\x00\x00\x2a\x94\x46\x43\x37\x00\x00\x00\x00\x2a\xf8\x46\x42\xce'
    msg +=  b'\x00\x00\x00\x00\x2b\x5c\x53\x00\x96\x00\x00\x2b\xc0\x53\x00\x10\x00\x00\x2c\x24\x46\x43\x90\x00\x00\x00\x00\x2c\x88\x46\x43\x95\x00\x00\x00\x00\x2c\xec\x53\x00\x06'
    msg +=  b'\x00\x00\x2d\x50\x53\x00\x06\x00\x00\x2d\xb4\x46\x43\x7d\x00\x00\x00\x00\x2e\x18\x46\x42\x3d\xeb\x85\x00\x00\x2e\x7c\x46\x42\x3d\xeb\x85\x00\x00\x2e\xe0\x53\x00\x03'
    msg +=  b'\x00\x00\x2f\x44\x53\x00\x03\x00\x00\x2f\xa8\x46\x42\x4d\xeb\x85\x00\x00\x30\x0c\x46\x42\x4d\xeb\x85\x00\x00\x30\x70\x53\x00\x03\x00\x00\x30\xd4\x53\x00\x03\x00\x00'
    msg +=  b'\x31\x38\x46\x42\x08\x00\x00\x00\x00\x31\x9c\x53\x00\x05\x00\x00\x32\x00\x53\x04\x00\x00\x00\x32\x64\x53\x00\x01\x00\x00\x32\xc8\x53\x13\x9c\x00\x00\x33\x2c\x53\x0f'
    msg +=  b'\xa0\x00\x00\x33\x90\x53\x00\x4f\x00\x00\x33\xf4\x53\x00\x66\x00\x00\x34\x58\x53\x03\xe8\x00\x00\x34\xbc\x53\x04\x00\x00\x00\x35\x20\x53\x00\x00\x00\x00\x35\x84\x53'
    msg +=  b'\x00\x00\x00\x00\x35\xe8\x53\x00\x00\x00\x00\x36\x4c\x53\x00\x00\x00\x01\x38\x80\x53\x00\x02\x00\x01\x38\x81\x53\x00\x01\x00\x01\x38\x82\x53\x00\x01\x00\x01\x38\x83'
    msg +=  b'\x53\x00\x00'  
    return msg

@pytest.fixture
def msg_inverter_ack(): # Get Time Request message
    return b'\x00\x00\x00\x14\x10R170000000000001\x99\x04\x01'

@pytest.fixture
def msg_inverter_invalid(): # Get Time Request message
    return b'\x00\x00\x00\x14\x10R170000000000001\x92\x04\x01'

@pytest.fixture
def msg_unknown(): # Get Time Request message
    return b'\x00\x00\x00\x17\x10R170000000000001\x91\x17\x01\x02\x03\x04'

@pytest.fixture
def config_tsun_allow_all():
    Config.act_config = {'tsun':{'enabled': True}, 'inverters':{'allow_all':True}}

@pytest.fixture
def config_no_tsun_inv1():
    Config.act_config = {'tsun':{'enabled': False},'inverters':{'R170000000000001':{'node_id':'inv1', 'sensor_list': 0, 'modbus_polling': True, 'suggested_area':'roof'}}}

@pytest.fixture
def config_tsun_inv1():
    Config.act_config = {'tsun':{'enabled': True},'inverters':{'R170000000000001':{'node_id':'inv1', 'sensor_list': 0x01900001, 'modbus_polling': True, 'suggested_area':'roof'}}}

@pytest.fixture
def config_no_modbus_poll():
    Config.act_config = {'tsun':{'enabled': True},'inverters':{'R170000000000001':{'node_id':'inv1', 'sensor_list': 0, 'modbus_polling': False, 'suggested_area':'roof'}}}

@pytest.fixture
def msg_ota_req(): # Over the air update request from tsun cloud
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
def msg_ota_ack(): # Over the air update rewuest from tsun cloud
    return b'\x00\x00\x00\x14\x10R170000000000001\x91\x13\x01'

@pytest.fixture
def msg_ota_invalid(): # Get Time Request message
    return b'\x00\x00\x00\x14\x10R170000000000001\x99\x13\x01'

@pytest.fixture
def msg_modbus_cmd():
    msg  = b'\x00\x00\x00\x20\x10R170000000000001'
    msg += b'\x70\x77\x00\x01\xa3\x28\x08\x01\x06\x20\x08'
    msg += b'\x00\x00\x03\xc8'
    return msg

@pytest.fixture
def msg_modbus_cmd_crc_err():
    msg  = b'\x00\x00\x00\x20\x10R170000000000001'
    msg += b'\x70\x77\x00\x01\xa3\x28\x08\x01\x06\x20\x08'
    msg += b'\x00\x00\x04\xc8'
    return msg

@pytest.fixture
def msg_modbus_rsp():
    msg  = b'\x00\x00\x00\x20\x10R170000000000001'
    msg += b'\x91\x77\x17\x18\x19\x1a\x08\x01\x06\x20\x08'
    msg += b'\x00\x00\x03\xc8'
    return msg

@pytest.fixture
def msg_modbus_inv():
    msg  = b'\x00\x00\x00\x20\x10R170000000000001'
    msg += b'\x99\x77\x17\x18\x19\x1a\x08\x01\x06\x20\x08'
    msg += b'\x00\x00\x03\xc8'
    return msg

@pytest.fixture
def msg_modbus_rsp20():
    msg  = b'\x00\x00\x00\x45\x10R170000000000001'
    msg += b'\x91\x77\x17\x18\x19\x1a\x2d\x01\x03\x28\x51'
    msg += b'\x09\x08\xd3\x00\x29\x13\x87\x00\x3e\x00\x00\x01\x2c\x03\xb4\x00'
    msg += b'\x08\x00\x00\x00\x00\x01\x59\x01\x21\x03\xe6\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\xdb\x6b'
    return msg

@pytest.fixture
def msg_modbus_rsp21():
    msg  = b'\x00\x00\x00\x45\x10R170000000000001'
    msg += b'\x91\x77\x17\x18\x19\x1a\x2d\x01\x03\x28\x51'
    msg += b'\x0e\x08\xd3\x00\x29\x13\x87\x00\x3e\x00\x00\x01\x2c\x03\xb4\x00'
    msg += b'\x08\x00\x00\x00\x00\x01\x59\x01\x21\x03\xe6\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\xe6\xef'
    return msg

@pytest.fixture
def msg_modbus_cmd_new():
    msg  = b'\x00\x00\x00\x20\x10R170000000000001'
    msg += b'\x70\x77\x00\x01\xa3\x28\x08\x01\x03\x30\x00'
    msg += b'\x00\x30\x4a\xde'
    return msg

@pytest.fixture
def msg_modbus_rsp20_new():
    msg  = b'\x00\x00\x00\x7e\x10R170000000000001'
    msg += b'\x91\x87\x00\x01\xa3\x28\x00\x65\x01\x03\x60'
    msg += b'\x00\x01\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x51\x09\x09\x17\x00\x17\x13\x88\x00\x40\x00\x00\x02\x58\x02\x23'
    msg += b'\x00\x07\x00\x00\x00\x00\x01\x4f\x00\xab\x02\x40\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\xc0\x93\x00\x00'
    msg += b'\x00\x00\x33\xad\x00\x09\x00\x00\x98\x1c\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\xa7\xab'
    return msg

@pytest.fixture
def broken_recv_buf(): # There are two message in the buffer, but the second has overwritten the first partly
    msg  = b'\x00\x00\x05\x02\x10R170000000000001\x91\x04\x01\x90\x00\x01\x10R170000000000001'
    msg += b'\x01\x00\x00\x01\x89\xc6\x63\x61\x08'
    msg += b'\x00\x00\x00\xa3\x00\x00\x00\x64\x53\x00\x01'
    msg += b'\x00\x00\x00\xc8\x53\x00\x00\x00\x00\x01\x2c\x53\x00\x02\x00\x00'
    msg += b'\x01\x90\x49\x00\x00\x00\x00\x00\x00\x01\x91\x53\x00\x00\x00\x00'
    msg += b'\x01\x92\x53\x00\x00\x00\x00\x01\x93\x53\x00\x00\x00\x00\x01\x94'
    msg += b'\x53\x00\x00\x00\x00\x00\x05\x02\x10\x52\x31\x37\x45\x37\x33\x30'
    msg += b'\x37\x30\x32\x31\x44\x30\x30\x36\x41\x91\x04\x01\x90\x00\x01\x10'
    msg += b'\x54\x31\x37\x45\x37\x33\x30\x37\x30\x32\x31\x44\x30\x30\x36\x41'
    msg += b'\x01\x00\x00\x01\x91\x1c\xe6\x80\xd0\x00\x00\x00\xa3\x00\x00\x00'
    msg += b'\x64\x53\x00\x01\x00\x00\x00\xc8\x53\x00\x00\x00\x00\x01\x2c\x53'
    msg += b'\x00\x02\x00\x00\x01\x90\x49\x00\x00\x00\x00\x00\x00\x01\x91\x53'
    msg += b'\x00\x00\x00\x00\x01\x92\x53\x00\x00\x00\x00\x01\x93\x53\x00\x00'
    msg += b'\x00\x00\x01\x94\x53\x00\x00\x00\x00\x01\x95\x53\x00\x00\x00\x00'
    msg += b'\x01\x96\x53\x00\x00\x00\x00\x01\x97\x53\x00\x00\x00\x00\x01\x98'
    msg += b'\x53\x00\x00\x00\x00\x01\x99\x53\x00\x00\x00\x00\x01\x9a\x53\x00'
    msg += b'\x00\x00\x00\x01\x9b\x53\x00\x00\x00\x00\x01\x9c\x53\x00\x00\x00'
    msg += b'\x00\x01\x9d\x53\x00\x00\x00\x00\x01\x9e\x53\x00\x00\x00\x00\x01'
    msg += b'\x9f\x53\x00\x00\x00\x00\x01\xa0\x53\x00\x00\x00\x00\x01\xf4\x49'
    msg += b'\x00\x00\x00\x00\x00\x00\x01\xf5\x53\x00\x00\x00\x00\x01\xf6\x53'
    msg += b'\x00\x00\x00\x00\x01\xf7\x53\x00\x00\x00\x00\x01\xf8\x53\x00\x00'
    msg += b'\x00\x00\x01\xf9\x53\x00\x00\x00\x00\x01\xfa\x53\x00\x00\x00\x00'
    msg += b'\x01\xfb\x53\x00\x00\x00\x00\x01\xfc\x53\x00\x00\x00\x00\x01\xfd'
    msg += b'\x53\x00\x00\x00\x00\x01\xfe\x53\x00\x00\x00\x00\x01\xff\x53\x00'
    msg += b'\x00\x00\x00\x02\x00\x53\x00\x00\x00\x00\x02\x01\x53\x00\x00\x00'
    msg += b'\x00\x02\x02\x53\x00\x00\x00\x00\x02\x03\x53\x00\x00\x00\x00\x02'
    msg += b'\x04\x53\x00\x00\x00\x00\x02\x58\x49\x00\x00\x00\x00\x00\x00\x02'
    msg += b'\x59\x53\x00\x00\x00\x00\x02\x5a\x53\x00\x00\x00\x00\x02\x5b\x53'
    msg += b'\x00\x00\x00\x00\x02\x5c\x53\x00\x00\x00\x00\x02\x5d\x53\x00\x00'
    msg += b'\x00\x00\x02\x5e\x53\x00\x00\x00\x00\x02\x5f\x53\x00\x00\x00\x00'
    msg += b'\x02\x60\x53\x00\x00\x00\x00\x02\x61\x53\x00\x00\x00\x00\x02\x62'
    msg += b'\x53\x00\x00\x00\x00\x02\x63\x53\x00\x00\x00\x00\x02\x64\x53\x00'
    msg += b'\x00\x00\x00\x02\x65\x53\x00\x00\x00\x00\x02\x66\x53\x00\x00\x00'
    msg += b'\x00\x02\x67\x53\x00\x00\x00\x00\x02\x68\x53\x00\x00\x00\x00\x02'
    msg += b'\xbc\x49\x00\x00\x00\x00\x00\x00\x02\xbd\x53\x00\x00\x00\x00\x02'
    msg += b'\xbe\x53\x00\x00\x00\x00\x02\xbf\x53\x00\x00\x00\x00\x02\xc0\x53'
    msg += b'\x00\x00\x00\x00\x02\xc1\x53\x00\x00\x00\x00\x02\xc2\x53\x00\x00'
    msg += b'\x00\x00\x02\xc3\x53\x00\x00\x00\x00\x02\xc4\x53\x00\x00\x00\x00'
    msg += b'\x02\xc5\x53\x00\x00\x00\x00\x02\xc6\x53\x00\x00\x00\x00\x02\xc7'
    msg += b'\x53\x00\x00\x00\x00\x02\xc8\x53\x00\x00\x00\x00\x02\xc9\x53\x00'
    msg += b'\x00\x00\x00\x02\xca\x53\x00\x00\x00\x00\x02\xcb\x53\x00\x00\x00'
    msg += b'\x00\x02\xcc\x53\x00\x00\x00\x00\x03\x20\x53\x00\x00\x00\x00\x03'
    msg += b'\x84\x53\x51\x09\x00\x00\x03\xe8\x46\x43\x62\xb3\x33\x00\x00\x04'
    msg += b'\x4c\x46\x3e\xc2\x8f\x5c\x00\x00\x04\xb0\x46\x42\x48\x00\x00\x00'
    msg += b'\x00\x05\x14\x53\x00\x18\x00\x00\x05\x78\x53\x00\x00\x00\x00\x05'
    msg += b'\xdc\x53\x02\x58\x00\x00\x06\x40\x46\x42\xae\xcc\xcd\x00\x00\x06'
    msg += b'\xa4\x46\x3f\x4c\xcc\xcd\x00\x00\x07\x08\x46\x00\x00\x00\x00\x00'
    msg += b'\x00\x07\x6c\x46\x00\x00\x00\x00\x00\x00\x07\xd0\x46\x42\x0a\x66'
    msg += b'\x66\x00\x00\x08\x34\x46\x40\x2a\x3d\x71\x00\x00\x08\x98\x46\x42'
    msg += b'\xb8\x33\x33\x00\x00\x08\xfc\x46\x00\x00\x00\x00\x00\x00\x09\x60'
    msg += b'\x46\x00\x00\x00\x00\x00\x00\x09\xc4\x46\x00\x00\x00\x00\x00\x00'
    msg += b'\x0a\x28\x46\x00\x00\x00\x00\x00\x00\x0a\x8c\x46\x00\x00\x00\x00'
    msg += b'\x00\x00\x0a\xf0\x46\x00\x00\x00\x00\x00\x00\x0b\x54\x46\x3e\x05'
    msg += b'\x1e\xb8\x00\x00\x0b\xb8\x46\x43\xe2\x42\x8f\x00\x00\x0c\x1c\x46'
    msg += b'\x00\x00\x00\x00\x00\x00\x0c\x80\x46\x43\x04\x4a\x3d\x00\x00\x0c'
    msg += b'\xe4\x46\x3e\x0f\x5c\x29\x00\x00\x0d\x48\x46\x43\xad\x48\xf6\x00'
    msg += b'\x00\x0d\xac\x46\x00\x00\x00\x00\x00\x00\x0e\x10\x46\x00\x00\x00'
    msg += b'\x00\x00\x00\x0e\x74\x46\x00\x00\x00\x00\x00\x00\x0e\xd8\x46\x00'
    msg += b'\x00\x00\x00\x00\x00\x0f\x3c\x53\x00\x00\x00\x00\x0f\xa0\x53\x00'
    msg += b'\x00\x00\x00\x10\x04\x53\x55\xaa\x00\x00\x10\x68\x53\x00\x01\x00'
    msg += b'\x00\x10\xcc\x53\x00\x00\x00\x00\x11\x30\x53\x00\x00\x00\x00\x11'
    msg += b'\x94\x53\x00\x00\x00\x00\x11\xf8\x53\xff\xff\x00\x00\x12\x5c\x53'
    msg += b'\x03\x20\x00\x00\x12\xc0\x53\x00\x02\x00\x00\x13\x24\x53\x04\x00'
    msg += b'\x00\x00\x13\x88\x53\x04\x00\x00\x00\x13\xec\x53\x04\x00\x00\x00'
    msg += b'\x14\x50\x53\x04\x00\x00\x00\x14\xb4\x53\x00\x01\x00\x00\x15\x18'
    msg += b'\x53\x08\x04\x00\x00\x15\x7c\x53\x00\x00\x00\x00\x27\x10\x53\x00'
    msg += b'\x02\x00\x00\x27\x74\x53\x00\x3c\x00\x00\x27\xd8\x53\x00\x68\x00'
    msg += b'\x00\x28\x3c\x53\x05\x00\x00\x00\x28\xa0\x46\x43\x79\x00\x00\x00'
    msg += b'\x00\x29\x04\x46\x43\x48\x00\x00\x00\x00\x29\x68\x46\x42\x48\x33'
    msg += b'\x33\x00\x00\x29\xcc\x46\x42\x3e\x3d\x71\x00\x00\x2a\x30\x53\x00'
    msg += b'\x01\x00\x00\x2a\x94\x46\x43\x37\x00\x00\x00\x00\x2a\xf8\x46\x42'
    msg += b'\xce\x00\x00\x00\x00\x2b\x5c\x53\x00\x96\x00\x00\x2b\xc0\x53\x00'
    msg += b'\x10\x00\x00\x2c\x24\x46\x43\x90\x00\x00\x00\x00\x2c\x88\x46\x43'
    msg += b'\x95\x00\x00\x00\x00\x2c\xec\x53\x00\x06\x00\x00\x2d\x50\x53\x00'
    msg += b'\x06\x00\x00\x2d\xb4\x46\x43\x7d\x00\x00\x00\x00\x2e\x18\x46\x42'
    msg += b'\x3d\xeb\x85\x00\x00\x2e\x7c\x46\x42\x3d\xeb\x85\x00\x00\x2e\xe0'
    msg += b'\x53\x00\x03\x00\x00\x2f\x44\x53\x00\x03\x00\x00\x2f\xa8\x46\x42'
    msg += b'\x4d\xeb\x85\x00\x00\x30\x0c\x46\x42\x4d\xeb\x85\x00\x00\x30\x70'
    msg += b'\x53\x00\x03\x00\x00\x30\xd4\x53\x00\x03\x00\x00\x31\x38\x46\x42'
    msg += b'\x08\x00\x00\x00\x00\x31'
    return msg

@pytest.fixture
def multiple_recv_buf(): # There are three message in the buffer, but the second has overwritten the first partly
    msg  = b'\x00\x00\x05\x02\x10R170000000000001\x91\x04\x01\x90\x00\x01\x10R170000000000001'
    msg += b'\x01\x00\x00\x01\x89\xc6\x63\x61\x08'
    msg += b'\x00\x00\x00\xa3\x00\x00\x00\x64\x53\x00\x01'
    msg += b'\x00\x00\x00\xc8\x53\x00\x00\x00\x00\x01\x2c\x53\x00\x02\x00\x00'  #  | ....S.....,S....
    msg += b'\x01\x90\x49\x00\x00\x00\x00\x00\x00\x01\x91\x53\x00\x00\x00\x00'  #  | ..I........S....
    msg += b'\x13\x10\x52\x31\x37\x45\x37\x33\x30\x37\x30\x32\x31\x44\x30\x30'  #  | ..R17E7307021D00
    msg += b'\x36\x41\x91\x22\x00\x00\x03\xbf\x10\x52\x31\x37\x45\x37\x33\x30'  #  | 6A.".....R17E730
    msg += b'\x37\x30\x32\x31\x44\x30\x30\x36\x41\x91\x71\x0e\x10\x00\x00\x10'  #  | 7021D006A.q.....
    msg += b'\x52\x31\x37\x45\x37\x33\x30\x37\x30\x32\x31\x44\x30\x30\x36\x41'  #  | R17E7307021D006A
    msg += b'\x01\x00\x00\x01\x91\xa3\xfe\xaf\x98\x00\x00\x00\x35\x00\x09\x2b'  #  | ............5..+
    msg += b'\xa8\x54\x10\x52\x53\x57\x5f\x34\x30\x30\x5f\x56\x31\x2e\x30\x30'  #  | .T.RSW_400_V1.00
    msg += b'\x2e\x31\x37\x00\x09\x27\xc0\x54\x06\x52\x61\x79\x6d\x6f\x6e\x00'  #  | .17..'.T.Raymon.
    msg += b'\x09\x2f\x90\x54\x0b\x52\x53\x57\x2d\x31\x2d\x31\x30\x30\x30\x31'  #  | ./.T.RSW-1-10001
    msg += b'\x00\x09\x5a\x88\x54\x0f\x74\x2e\x72\x61\x79\x6d\x6f\x6e\x69\x6f'  #  | ..Z.T.t.raymonio
    msg += b'\x74\x2e\x63\x6f\x6d\x00\x09\x5a\xec\x54\x1c\x6c\x6f\x67\x67\x65'  #  | t.com..Z.T.logge
    msg += b'\x72\x2e\x74\x61\x6c\x65\x6e\x74\x2d\x6d\x6f\x6e\x69\x74\x6f\x72'  #  | r.talent-monitor
    msg += b'\x69\x6e\x67\x2e\x63\x6f\x6d\x00\x0d\x2f\x00\x54\x10\xff\xff\xff'  #  | ing.com../.T....
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x32'  #  | ...............2
    msg += b'\xe8\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  #  | .T..............
    msg += b'\xff\xff\xff\x00\x0d\x36\xd0\x54\x10\xff\xff\xff\xff\xff\xff\xff'  #  | .....6.T........
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x3a\xb8\x54\x10\xff'  #  | ...........:.T..
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'  #  | ................
    msg += b'\x0d\x3e\xa0\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  #  | .>.T............
    msg += b'\xff\xff\xff\xff\xff\x00\x0d\x42\x88\x54\x10\xff\xff\xff\xff\xff'  #  | .......B.T......
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x46\x70\x54'  #  | .............FpT
    msg += b'\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  #  | ................
    msg += b'\xff\x00\x0d\x4a\x58\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff'  #  | ...JXT..........
    msg += b'\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x4e\x40\x54\x10\xff\xff\xff'  #  | .........N@T....
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x52'  #  | ...............R
    msg += b'\x28\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  #  | (T..............
    msg += b'\xff\xff\xff\x00\x0d\x56\x10\x54\x10\xff\xff\xff\xff\xff\xff\xff'  #  | .....V.T........
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x59\xf8\x54\x10\xff'  #  | ...........Y.T..
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'  #  | ................
    msg += b'\x0d\x5d\xe0\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  #  | .].T............
    msg += b'\xff\xff\xff\xff\xff\x00\x0d\x61\xc8\x54\x10\xff\xff\xff\xff\xff'  #  | .......a.T......
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x65\xb0\x54'  #  | .............e.T
    msg += b'\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  #  | ................
    msg += b'\xff\x00\x0d\x69\x98\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff'  #  | ...i.T..........
    msg += b'\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x6d\x80\x54\x10\xff\xff\xff'  #  | .........m.T....
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x71'  #  | ...............q
    msg += b'\x68\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  #  | hT..............
    msg += b'\xff\xff\xff\x00\x0d\x75\x50\x54\x10\xff\xff\xff\xff\xff\xff\xff'  #  | .....uPT........
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x79\x38\x54\x10\xff'  #  | ...........y8T..
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'  #  | ................
    msg += b'\x0d\x7d\x20\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  #  | .} T............
    msg += b'\xff\xff\xff\xff\xff\x00\x0d\x81\x08\x54\x10\xff\xff\xff\xff\xff'  #  | .........T......
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x84\xf0\x54'  #  | ...............T
    msg += b'\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  #  | ................
    msg += b'\xff\x00\x0d\x88\xd8\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff'  #  | .....T..........
    msg += b'\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x8c\xc0\x54\x10\xff\xff\xff'  #  | ...........T....
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x90'  #  | ................
    msg += b'\xa8\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  #  | .T..............
    msg += b'\xff\xff\xff\x00\x0d\x94\x90\x54\x10\xff\xff\xff\xff\xff\xff\xff'  #  | .......T........
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x98\x78\x54\x10\xff'  #  | ............xT..
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'  #  | ................
    msg += b'\x0d\x00\x20\x49\x00\x00\x00\x01\x00\x0c\x35\x00\x49\x00\x00\x00'  #  | .. I......5.I...
    msg += b'\x28\x00\x0c\x96\xa8\x49\x00\x00\x01\x69\x00\x0c\x7f\x38\x49\x00'  #  | (....I...i...8I.
    msg += b'\x00\x00\x01\x00\x0c\xfc\x38\x49\x00\x00\x00\x01\x00\x0c\xf8\x50'  #  | ......8I.......P
    msg += b'\x49\x00\x00\x01\x2c\x00\x0c\x63\xe0\x49\x00\x00\x00\x00\x00\x0c'  #  | I...,..c.I......
    msg += b'\x67\xc8\x49\x00\x00\x00\x00\x00\x0c\x50\x58\x49\x00\x00\x00\x01'  #  | g.I......PXI....
    msg += b'\x00\x09\x5e\x70\x49\x00\x00\x13\x8d\x00\x09\x5e\xd4\x49\x00\x00'  #  | ..^pI......^.I..
    msg += b'\x13\x8d\x00\x09\x5b\x50\x49\x00\x00\x00\x02\x00\x0d\x04\x08\x49'  #  | ....[PI........I
    msg += b'\x00\x00\x00\x00\x00\x07\xa1\x84\x49\x00\x00\x00\x01\x00\x0c\x50'  #  | ........I......P
    msg += b'\x59\x49\x00\x00\x00\x3e\x00\x0d\x1f\x60\x49\x00\x00\x00\x00\x00'  #  | YI...>...`I.....
    msg += b'\x0d\x23\x48\x49\xff\xff\xff\xff\x00\x0d\x27\x30\x49\xff\xff\xff'  #  | .#HI......'0I...
    msg += b'\xff\x00\x0d\x2b\x18\x4c\x00\x00\x00\x00\xff\xff\xff\xff\x00\x0c'  #  | ...+.L..........
    msg += b'\xa2\x60\x49\x00\x00\x00\x00\x00\x00\x05\x02\x10\x52\x31\x37\x45'  #  | .`I.........R17E
    msg += b'\x37\x33\x30\x37\x30\x32\x31\x44\x30\x30\x36\x41\x91\x04\x01\x90'  #  | 7307021D006A....
    msg += b'\x00\x01\x10\x54\x31\x37\x45\x37\x33\x30\x37\x30\x32\x31\x44\x30'  #  | ...T17E7307021D0
    msg += b'\x30\x36\x41\x01\x00\x00\x01\x91\xa3\xfe\xb3\x80\x00\x00\x00\xa3'  #  | 06A.............
    msg += b'\x00\x00\x00\x64\x53\x00\x01\x00\x00\x00\xc8\x53\x00\x00\x00\x00'  #  | ...dS......S....
    msg += b'\x01\x2c\x53\x00\x02\x00\x00\x01\x90\x49\x00\x00\x00\x00\x00\x00'  #  | .,S......I......
    msg += b'\x01\x91\x53\x00\x00\x00\x00\x01\x92\x53\x00\x00\x00\x00\x01\x93'  #  | ..S......S......
    msg += b'\x53\x00\x00\x00\x00\x01\x94\x53\x00\x00\x00\x00\x01\x95\x53\x00'  #  | S......S......S.
    msg += b'\x00\x00\x00\x01\x96\x53\x00\x00\x00\x00\x01\x97\x53\x00\x00\x00'  #  | .....S......S...
    msg += b'\x00\x01\x98\x53\x00\x00\x00\x00\x01\x99\x53\x00\x00\x00\x00\x01'  #  | ...S......S.....
    msg += b'\x9a\x53\x00\x00\x00\x00\x01\x9b\x53\x00\x00\x00\x00\x01\x9c\x53'  #  | .S......S......S
    msg += b'\x00\x00\x00\x00\x01\x9d\x53\x00\x00\x00\x00\x01\x9e\x53\x00\x00'  #  | ......S......S..
    msg += b'\x00\x00\x01\x9f\x53\x00\x00\x00\x00\x01\xa0\x53\x00\x00\x00\x00'  #  | ....S......S....
    msg += b'\x01\xf4\x49\x00\x00\x00\x00\x00\x00\x01\xf5\x53\x00\x00\x00\x00'  #  | ..I........S....
    msg += b'\x01\xf6\x53\x00\x00\x00\x00\x01\xf7\x53\x00\x00\x00\x00\x01\xf8'  #  | ..S......S......
    msg += b'\x53\x00\x00\x00\x00\x01\xf9\x53\x00\x00\x00\x00\x01\xfa\x53\x00'  #  | S......S......S.
    msg += b'\x00\x00\x00\x01\xfb\x53\x00\x00\x00\x00\x01\xfc\x53\x00\x00\x00'  #  | .....S......S...
    msg += b'\x00\x01\xfd\x53\x00\x00\x00\x00\x01\xfe\x53\x00\x00\x00\x00\x01'  #  | ...S......S.....
    msg += b'\xff\x53\x00\x00\x00\x00\x02\x00\x53\x00\x00\x00\x00\x02\x01\x53'  #  | .S......S......S
    msg += b'\x00\x00\x00\x00\x02\x02\x53\x00\x00\x00\x00\x02\x03\x53\x00\x00'  #  | ......S......S..
    msg += b'\x00\x00\x02\x04\x53\x00\x00\x00\x00\x02\x58\x49\x00\x00\x00\x00'  #  | ....S.....XI....
    msg += b'\x00\x00\x02\x59\x53\x00\x00\x00\x00\x02\x5a\x53\x00\x00\x00\x00'  #  | ...YS.....ZS....
    msg += b'\x02\x5b\x53\x00\x00\x00\x00\x02\x5c\x53\x00\x00\x00\x00\x02\x5d'  #  | .[S.....\S.....]
    msg += b'\x53\x00\x00\x00\x00\x02\x5e\x53\x00\x00\x00\x00\x02\x5f\x53\x00'  #  | S.....^S....._S.
    msg += b'\x00\x00\x00\x02\x60\x53\x00\x00\x00\x00\x02\x61\x53\x00\x00\x00'  #  | ....`S.....aS...
    msg += b'\x00\x02\x62\x53\x00\x00\x00\x00\x02\x63\x53\x00\x00\x00\x00\x02'  #  | ..bS.....cS.....
    msg += b'\x64\x53\x00\x00\x00\x00\x02\x65\x53\x00\x00\x00\x00\x02\x66\x53'  #  | dS.....eS.....fS
    msg += b'\x00\x00\x00\x00\x02\x67\x53\x00\x00\x00\x00\x02\x68\x53\x00\x00'  #  | .....gS.....hS..
    msg += b'\x00\x00\x02\xbc\x49\x00\x00\x00\x00\x00\x00\x02\xbd\x53\x00\x00'  #  | ....I........S..
    msg += b'\x00\x00\x02\xbe\x53\x00\x00\x00\x00\x02\xbf\x53\x00\x00\x00\x00'  #  | ....S......S....
    msg += b'\x02\xc0\x53\x00\x00\x00\x00\x02\xc1\x53\x00\x00\x00\x00\x02\xc2'  #  | ..S......S......
    msg += b'\x53\x00\x00\x00\x00\x02\xc3\x53\x00\x00\x00\x00\x02\xc4\x53\x00'  #  | S......S......S.
    msg += b'\x00\x00\x00\x02\xc5\x53\x00\x00\x00\x00\x02\xc6\x53\x00\x00\x00'  #  | .....S......S...
    msg += b'\x00\x02\xc7\x53\x00\x00\x00\x00\x02\xc8\x53\x00\x00\x00\x00\x02'  #  | ...S......S.....
    msg += b'\xc9\x53\x00\x00\x00\x00\x02\xca\x53\x00\x00\x00\x00\x02\xcb\x53'  #  | .S......S......S
    msg += b'\x00\x00\x00\x00\x02\xcc\x53\x00\x00\x00\x00\x03\x20\x53\x00\x00'  #  | ......S..... S..
    msg += b'\x00\x00\x03\x84\x53\x51\x09\x00\x00\x03\xe8\x46\x43\x65\x99\x9a'  #  | ....SQ.....FCe..
    msg += b'\x00\x00\x04\x4c\x46\x3e\xd7\x0a\x3d\x00\x00\x04\xb0\x46\x42\x48'  #  | ...LF>..=....FBH
    msg += b'\x28\xf6\x00\x00\x05\x14\x53\x00\x1f\x00\x00\x05\x78\x53\x00\x00'  #  | (.....S.....xS..
    msg += b'\x00\x00\x05\xdc\x53\x02\x58\x00\x00\x06\x40\x46\x42\xc1\x33\x33'  #  | ....S.X...@FB.33
    msg += b'\x00\x00\x06\xa4\x46\x3f\x33\x33\x33\x00\x00\x07\x08\x46\x00\x00'  #  | ....F?333....F..
    msg += b'\x00\x00\x00\x00\x07\x6c\x46\x00\x00\x00\x00\x00\x00\x07\xd0\x46'  #  | .....lF........F
    msg += b'\x42\x05\x99\x9a\x00\x00\x08\x34\x46\x40\x41\xeb\x85\x00\x00\x08'  #  | B......4F@A.....
    msg += b'\x98\x46\x42\xcb\x66\x66\x00\x00\x08\xfc\x46\x00\x00\x00\x00\x00'  #  | .FB.ff....F.....
    msg += b'\x00\x09\x60\x46\x00\x00\x00\x00\x00\x00\x09\xc4\x46\x00\x00\x00'  #  | ..`F........F...
    msg += b'\x00\x00\x00\x0a\x28\x46\x00\x00\x00\x00\x00\x00\x0a\x8c\x46\x00'  #  | ....(F........F.
    msg += b'\x00\x00\x00\x00\x00\x0a\xf0\x46\x00\x00\x00\x00\x00\x00\x0b\x54'  #  | .......F.......T
    msg += b'\x46\x3f\x19\x99\x9a\x00\x00\x0b\xb8\x46\x43\xf3\x95\xc3\x00\x00'  #  | F?.......FC.....
    msg += b'\x0c\x1c\x46\x00\x00\x00\x00\x00\x00\x0c\x80\x46\x43\x04\x4a\x3d'  #  | ..F........FC.J=
    msg += b'\x00\x00\x0c\xe4\x46\x3f\x23\xd7\x0a\x00\x00\x0d\x48\x46\x43\xbf'  #  | ....F?#.....HFC.
    msg += b'\x9e\xb8\x00\x00\x0d\xac\x46\x00\x00\x00\x00\x00\x00\x0e\x10\x46'  #  | ......F........F
    msg += b'\x00\x00\x00\x00\x00\x00\x0e\x74\x46\x00\x00\x00\x00\x00\x00\x0e'  #  | .......tF.......
    msg += b'\xd8\x46\x00\x00\x00\x00\x00\x00\x0f\x3c\x53\x00\x00\x00\x00\x0f'  #  | .F.......<S.....
    msg += b'\xa0\x53\x00\x00\x00\x00\x10\x04\x53\x55\xaa\x00\x00\x10\x68\x53'  #  | .S......SU....hS
    msg += b'\x00\x00\x00\x00\x10\xcc\x53\x00\x00\x00\x00\x11\x30\x53\x00\x00'  #  | ......S.....0S..
    msg += b'\x00\x00\x11\x94\x53\x00\x00\x00\x00\x11\xf8\x53\xff\xff\x00\x00'  #  | ....S......S....
    msg += b'\x12\x5c\x53\x03\x20\x00\x00\x12\xc0\x53\x00\x02\x00\x00\x13\x24'  #  | .\S. ....S.....$
    msg += b'\x53\x04\x00\x00\x00\x13\x88\x53\x04\x00\x00\x00\x13\xec\x53\x04'  #  | S......S......S.
    msg += b'\x00\x00\x00\x14\x50\x53\x04\x00\x00\x00\x14\xb4\x53\x00\x01\x00'  #  | ....PS......S...
    msg += b'\x00\x15\x18\x53\x08\x1e\x00\x00\x15\x7c\x53\x00\x00\x00\x00\x27'  #  | ...S.....|S....'
    msg += b'\x10\x53\x00\x02\x00\x00\x27\x74\x53\x00\x3c\x00\x00\x27\xd8\x53'  #  | .S....'tS.<..'.S
    msg += b'\x00\x68\x00\x00\x28\x3c\x53\x05\x00\x00\x00\x28\xa0\x46\x43\x79'  #  | .h..(<S....(.FCy
    msg += b'\x00\x00\x00\x00\x29\x04\x46\x43\x48\x00\x00\x00\x00\x29\x68\x46'  #  | ....).FCH....)hF
    msg += b'\x42\x48\x33\x33\x00\x00\x29\xcc\x46\x42\x3e\x3d\x71\x00\x00\x2a'  #  | BH33..).FB>=q..*
    msg += b'\x30\x53\x00\x01\x00\x00\x2a\x94\x46\x43\x37\x00\x00\x00\x00\x2a'  #  | 0S....*.FC7....*
    msg += b'\xf8\x46\x42\xce\x00\x00\x00\x00\x2b\x5c\x53\x00\x96\x00\x00\x2b'  #  | .FB.....+\S....+
    msg += b'\xc0\x53\x00\x10\x00\x00\x2c\x24\x46\x43\x90\x00\x00\x00\x00\x2c'  #  | .S....,$FC.....,
    msg += b'\x88\x46\x43\x95\x00\x00\x00\x00\x2c\xec\x53\x00\x06\x00\x00\x2d'  #  | .FC.....,.S....-
    msg += b'\x50\x53\x00\x06\x00\x00\x2d\xb4\x46\x43\x7d\x00\x00\x00\x00\x2e'  #  | PS....-.FC}.....
    msg += b'\x18\x46\x42\x3d\xeb\x85\x00\x00\x2e\x7c\x46\x42\x3d\xeb\x85\x00'  #  | .FB=.....|FB=...
    msg += b'\x00\x2e\xe0\x53\x00\x03\x00\x00\x2f\x44\x53\x00\x03\x00\x00\x2f'  #  | ...S..../DS..../
    msg += b'\xa8\x46\x42\x4d\xeb\x85\x00\x00\x30\x0c\x46\x42\x4d\xeb\x85\x00'  #  | .FBM....0.FBM...
    msg += b'\x00\x30\x70\x53\x00\x03\x00\x00\x30\xd4\x53\x00\x03\x00\x00\x31'  #  | .0pS....0.S....1
    msg += b'\x38\x46\x42\x08\x00\x00\x00\x00\x31\x9c\x53\x00\x05\x00\x00\x32'  #  | 8FB.....1.S....2
    msg += b'\x00\x53\x01\x61\x00\x00\x32\x64\x53\x00\x01\x00\x00\x32\xc8\x53'  #  | .S.a..2dS....2.S
    msg += b'\x13\x9c\x00\x00\x33\x2c\x53\x0f\xa0\x00\x00\x33\x90\x53\x00\x4f'  #  | ....3,S....3.S.O
    msg += b'\x00\x00\x33\xf4\x53\x00\x66\x00\x00\x34\x58\x53\x03\xe8\x00\x00'  #  | ..3.S.f..4XS....
    msg += b'\x34\xbc\x53\x04\x00\x00\x00\x35\x20\x53\x09\xc4\x00\x00\x35\x84'  #  | 4.S....5 S....5.
    msg += b'\x53\x07\xc6\x00\x00\x35\xe8\x53\x13\x8c\x00\x00\x36\x4c\x53\x12'  #  | S....5.S....6LS.
    msg += b'\x94\x00\x01\x38\x80\x53\x00\x02\x00\x01\x38\x81\x53\x00\x01\x00'  #  | ...8.S....8.S...
    msg += b'\x01\x38\x82\x53\x00\x01\x00\x01\x38\x83\x53\x00\x00\x00\x00\x00'  #  | .8.S....8.S.....
    msg += b'\x8b\x10\x52\x31\x37\x45\x37\x33\x30\x37\x30\x32\x31\x44\x30\x30'  #  | ..R17E7307021D00
    msg += b'\x36\x41\x91\x04\x01\x90\x00\x01\x10\x54\x31\x37\x45\x37\x33\x30'  #  | 6A.......T17E730
    msg += b'\x37\x30\x32\x31\x44\x30\x30\x36\x41\x01\x00\x00\x01\x91\xa3\xfe'  #  | 7021D006A.......
    msg += b'\xb3\x80\x00\x00\x00\x06\x00\x00\x00\x0a\x54\x08\x4d\x69\x63\x72'  #  | ..........T.Micr
    msg += b'\x6f\x69\x6e\x76\x00\x00\x00\x14\x54\x04\x54\x53\x55\x4e\x00\x00'  #  | oinv....T.TSUN..
    msg += b'\x00\x1e\x54\x07\x56\x35\x2e\x31\x2e\x30\x39\x00\x00\x00\x28\x54'  #  | ..T.V5.1.09...(T
    msg += b'\x10\x54\x31\x37\x45\x37\x33\x30\x37\x30\x32\x31\x44\x30\x30\x36'  #  | .T17E7307021D006
    msg += b'\x41\x00\x00\x00\x32\x54\x0a\x54\x53\x4f\x4c\x2d\x4d\x53\x36\x30'  #  | A...2T.TSOL-MS60
    msg += b'\x30\x00\x00\x00\x3c\x54\x05\x41\x2c\x42\x2c\x43'                  #  | 0...<T.A,B,C'
    return msg

@pytest.fixture
def msg_controller_ms3000_ind(): # Data indication from the controller
    msg  =  b'\x00\x00\x04\xdf\x10R170000000000001\x91\x71\x0e\x10\x00\x00\x10R170000000000001'
    msg +=  b'\x01\x00\x00\x01'
    msg +=  b'\x95\x18\x5e\x19\x98\x00\x00\x00\x39\x00\x09\x2b\xa8\x54\x10\x52'  # | ..^.....9..+.T.R
    msg +=  b'\x53\x57\x5f\x34\x30\x30\x5f\x56\x32\x2e\x30\x31\x2e\x31\x33\x00'  # | SW_400_V2.01.13.
    msg +=  b'\x09\x27\xc0\x54\x06\x52\x61\x79\x6d\x6f\x6e\x00\x09\x2f\x90\x54'  # | .'.T.Raymon../.T
    msg +=  b'\x0b\x52\x53\x57\x2d\x31\x2d\x31\x30\x30\x30\x31\x00\x09\x5a\x88'  # | .RSW-1-10001..Z.
    msg +=  b'\x54\x0f\x74\x2e\x72\x61\x79\x6d\x6f\x6e\x69\x6f\x74\x2e\x63\x6f'  # | T.t.raymoniot.co
    msg +=  b'\x6d\x00\x09\x5a\xec\x54\x1c\x6c\x6f\x67\x67\x65\x72\x2e\x74\x61'  # | m..Z.T.logger.ta
    msg +=  b'\x6c\x65\x6e\x74\x2d\x6d\x6f\x6e\x69\x74\x6f\x72\x69\x6e\x67\x2e'  # | lent-monitoring.
    msg +=  b'\x63\x6f\x6d\x00\x0d\x2f\x00\x54\x10\xff\xff\xff\xff\xff\xff\xff'  # | com../.T........
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x32\xe8\x54\x10\xff'  # | ...........2.T..
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'  # | ................
    msg +=  b'\x0d\x36\xd0\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | .6.T............
    msg +=  b'\xff\xff\xff\xff\xff\x00\x0d\x3a\xb8\x54\x10\xff\xff\xff\xff\xff'  # | .......:.T......
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x3e\xa0\x54'  # | .............>.T
    msg +=  b'\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\x00\x0d\x42\x88\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ...B.T..........
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x46\x70\x54\x10\xff\xff\xff'  # | .........FpT....
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x4a'  # | ...............J
    msg +=  b'\x58\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | XT..............
    msg +=  b'\xff\xff\xff\x00\x0d\x4e\x40\x54\x10\xff\xff\xff\xff\xff\xff\xff'  # | .....N@T........
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x52\x28\x54\x10\xff'  # | ...........R(T..
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'  # | ................
    msg +=  b'\x0d\x56\x10\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | .V.T............
    msg +=  b'\xff\xff\xff\xff\xff\x00\x0d\x59\xf8\x54\x10\xff\xff\xff\xff\xff'  # | .......Y.T......
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x5d\xe0\x54'  # | .............].T
    msg +=  b'\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\x00\x0d\x61\xc8\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ...a.T..........
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x65\xb0\x54\x10\xff\xff\xff'  # | .........e.T....
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x69'  # | ...............i
    msg +=  b'\x98\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | .T..............
    msg +=  b'\xff\xff\xff\x00\x0d\x6d\x80\x54\x10\xff\xff\xff\xff\xff\xff\xff'  # | .....m.T........
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x71\x68\x54\x10\xff'  # | ...........qhT..
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'  # | ................
    msg +=  b'\x0d\x75\x50\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | .uPT............
    msg +=  b'\xff\xff\xff\xff\xff\x00\x0d\x79\x38\x54\x10\xff\xff\xff\xff\xff'  # | .......y8T......
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x7d\x20\x54'  # | .............} T
    msg +=  b'\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\x00\x0d\x81\x08\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | .....T..........
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x84\xf0\x54\x10\xff\xff\xff'  # | ...........T....
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x88'  # | ................
    msg +=  b'\xd8\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | .T..............
    msg +=  b'\xff\xff\xff\x00\x0d\x8c\xc0\x54\x10\xff\xff\xff\xff\xff\xff\xff'  # | .......T........
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x90\xa8\x54\x10\xff'  # | .............T..
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'  # | ................
    msg +=  b'\x0d\x94\x90\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ...T............
    msg +=  b'\xff\xff\xff\xff\xff\x00\x0d\x98\x78\x54\x10\xff\xff\xff\xff\xff'  # | ........xT......
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x9c\x60\x54'  # | ..............`T
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'  # | ................
    msg +=  b'\x00\x0d\x00\x20\x49\x00\x00\x00\x01\x00\x0c\x35\x00\x49\x00\x00'  # | ... I......5.I..
    msg +=  b'\x00\x62\x00\x0c\x96\xa8\x49\x00\x00\x01\x4f\x00\x0c\x7f\x38\x49'  # | .b....I...O...8I
    msg +=  b'\x00\x00\x00\x01\x00\x0c\xfc\x38\x49\x00\x00\x00\x01\x00\x0c\xf8'  # | .......8I.......
    msg +=  b'\x50\x49\x00\x00\x01\x2c\x00\x0c\x63\xe0\x49\x00\x00\x00\x00\x00'  # | PI...,..c.I.....
    msg +=  b'\x0c\x67\xc8\x49\x00\x00\x00\x00\x00\x0c\x50\x58\x49\x00\x00\x00'  # | .g.I......PXI...
    msg +=  b'\x01\x00\x09\x5e\x70\x49\x00\x00\x13\x8d\x00\x09\x5e\xd4\x49\x00'  # | ...^pI......^.I.
    msg +=  b'\x00\x13\x8d\x00\x09\x5b\x50\x49\x00\x00\x00\x02\x00\x0d\x04\x08'  # | .....[PI........
    msg +=  b'\x49\x00\x00\x00\x00\x00\x07\xa1\x84\x49\x00\x00\x00\x01\x00\x0c'  # | I........I......
    msg +=  b'\x50\x59\x49\x00\x00\x00\x2d\x00\x0d\x1f\x60\x49\x00\x00\x00\x00'  # | PYI...-...`I....
    msg +=  b'\x00\x0d\x23\x48\x49\xff\xff\xff\xff\x00\x0d\x27\x30\x49\xff\xff'  # | ..#HI......'0I..
    msg +=  b'\xff\xff\x00\x0d\x2b\x18\x4c\x00\x00\x00\x00\xff\xff\xff\xff\x00'  # | ....+.L.........
    msg +=  b'\x0c\xa2\x60\x49\x00\x00\x00\x00\x00\x0d\xa0\x48\x49\x00\x00\x00'  # | ..`I.......HI...
    msg +=  b'\x00\x00\x0d\xa4\x30\x49\x00\x00\x00\xff\x00\x0d\xa8\x18\x49\x00'  # | ....0I........I.
    msg +=  b'\x00\x00\xff'
    return msg

@pytest.fixture
def msg_inverter_ms3000_ind(): # Data indication from the controller
    msg  =  b'\x00\x00\x08\xff\x10R170000000000001\x91\x04\x01\x90\x00\x00\x10R170000000000001'
    msg +=  b'\x01\x00\x00\x01'
    msg +=  b'\x95\x18\x5e\x1d\x80\x00\x00\x01\x2c\x00\x00\x00\x64\x53\x00\x00'  #  | ..^.....,...dS..
    msg +=  b'\x00\x00\x00\xc8\x53\x44\x00\x00\x00\x01\x2c\x53\x00\x00\x00\x00'  #  | ....SD....,S....
    msg +=  b'\x01\x90\x49\x00\x00\x00\x00\x00\x00\x01\x91\x53\x00\x00\x00\x00'  #  | ..I........S....
    msg +=  b'\x01\x92\x53\x00\x00\x00\x00\x01\x93\x53\x00\x00\x00\x00\x01\x94'  #  | ..S......S......
    msg +=  b'\x53\x00\x00\x00\x00\x01\x95\x53\x00\x00\x00\x00\x01\x96\x53\x00'  #  | S......S......S.
    msg +=  b'\x00\x00\x00\x01\x97\x53\x00\x00\x00\x00\x01\x98\x53\x00\x00\x00'  #  | .....S......S...
    msg +=  b'\x00\x01\x99\x53\x00\x00\x00\x00\x01\x9a\x53\x00\x00\x00\x00\x01'  #  | ...S......S.....
    msg +=  b'\x9b\x53\x00\x00\x00\x00\x01\x9c\x53\x00\x00\x00\x00\x01\x9d\x53'  #  | .S......S......S
    msg +=  b'\x00\x00\x00\x00\x01\x9e\x53\x00\x00\x00\x00\x01\x9f\x53\x00\x00'  #  | ......S......S..
    msg +=  b'\x00\x00\x01\xa0\x53\x00\x00\x00\x00\x01\xf4\x49\x00\x00\x00\x00'  #  | ....S......I....
    msg +=  b'\x00\x00\x01\xf5\x53\x00\x00\x00\x00\x01\xf6\x53\x00\x00\x00\x00'  #  | ....S......S....
    msg +=  b'\x01\xf7\x53\x00\x00\x00\x00\x01\xf8\x53\x00\x00\x00\x00\x01\xf9'  #  | ..S......S......
    msg +=  b'\x53\x00\x00\x00\x00\x01\xfa\x53\x00\x00\x00\x00\x01\xfb\x53\x00'  #  | S......S......S.
    msg +=  b'\x00\x00\x00\x01\xfc\x53\x00\x00\x00\x00\x01\xfd\x53\x00\x00\x00'  #  | .....S......S...
    msg +=  b'\x00\x01\xfe\x53\x00\x00\x00\x00\x01\xff\x53\x00\x00\x00\x00\x02'  #  | ...S......S.....
    msg +=  b'\x00\x53\x00\x00\x00\x00\x02\x01\x53\x00\x00\x00\x00\x02\x02\x53'  #  | .S......S......S
    msg +=  b'\x00\x00\x00\x00\x02\x03\x53\x00\x00\x00\x00\x02\x04\x53\x00\x00'  #  | ......S......S..
    msg +=  b'\x00\x00\x02\x58\x49\x00\x00\x00\x00\x00\x00\x02\x59\x53\x00\x00'  #  | ...XI.......YS..
    msg +=  b'\x00\x00\x02\x5a\x53\x00\x00\x00\x00\x02\x5b\x53\x00\x00\x00\x00'  #  | ...ZS.....[S....
    msg +=  b'\x02\x5c\x53\x00\x00\x00\x00\x02\x5d\x53\x00\x00\x00\x00\x02\x5e'  #  | .\S.....]S.....^
    msg +=  b'\x53\x00\x00\x00\x00\x02\x5f\x53\x00\x00\x00\x00\x02\x60\x53\x00'  #  | S....._S.....`S.
    msg +=  b'\x00\x00\x00\x02\x61\x53\x00\x00\x00\x00\x02\x62\x53\x00\x00\x00'  #  | ....aS.....bS...
    msg +=  b'\x00\x02\x63\x53\x00\x00\x00\x00\x02\x64\x53\x00\x00\x00\x00\x02'  #  | ..cS.....dS.....
    msg +=  b'\x65\x53\x00\x00\x00\x00\x02\x66\x53\x00\x00\x00\x00\x02\x67\x53'  #  | eS.....fS.....gS
    msg +=  b'\x00\x00\x00\x00\x02\x68\x53\x00\x00\x00\x00\x02\xbc\x49\x00\x00'  #  | .....hS......I..
    msg +=  b'\x00\x00\x00\x00\x02\xbd\x53\x00\x00\x00\x00\x02\xbe\x53\x00\x00'  #  | ......S......S..
    msg +=  b'\x00\x00\x02\xbf\x53\x00\x00\x00\x00\x02\xc0\x53\x00\x00\x00\x00'  #  | ....S......S....
    msg +=  b'\x02\xc1\x53\x00\x00\x00\x00\x02\xc2\x53\x00\x00\x00\x00\x02\xc3'  #  | ..S......S......
    msg +=  b'\x53\x00\x00\x00\x00\x02\xc4\x53\x00\x00\x00\x00\x02\xc5\x53\x00'  #  | S......S......S.
    msg +=  b'\x00\x00\x00\x02\xc6\x53\x00\x00\x00\x00\x02\xc7\x53\x00\x00\x00'  #  | .....S......S...
    msg +=  b'\x00\x02\xc8\x53\x00\x00\x00\x00\x02\xc9\x53\x00\x00\x00\x00\x02'  #  | ...S......S.....
    msg +=  b'\xca\x53\x00\x00\x00\x00\x02\xcb\x53\x00\x00\x00\x00\x02\xcc\x53'  #  | .S......S......S
    msg +=  b'\x00\x00\x00\x00\x03\x20\x53\x00\x01\x00\x00\x03\x84\x53\x11\x68'  #  | ..... S......S.h
    msg +=  b'\x00\x00\x03\xe8\x46\x44\x23\xd1\xec\x00\x00\x04\x4c\x46\x43\xa3'  #  | ....FD#.....LFC.
    msg +=  b'\xb3\x33\x00\x00\x04\xb0\x46\x00\x00\x00\x00\x00\x00\x05\x14\x46'  #  | .3....F........F
    msg +=  b'\x43\x6e\x80\x00\x00\x00\x05\x78\x46\x3d\x4c\xcc\xcd\x00\x00\x05'  #  | Cn.....xF=L.....
    msg +=  b'\xdc\x46\x00\x00\x00\x00\x00\x00\x06\x40\x46\x42\x48\x00\x00\x00'  #  | .F.......@FBH...
    msg +=  b'\x00\x06\xa4\x53\x00\x03\x00\x00\x07\x08\x53\x00\x0c\x00\x00\x07'  #  | ...S......S.....
    msg +=  b'\x6c\x53\x00\x50\x00\x00\x07\xd0\x46\x43\xa3\xb3\x33\x00\x00\x08'  #  | lS.P....FC..3...
    msg +=  b'\x34\x53\x0b\xb8\x00\x00\x08\x98\x46\x00\x00\x00\x00\x00\x00\x08'  #  | 4S......F.......
    msg +=  b'\xfc\x46\x00\x00\x00\x00\x00\x00\x09\x60\x46\x41\xee\xe1\x48\x00'  #  | .F.......`FA..H.
    msg +=  b'\x00\x09\xc4\x53\x00\x00\x00\x00\x0a\x28\x46\x41\xf2\x00\x00\x00'  #  | ...S.....(FA....
    msg +=  b'\x00\x0a\x8c\x46\x3f\xac\x28\xf6\x00\x00\x0a\xf0\x53\x00\x0c\x00'  #  | ...F?.(.....S...
    msg +=  b'\x00\x0b\x54\x53\x00\x00\x00\x00\x0b\xb8\x53\x00\x00\x00\x00\x0c'  #  | ..TS......S.....
    msg +=  b'\x1c\x53\x00\x00\x00\x00\x0c\x80\x53\x00\x00\x00\x00\x0c\xe4\x53'  #  | .S......S......S
    msg +=  b'\x00\x00\x00\x00\x0d\x48\x53\x00\x00\x00\x00\x0d\xac\x53\x00\x00'  #  | .....HS......S..
    msg +=  b'\x00\x00\x0e\x10\x53\x00\x00\x00\x00\x0e\x74\x53\x00\x00\x00\x00'  #  | ....S.....tS....
    msg +=  b'\x0e\xd8\x53\x00\x00\x00\x00\x0f\x3c\x53\x00\x00\x00\x00\x0f\xa0'  #  | ..S.....<S......
    msg +=  b'\x53\x00\x00\x00\x00\x10\x04\x53\x00\x00\x00\x00\x10\x68\x53\x00'  #  | S......S.....hS.
    msg +=  b'\x00\x00\x00\x10\xcc\x53\x00\x00\x00\x00\x11\x30\x53\x00\x00\x00'  #  | .....S.....0S...
    msg +=  b'\x00\x11\x94\x53\x00\x00\x00\x00\x11\xf8\x53\x00\x00\x00\x00\x12'  #  | ...S......S.....
    msg +=  b'\x5c\x53\x00\x00\x00\x00\x12\xc0\x53\x00\x00\x00\x00\x13\x24\x46'  #  | \S......S.....$F
    msg +=  b'\x42\x9d\x33\x33\x00\x00\x13\x88\x46\x00\x00\x00\x00\x00\x00\x13'  #  | B.33....F.......
    msg +=  b'\xec\x46\x00\x00\x00\x00\x00\x00\x14\x50\x46\x42\xdc\x00\x00\x00'  #  | .F.......PFB....
    msg +=  b'\x00\x14\xb4\x53\x00\x00\x00\x00\x15\x18\x53\x00\x00\x00\x00\x15'  #  | ...S......S.....
    msg +=  b'\x7c\x53\x00\x00\x00\x00\x15\x7d\x53\x00\x00\x00\x00\x15\x7e\x53'  #  | |S.....}S.....~S
    msg +=  b'\x00\x00\x00\x00\x15\x7f\x53\x00\x00\x00\x00\x15\x80\x53\x00\x00'  #  | ......S......S..
    msg +=  b'\x00\x00\x15\x81\x53\x00\x00\x00\x00\x15\x82\x53\x00\x00\x00\x00'  #  | ....S......S....
    msg +=  b'\x15\x83\x53\x00\x00\x00\x00\x15\x84\x53\x00\x00\x00\x00\x15\x85'  #  | ..S......S......
    msg +=  b'\x53\x00\x00\x00\x00\x15\x86\x53\x00\x00\x00\x00\x15\x87\x53\x00'  #  | S......S......S.
    msg +=  b'\x00\x00\x00\x15\x88\x53\x00\x00\x00\x00\x15\x89\x53\x00\x00\x00'  #  | .....S......S...
    msg +=  b'\x00\x15\x8a\x53\x00\x00\x00\x00\x15\x8b\x53\x00\x00\x00\x00\x15'  #  | ...S......S.....
    msg +=  b'\x8c\x53\x00\x00\x00\x00\x15\xe0\x46\x42\x68\x66\x66\x00\x00\x16'  #  | .S......FBhff...
    msg +=  b'\x44\x46\x00\x00\x00\x00\x00\x00\x16\xa8\x46\x00\x00\x00\x00\x00'  #  | DF........F.....
    msg +=  b'\x00\x17\x0c\x46\x42\xdc\x00\x00\x00\x00\x17\x70\x53\x00\x00\x00'  #  | ...FB......pS...
    msg +=  b'\x00\x17\xd4\x53\x00\x00\x00\x00\x18\x38\x53\x00\x00\x00\x00\x18'  #  | ...S.....8S.....
    msg +=  b'\x39\x53\x00\x00\x00\x00\x18\x3a\x53\x00\x00\x00\x00\x18\x3b\x53'  #  | 9S.....:S.....;S
    msg +=  b'\x00\x00\x00\x00\x18\x3c\x53\x00\x00\x00\x00\x18\x3d\x53\x00\x00'  #  | .....<S.....=S..
    msg +=  b'\x00\x00\x18\x3e\x53\x00\x00\x00\x00\x18\x3f\x53\x00\x00\x00\x00'  #  | ...>S.....?S....
    msg +=  b'\x18\x40\x53\x00\x00\x00\x00\x18\x41\x53\x00\x00\x00\x00\x18\x42'  #  | .@S.....AS.....B
    msg +=  b'\x53\x00\x00\x00\x00\x18\x43\x53\x00\x00\x00\x00\x18\x44\x53\x00'  #  | S.....CS.....DS.
    msg +=  b'\x00\x00\x00\x18\x45\x53\x00\x00\x00\x00\x18\x46\x53\x00\x00\x00'  #  | ....ES.....FS...
    msg +=  b'\x00\x18\x47\x53\x00\x00\x00\x00\x18\x48\x53\x00\x00\x00\x00\x18'  #  | ..GS.....HS.....
    msg +=  b'\x9c\x46\x42\x6b\x33\x33\x00\x00\x19\x00\x46\x00\x00\x00\x00\x00'  #  | .FBk33....F.....
    msg +=  b'\x00\x19\x64\x46\x00\x00\x00\x00\x00\x00\x19\xc8\x46\x42\xdc\x00'  #  | ..dF........FB..
    msg +=  b'\x00\x00\x00\x1a\x2c\x53\x00\x00\x00\x00\x1a\x90\x53\x00\x00\x00'  #  | ....,S......S...
    msg +=  b'\x00\x1a\xf4\x53\x00\x00\x00\x00\x1a\xf5\x53\x00\x00\x00\x00\x1a'  #  | ...S......S.....
    msg +=  b'\xf6\x53\x00\x00\x00\x00\x1a\xf7\x53\x00\x00\x00\x00\x1a\xf8\x53'  #  | .S......S......S
    msg +=  b'\x00\x00\x00\x00\x1a\xf9\x53\x00\x00\x00\x00\x1a\xfa\x53\x00\x00'  #  | ......S......S..
    msg +=  b'\x00\x00\x1a\xfb\x53\x00\x00\x00\x00\x1a\xfc\x53\x00\x00\x00\x00'  #  | ....S......S....
    msg +=  b'\x1a\xfd\x53\x00\x00\x00\x00\x1a\xfe\x53\x00\x00\x00\x00\x1a\xff'  #  | ..S......S......
    msg +=  b'\x53\x00\x00\x00\x00\x1b\x00\x53\x00\x00\x00\x00\x1b\x01\x53\x00'  #  | S......S......S.
    msg +=  b'\x00\x00\x00\x1b\x02\x53\x00\x00\x00\x00\x1b\x03\x53\x00\x00\x00'  #  | .....S......S...
    msg +=  b'\x00\x1b\x04\x53\x00\x00\x00\x00\x1b\x58\x53\x00\x00\x00\x00\x1b'  #  | ...S.....XS.....
    msg +=  b'\xbc\x53\x11\x3d\x00\x00\x1c\x20\x46\x3c\x23\xd7\x0a\x00\x00\x1c'  #  | .S.=... F<#.....
    msg +=  b'\x84\x46\x00\x00\x00\x00\x00\x00\x1c\xe8\x46\x42\x04\x00\x00\x00'  #  | .F........FB....
    msg +=  b'\x00\x1d\x4c\x46\x00\x00\x00\x00\x00\x00\x1d\xb0\x46\x00\x00\x00'  #  | ..LF........F...
    msg +=  b'\x00\x00\x00\x1e\x14\x53\x00\x02\x00\x00\x1e\x78\x46\x41\x8b\x33'  #  | .....S.....xFA.3
    msg +=  b'\x33\x00\x00\x1e\xdc\x46\x3c\xa3\xd7\x0a\x00\x00\x1f\x40\x46\x3e'  #  | 3....F<......@F>
    msg +=  b'\x99\x99\x9a\x00\x00\x1f\xa4\x46\x40\x99\x99\x9a\x00\x00\x20\x08'  #  | .......F@..... .
    msg +=  b'\x53\x00\x00\x00\x00\x20\x6c\x53\x00\x00\x00\x00\x20\xd0\x53\x05'  #  | S.... lS.... .S.
    msg +=  b'\x00\x00\x00\x20\xd1\x53\x00\x00\x00\x00\x20\xd2\x53\x00\x00\x00'  #  | ... .S.... .S...
    msg +=  b'\x00\x20\xd3\x53\x00\x00\x00\x00\x20\xd4\x53\x00\x00\x00\x00\x20'  #  | . .S.... .S.... 
    msg +=  b'\xd5\x53\x00\x00\x00\x00\x20\xd6\x53\x00\x00\x00\x00\x20\xd7\x53'  #  | .S.... .S.... .S
    msg +=  b'\x00\x00\x00\x00\x20\xd8\x53\x00\x00\x00\x00\x20\xd9\x53\x00\x01'  #  | .... .S.... .S..
    msg +=  b'\x00\x00\x20\xda\x53\x00\x00\x00\x00\x20\xdb\x53\x00\x01\x00\x00'  #  | .. .S.... .S....
    msg +=  b'\x20\xdc\x53\x00\x00\x00\x00\x20\xdd\x53\x00\x00\x00\x00\x20\xde'  #  |  .S.... .S.... .
    msg +=  b'\x53\x00\x00\x00\x00\x20\xdf\x53\x00\x00\x00\x00\x20\xe0\x53\x00'  #  | S.... .S.... .S.
    msg +=  b'\x00\x00\x00\x21\x34\x46\x00\x00\x00\x00\x00\x00\x21\x98\x46\x00'  #  | ...!4F......!.F.
    msg +=  b'\x00\x00\x00\x00\x00\x21\xfc\x46\x00\x00\x00\x00\x00\x00\x22\x60'  #  | .....!.F......"`
    msg +=  b'\x46\x00\x00\x00\x00\x00\x00\x22\xc4\x53\x00\x00\x00\x00\x23\x28'  #  | F......".S....#(
    msg +=  b'\x53\x00\x00\x00\x00\x23\x8c\x53\x00\x00\x00\x00\x23\x8d\x53\x00'  #  | S....#.S....#.S.
    msg +=  b'\x00\x00\x00\x23\x8e\x53\x00\x00\x00\x00\x23\x8f\x53\x00\x00\x00'  #  | ...#.S....#.S...
    msg +=  b'\x00\x23\x90\x53\x00\x00\x00\x00\x23\x91\x53\x00\x00\x00\x00\x23'  #  | .#.S....#.S....#
    msg +=  b'\x92\x53\x00\x00\x00\x00\x23\x93\x53\x00\x00\x00\x00\x23\x94\x53'  #  | .S....#.S....#.S
    msg +=  b'\x00\x00\x00\x00\x23\x95\x53\x00\x00\x00\x00\x23\x96\x53\x00\x00'  #  | ....#.S....#.S..
    msg +=  b'\x00\x00\x23\x97\x53\x00\x00\x00\x00\x23\x98\x53\x00\x00\x00\x00'  #  | ..#.S....#.S....
    msg +=  b'\x23\x99\x53\x00\x00\x00\x00\x23\x9a\x53\x00\x00\x00\x00\x23\x9b'  #  | #.S....#.S....#.
    msg +=  b'\x53\x00\x00\x00\x00\x23\x9c\x53\x00\x00\x00\x00\x23\xf0\x46\x00'  #  | S....#.S....#.F.
    msg +=  b'\x00\x00\x00\x00\x00\x24\x54\x46\x00\x00\x00\x00\x00\x00\x24\xb8'  #  | .....$TF......$.
    msg +=  b'\x46\x00\x00\x00\x00\x00\x00\x25\x1c\x46\x00\x00\x00\x00\x00\x00'  #  | F......%.F......
    msg +=  b'\x25\x80\x53\x00\x00\x00\x00\x25\xe4\x53\x00\x00\x00\x00\x26\x48'  #  | %.S....%.S....&H
    msg +=  b'\x53\x00\x00\x00\x00\x26\x49\x53\x00\x00\x00\x00\x26\x4a\x53\x00'  #  | S....&IS....&JS.
    msg +=  b'\x00\x00\x00\x26\x4b\x53\x00\x00\x00\x00\x26\x4c\x53\x00\x00\x00'  #  | ...&KS....&LS...
    msg +=  b'\x00\x26\x4d\x53\x00\x00\x00\x00\x26\x4e\x53\x00\x00\x00\x00\x26'  #  | .&MS....&NS....&
    msg +=  b'\x4f\x53\x00\x00\x00\x00\x26\x50\x53\x00\x00\x00\x00\x26\x51\x53'  #  | OS....&PS....&QS
    msg +=  b'\x00\x00\x00\x00\x26\x52\x53\x00\x00\x00\x00\x26\x53\x53\x00\x00'  #  | ....&RS....&SS..
    msg +=  b'\x00\x00\x26\x54\x53\x00\x00\x00\x00\x26\x55\x53\x00\x00\x00\x00'  #  | ..&TS....&US....
    msg +=  b'\x26\x56\x53\x00\x00\x00\x00\x26\x57\x53\x00\x00\x00\x00\x26\x58'  #  | &VS....&WS....&X
    msg +=  b'\x53\x00\x00\x00\x00\x26\xac\x53\x00\x00\x00\x00\x27\x10\x53\x11'  #  | S....&.S....'.S.
    msg +=  b'\x3d\x00\x00\x27\x74\x46\x00\x00\x00\x00\x00\x00\x27\xd8\x46\x00'  #  | =..'tF......'.F.
    msg +=  b'\x00\x00\x00\x00\x00\x28\x3c\x46\x42\x03\xf5\xc3\x00\x00\x28\xa0'  #  | .....(<FB.....(.
    msg +=  b'\x46\x00\x00\x00\x00\x00\x00\x29\x04\x46\x00\x00\x00\x00\x00\x00'  #  | F......).F......
    msg +=  b'\x29\x68\x53\x00\x02\x00\x00\x29\xcc\x53\x00\x03\x00\x00\x2a\x30'  #  | )hS....).S....*0
    msg +=  b'\x46\x42\x20\x00\x00\x00\x00\x2a\x94\x46\x42\x20\x00\x00\x00\x00'  #  | FB ....*.FB ....
    msg +=  b'\x2a\xf8\x46\x44\x20\x00\x00\x00\x00\x2b\x5c\x46\x43\x7b\x00\x00'  #  | *.FD ....+\FC{..
    msg +=  b'\x00\x00\x2b\xc0\x46\x43\x50\x00\x00\x00\x00\x2c\x24\x46\x42\x48'  #  | ..+.FCP....,$FBH
    msg +=  b'\x5c\x29\x00\x00\x2c\x88\x46\x42\x47\xa3\xd7\x00\x00\x2c\xec\x53'  #  | \)..,.FBG....,.S
    msg +=  b'\x00\x00\x00\x00\x2d\x50\x46\x43\x42\x00\x00\x00\x00\x2d\xb4\x46'  #  | ....-PFCB....-.F
    msg +=  b'\x42\xbc\x00\x00\x00\x00\x2e\x18\x46\x3f\xe6\x66\x66\x00\x00\x2e'  #  | B.......F?.ff...
    msg +=  b'\x7c\x46\x3f\xe6\x66\x66\x00\x00\x2e\xe0\x46\x43\x7e\x00\x00\x00'  #  | |F?.ff....FC~...
    msg +=  b'\x00\x2f\x44\x46\x43\x83\xf3\x33\x00\x00\x2f\xa8\x46\x3f\xe6\x66'  #  | ./DFC..3../.F?.f
    msg +=  b'\x66\x00\x00\x30\x0c\x46\x3f\xe6\x66\x66\x00\x00\x30\x70\x46\x43'  #  | f..0.F?.ff..0pFC
    msg +=  b'\x7e\x00\x00\x00\x00\x30\xd4\x46\x42\x3f\xeb\x85\x00\x00\x31\x38'  #  | ~....0.FB?....18
    msg +=  b'\x46\x42\x3d\xeb\x85\x00\x00\x31\x9c\x46\x3e\x4c\xcc\xcd\x00\x00'  #  | FB=....1.F>L....
    msg +=  b'\x32\x00\x46\x3e\x4c\xcc\xcd\x00\x00\x32\x64\x46\x42\x4c\x14\x7b'  #  | 2.F>L....2dFBL.{
    msg +=  b'\x00\x00\x32\xc8\x46\x42\x4d\xeb\x85\x00\x00\x33\x2c\x46\x3e\x4c'  #  | ..2.FBM....3,F>L
    msg +=  b'\xcc\xcd\x00\x00\x33\x90\x46\x3e\x4c\xcc\xcd\x00\x00\x33\xf4\x53'  #  | ....3.F>L....3.S
    msg +=  b'\x00\x00\x00\x00\x34\x58\x53\x00\x00\x00\x00\x34\xbc\x53\x04\x00'  #  | ....4XS....4.S..
    msg +=  b'\x00\x00\x35\x20\x53\x00\x01\x00\x00\x35\x84\x53\x13\x9c\x00\x00'  #  | ..5 S....5.S....
    msg +=  b'\x35\xe8\x53\x0f\xa0\x00\x00\x36\x4c\x53\x00\x00\x00\x00\x36\xb0'  #  | 5.S....6LS....6.
    msg +=  b'\x53\x00\x66'                                                      #  | S.f'
    return msg

@pytest.mark.asyncio(loop_scope="session")
async def test_read_message(msg_contact_info):
    Config.act_config = {'tsun':{'enabled': True}}
    m = MemoryStream(msg_contact_info, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == None
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==23
    assert m.data_len==25
    assert m.ifc.rx_get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.ifc.fwd_fifo.get()==b''
    m.close()

def test_read_message_twice(config_no_tsun_inv1, msg_inverter_ind):
    _ = config_no_tsun_inv1
    m = MemoryStream(msg_inverter_ind, (0,))
    m.append_msg(msg_inverter_ind)
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 2
    assert m.msg_recvd[0]['ctrl']==145
    assert m.msg_recvd[0]['msg_id']==4
    assert m.msg_recvd[0]['header_len']==23
    assert m.msg_recvd[0]['data_len']==120
    assert m.msg_recvd[1]['ctrl']==145
    assert m.msg_recvd[1]['msg_id']==4
    assert m.msg_recvd[1]['header_len']==23
    assert m.msg_recvd[1]['data_len']==120
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert m.ifc.fwd_fifo.get()==b''
    m.close()
 
def test_read_message_long_id(msg_contact_info_long_id):
    m = MemoryStream(msg_contact_info_long_id, (23,24))
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
    

def test_read_message_in_chunks(msg_contact_info):
    Config.act_config = {'tsun':{'enabled': True}}
    m = MemoryStream(msg_contact_info, (4,23,0))
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
    
def test_read_message_in_chunks2(msg_contact_info):
    Config.act_config = {'tsun':{'enabled': True}}
    m = MemoryStream(msg_contact_info, (4,10,0))
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

def test_read_two_messages(config_tsun_allow_all, msg2_contact_info,msg_contact_rsp,msg_contact_rsp2):
    _ = config_tsun_allow_all
    m = MemoryStream(msg2_contact_info, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 2
    assert m.id_str == b"R170000000000002" 
    assert m.unique_id == 'R170000000000002'
    m.contact_name = b'solarhub'
    m.contact_mail = b'solarhub@123456'
    assert m.msg_recvd[0]['ctrl']==145
    assert m.msg_recvd[0]['msg_id']==0
    assert m.msg_recvd[0]['header_len']==23
    assert m.msg_recvd[0]['data_len']==25
    assert m.msg_recvd[1]['ctrl']==145
    assert m.msg_recvd[1]['msg_id']==0
    assert m.msg_recvd[1]['header_len']==23
    assert m.msg_recvd[1]['data_len']==25
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==msg_contact_rsp + msg_contact_rsp2
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0

    m.ifc.tx_clear() # clear send buffer for next test    
    m.contact_name = b'solarhub'
    m.contact_mail = b'solarhub@123456'
    m._init_new_client_conn()
    assert m.ifc.tx_fifo.get()==b'\x00\x00\x00,\x10R170000000000002\x91\x00\x08solarhub\x0fsolarhub@123456'
    m.close()

def test_conttact_req(config_tsun_allow_all, msg_contact_info, msg_contact_rsp):
    _ = config_tsun_allow_all
    m = MemoryStream(msg_contact_info, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.contact_name == b'solarhub'
    assert m.contact_mail == b'solarhub@123456'
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==23
    assert m.data_len==25
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==msg_contact_rsp
    m.close()

def test_contact_broken_req(config_tsun_allow_all, msg_contact_info_broken, msg_contact_rsp):
    _ = config_tsun_allow_all
    m = MemoryStream(msg_contact_info_broken, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.contact_name == b''
    assert m.contact_mail == b''
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==23
    assert m.data_len==23
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==msg_contact_rsp
    m.close()

def test_conttact_req(config_tsun_allow_all, msg_contact_info, msg_contact_rsp):
    _ = config_tsun_allow_all
    m = MemoryStream(msg_contact_info, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.contact_name == b'solarhub'
    assert m.contact_mail == b'solarhub@123456'
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==23
    assert m.data_len==25
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==msg_contact_rsp
    m.close()

def test_contact_broken_req(config_tsun_allow_all, msg_contact_info_broken, msg_contact_rsp):
    _ = config_tsun_allow_all
    m = MemoryStream(msg_contact_info_broken, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.contact_name == b''
    assert m.contact_mail == b''
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==0 
    assert m.header_len==23
    assert m.data_len==23
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==msg_contact_rsp
    m.close()

def test_msg_contact_resp(config_tsun_inv1, msg_contact_rsp):
    _ = config_tsun_inv1
    m = MemoryStream(msg_contact_rsp, (0,), False)
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
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_contact_resp_2(config_tsun_inv1, msg_contact_rsp):
    _ = config_tsun_inv1
    m = MemoryStream(msg_contact_rsp, (0,), False)
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
    assert m.ifc.fwd_fifo.get()==msg_contact_rsp
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_contact_resp_3(config_tsun_inv1, msg_contact_rsp):
    _ = config_tsun_inv1
    m = MemoryStream(msg_contact_rsp, (0,), True)
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
    assert m.ifc.fwd_fifo.get()==msg_contact_rsp
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_contact_invalid(config_tsun_inv1, msg_contact_invalid):
    _ = config_tsun_inv1
    m = MemoryStream(msg_contact_invalid, (0,))
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
    assert m.ifc.fwd_fifo.get()==msg_contact_invalid
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()

def test_msg_get_time(config_tsun_inv1, msg_get_time):
    _ = config_tsun_inv1
    m = MemoryStream(msg_get_time, (0,))
    m.state = State.up
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
    assert m.state==State.pend
    assert m.ifc.fwd_fifo.get()==msg_get_time
    assert m.ifc.tx_fifo.get()==b'\x00\x00\x00\x1b\x10R170000000000001\x91"\x00\x00\x01\x89\xc6,_\x00'
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_get_time_autark(config_no_tsun_inv1, msg_get_time):
    _ = config_no_tsun_inv1
    m = MemoryStream(msg_get_time, (0,))
    m.state = State.received
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
    assert m.state==State.received
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==bytearray(b'\x00\x00\x00\x1b\x10R170000000000001\x91"\x00\x00\x01\x89\xc6,_\x00')
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_time_resp(config_tsun_inv1, msg_time_rsp):
    # test if ts_offset will be set on client and server side
    _ = config_tsun_inv1
    m = MemoryStream(msg_time_rsp, (0,), False)
    s = MemoryStream(b'', (0,), True)
    assert s.ts_offset==0
    m.ifc.remote.stream = s
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
    assert s.ts_offset==3600000
    assert m.data_len==8
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.ifc.remote.stream = None
    s.close()
    m.close()

def test_msg_time_resp_autark(config_no_tsun_inv1, msg_time_rsp):
    _ = config_no_tsun_inv1
    m = MemoryStream(msg_time_rsp, (0,), False)
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
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_time_inv_resp(config_tsun_inv1, msg_time_rsp_inv):
    _ = config_tsun_inv1
    m = MemoryStream(msg_time_rsp_inv, (0,), False)
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
    assert m.ifc.fwd_fifo.get()==msg_time_rsp_inv
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_time_invalid(config_tsun_inv1, msg_time_invalid):
    _ = config_tsun_inv1
    m = MemoryStream(msg_time_invalid, (0,), False)
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
    assert m.ifc.fwd_fifo.get()==msg_time_invalid
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()

def test_msg_time_invalid_autark(config_no_tsun_inv1, msg_time_invalid):
    _ = config_no_tsun_inv1
    m = MemoryStream(msg_time_invalid, (0,), False)
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
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()

def test_msg_act_time(config_no_modbus_poll, msg_act_time, msg_act_time_ack):
    _ = config_no_modbus_poll
    m = MemoryStream(msg_act_time, (0,))
    m.ts_offset=0
    m.mb_timeout = 124
    m.db.set_db_def_value(Register.POLLING_INTERVAL, 125)
    m.state = State.received
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==153
    assert m.ts_offset==0
    assert m.header_len==23
    assert m.data_len==9
    assert m.state == State.up
    assert m.ifc.fwd_fifo.get()==msg_act_time
    assert m.ifc.tx_fifo.get()==msg_act_time_ack
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert 125 == m.db.get_db_value(Register.POLLING_INTERVAL, 0)
    m.close()

def test_msg_act_time2(config_tsun_inv1, msg_act_time, msg_act_time_ack):
    _ = config_tsun_inv1
    m = MemoryStream(msg_act_time, (0,))
    m.ts_offset=0
    m.modbus_polling = True
    m.mb_timeout = 123
    m.db.set_db_def_value(Register.POLLING_INTERVAL, 125)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==153
    assert m.ts_offset==0
    assert m.header_len==23
    assert m.data_len==9
    assert m.ifc.fwd_fifo.get()==msg_act_time
    assert m.ifc.tx_fifo.get()==msg_act_time_ack
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert 123 == m.db.get_db_value(Register.POLLING_INTERVAL, 0)
    m.close()

def test_msg_act_time_ofs(config_tsun_inv1, msg_act_time, msg_act_time_ofs, msg_act_time_ack):
    _ = config_tsun_inv1
    m = MemoryStream(msg_act_time, (0,))
    m.ts_offset=3600
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==153
    assert m.ts_offset==3600
    assert m.header_len==23
    assert m.data_len==9
    assert m.ifc.fwd_fifo.get()==msg_act_time_ofs
    assert m.ifc.tx_fifo.get()==msg_act_time_ack
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_act_time_ofs2(config_tsun_inv1, msg_act_time, msg_act_time_ofs, msg_act_time_ack):
    _ = config_tsun_inv1
    m = MemoryStream(msg_act_time_ofs, (0,))
    m.ts_offset=-3600
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==153
    assert m.ts_offset==-3600
    assert m.header_len==23
    assert m.data_len==9
    assert m.ifc.fwd_fifo.get()==msg_act_time
    assert m.ifc.tx_fifo.get()==msg_act_time_ack
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_act_time_autark(config_no_tsun_inv1, msg_act_time, msg_act_time_ack):
    _ = config_no_tsun_inv1
    m = MemoryStream(msg_act_time, (0,))
    m.ts_offset=0
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==153
    assert m.ts_offset==0
    assert m.header_len==23
    assert m.data_len==9
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==msg_act_time_ack
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_act_time_ack(config_tsun_inv1, msg_act_time_ack):
    _ = config_tsun_inv1
    m = MemoryStream(msg_act_time_ack, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==153
    assert m.msg_id==153
    assert m.header_len==23
    assert m.data_len==1
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_act_time_cmd(config_tsun_inv1, msg_act_time_cmd):
    _ = config_tsun_inv1
    m = MemoryStream(msg_act_time_cmd, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==112
    assert m.msg_id==153
    assert m.header_len==23
    assert m.data_len==1
    assert m.ifc.fwd_fifo.get()==msg_act_time_cmd
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()

def test_msg_act_time_inv(config_tsun_inv1, msg_act_time_inv):
    _ = config_tsun_inv1
    m = MemoryStream(msg_act_time_inv, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==153
    assert m.header_len==23
    assert m.data_len==8
    assert m.ifc.fwd_fifo.get()==msg_act_time_inv
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_cntrl_ind(config_tsun_inv1, msg_controller_ind, msg_controller_ind_ts_offs, msg_controller_ack):
    _ = config_tsun_inv1
    m = MemoryStream(msg_controller_ind, (0,))
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
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.peek()==msg_controller_ind
    m.ts_offset = -4096
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.get()==msg_controller_ind_ts_offs
    assert m.ifc.tx_fifo.get()==msg_controller_ack
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_cntrl_ack(config_tsun_inv1, msg_controller_ack):
    _ = config_tsun_inv1
    m = MemoryStream(msg_controller_ack, (0,), False)
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
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_cntrl_invalid(config_tsun_inv1, msg_controller_invalid):
    _ = config_tsun_inv1
    m = MemoryStream(msg_controller_invalid, (0,))
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
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.peek()==msg_controller_invalid
    m.ts_offset = -4096
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.get()==msg_controller_invalid
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()

def test_msg_inv_ind(config_tsun_inv1, msg_inverter_ind, msg_inverter_ind_ts_offs, msg_inverter_ack):
    _ = config_tsun_inv1
    tracer.setLevel(logging.DEBUG)
    m = MemoryStream(msg_inverter_ind, (0,))
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
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.peek()==msg_inverter_ind
    m.ts_offset = +256
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.get()==msg_inverter_ind_ts_offs
    assert m.ifc.tx_fifo.get()==msg_inverter_ack
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_inv_ind1(config_tsun_inv1, msg_inverter_ind2, msg_inverter_ind_ts_offs, msg_inverter_ack):
    _ = config_tsun_inv1
    tracer.setLevel(logging.DEBUG)
    m = MemoryStream(msg_inverter_ind2, (0,))
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
    assert m.data_len==1263
    m.ts_offset = 0
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.get()==msg_inverter_ind2
    assert m.ifc.tx_fifo.get()==msg_inverter_ack
    assert m.db.get_db_value(Register.TS_GRID) == 1691243349
    m.close()

def test_msg_inv_ind2(config_tsun_inv1, msg_inverter_ind_new, msg_inverter_ind_ts_offs, msg_inverter_ack):
    _ = config_tsun_inv1
    tracer.setLevel(logging.DEBUG)
    m = MemoryStream(msg_inverter_ind_new, (0,))
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
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.get()==msg_inverter_ind_new
    assert m.ifc.tx_fifo.get()==msg_inverter_ack
    assert m.db.get_db_value(Register.INVERTER_STATUS) == None
    assert m.db.get_db_value(Register.TS_GRID) == None
    m.db.db['grid'] = {'Output_Power': 100}
    m.close()
    assert m.db.get_db_value(Register.INVERTER_STATUS) == None

def test_msg_inv_ind3(config_tsun_inv1, msg_inverter_ind_0w, msg_inverter_ack):
    '''test that after close the invert_status will be resetted if the grid power is <2W'''
    _ = config_tsun_inv1
    tracer.setLevel(logging.DEBUG)
    m = MemoryStream(msg_inverter_ind_0w, (0,))
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
    assert m.data_len==1263
    m.ts_offset = 0
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.get()==msg_inverter_ind_0w
    assert m.ifc.tx_fifo.get()==msg_inverter_ack
    assert m.db.get_db_value(Register.INVERTER_STATUS) == 1
    assert isclose(m.db.db['grid']['Output_Power'], 0.5)
    m.close()
    assert m.db.get_db_value(Register.INVERTER_STATUS) == 0

def test_msg_inv_ind4(config_tsun_inv1, msg_inverter_ms3000_ind, msg_inverter_ack):
    '''Check sonar_lists of MS-3000 inverter'''
    _ = config_tsun_inv1
    tracer.setLevel(logging.DEBUG)
    with patch.object(logging, 'warning') as spy:
        m = MemoryStream(msg_inverter_ms3000_ind, (0,))
        m.db.stat['proxy']['Unknown_Ctrl'] = 0
        m.db.stat['proxy']['Invalid_Data_Type'] = 0
        m.read()         # read complete msg, and dispatch msg
        spy.assert_not_called()
        assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
        assert m.db.stat['proxy']['Invalid_Data_Type'] == 0
        assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
        assert m.msg_count == 1
        assert m.id_str == b"R170000000000001" 
        assert m.unique_id == 'R170000000000001'
        assert int(m.ctrl)==145
        assert m.msg_id==4
        assert m.header_len==23
        assert m.data_len==2284
        m.ts_offset = 0
        m._update_header(m.ifc.fwd_fifo.peek())
        assert m.ifc.fwd_fifo.get()==msg_inverter_ms3000_ind
        assert m.ifc.tx_fifo.get()==msg_inverter_ack
        assert m.db.get_db_value(Register.INVERTER_STATUS) == 0
        assert m.db.get_db_value(Register.TS_GRID) == 1739866976
        m.db.db['grid'] = {'Output_Power': 100}
        m.close()

def test_msg_inv_ind5(config_tsun_inv1, msg_inverter_ms3000_ind, msg_inverter_ack):
    '''Check that unexpected sonar_lists will log a warning'''
    _ = config_tsun_inv1
    tracer.setLevel(logging.DEBUG)
    with patch.object(logging, 'warning') as spy:
        m = MemoryStream(msg_inverter_ms3000_ind, (0,))
        m.sensor_list = 0x01900002    # change the expected sensor_list
        m.db.stat['proxy']['Unknown_Ctrl'] = 0
        m.db.stat['proxy']['Invalid_Data_Type'] = 0
        m.read()         # read complete msg, and dispatch msg
        spy.assert_called()
        assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
        assert m.db.stat['proxy']['Invalid_Data_Type'] == 0
        assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
        assert m.msg_count == 1
        assert m.id_str == b"R170000000000001" 
        assert m.unique_id == 'R170000000000001'
        assert int(m.ctrl)==145
        assert m.msg_id==4
        assert m.header_len==23
        assert m.data_len==2284
        m.ts_offset = 0
        m._update_header(m.ifc.fwd_fifo.peek())
        assert m.ifc.fwd_fifo.get()==msg_inverter_ms3000_ind
        assert m.ifc.tx_fifo.get()==msg_inverter_ack
        assert m.db.get_db_value(Register.INVERTER_STATUS) == 0
        assert m.db.get_db_value(Register.TS_GRID) == 1739866976
        m.db.db['grid'] = {'Output_Power': 100}
        m.close()

def test_msg_inv_ack(config_tsun_inv1, msg_inverter_ack):
    _ = config_tsun_inv1
    tracer.setLevel(logging.ERROR)

    m = MemoryStream(msg_inverter_ack, (0,), False)
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
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

def test_msg_inv_invalid(config_tsun_inv1, msg_inverter_invalid):
    _ = config_tsun_inv1
    m = MemoryStream(msg_inverter_invalid, (0,), False)
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
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.peek()==msg_inverter_invalid
    m.ts_offset = 256
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.get()==msg_inverter_invalid
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    m.close()

def test_build_modell_3000(config_tsun_allow_all, msg_inverter_ms3000_ind):
    _ = config_tsun_allow_all
    m = MemoryStream(msg_inverter_ms3000_ind, (0,))
    assert 0 == m.db.get_db_value(Register.MAX_DESIGNED_POWER, 0)
    assert None == m.db.get_db_value(Register.RATED_POWER, None)
    assert None == m.db.get_db_value(Register.INVERTER_TEMP, None)
    m.read()         # read complete msg, and dispatch msg
    assert 3000 == m.db.get_db_value(Register.MAX_DESIGNED_POWER, 0)
    assert 0 == m.db.get_db_value(Register.RATED_POWER, 0)
    assert 'TSOL-MS3000' == m.db.get_db_value(Register.EQUIPMENT_MODEL, 0)
    m.close()

def test_msg_ota_req(config_tsun_inv1, msg_ota_req):
    _ = config_tsun_inv1
    m = MemoryStream(msg_ota_req, (0,), False)
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
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.peek()==msg_ota_req
    m.ts_offset = 4096
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.get()==msg_ota_req
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['OTA_Start_Msg'] == 1
    m.close()

def test_msg_ota_ack(config_tsun_inv1, msg_ota_ack):
    _ = config_tsun_inv1
    tracer.setLevel(logging.ERROR)

    m = MemoryStream(msg_ota_ack, (0,), False)
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
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.peek()==msg_ota_ack
    m.ts_offset = 256
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.get()==msg_ota_ack
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['OTA_Start_Msg'] == 0
    m.close()

def test_msg_ota_invalid(config_tsun_inv1, msg_ota_invalid):
    _ = config_tsun_inv1
    m = MemoryStream(msg_ota_invalid, (0,), False)
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
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.fwd_fifo.peek()==msg_ota_invalid
    m.ts_offset = 4096
    assert m.ifc.fwd_fifo.get()==msg_ota_invalid
    m._update_header(m.ifc.fwd_fifo.peek())
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    assert m.db.stat['proxy']['OTA_Start_Msg'] == 0
    m.close()

def test_msg_unknown(config_tsun_inv1, msg_unknown):
    _ = config_tsun_inv1
    m = MemoryStream(msg_unknown, (0,), False)
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
    assert m.ifc.fwd_fifo.get()==msg_unknown
    assert m.ifc.tx_fifo.get()==b''
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
    m1 = Talent(None, ('test1.local', 1234), ifc=AsyncIfcImpl(), server_side=True)
    m2 = Talent(None, ('test2.local', 1234), ifc=AsyncIfcImpl(), server_side=True)
    m3 = Talent(None, ('test3.local', 1234), ifc=AsyncIfcImpl(), server_side=True)
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

def test_timestamp_cnv():
    '''test converting inverter timestamps into utc'''
    m = MemoryStream(b'')
    ts = 1722645998453    # Saturday, 3. August 2024 00:46:38.453 (GMT+2:00)
    utc =1722638798.453   # GMT: Friday, 2. August 2024 22:46:38.453
    assert isclose(utc, m._utcfromts(ts))

    ts = 1691246944000    # Saturday, 5. August 2023 14:49:04 (GMT+2:00)
    utc =1691239744.0     # GMT: Saturday, 5. August 2023 12:49:04
    assert isclose(utc, m._utcfromts(ts))

    ts = 1704152544000    # Monday, 1. January 2024 23:42:24 (GMT+1:00)
    utc =1704148944.0     # GMT: Monday, 1. January 2024 22:42:24
    assert isclose(utc, m._utcfromts(ts))

    m.close()

def test_proxy_counter():
    Infos.stat['proxy']['Modbus_Command'] = 1
 
    m = MemoryStream(b'')
    m.id_str = b"R170000000000001" 
    c = m.createClientStream(b'')

    assert m.new_data == {'status': True}
    m.db.stat['proxy']['Unknown_Msg'] = 0
    c.db.stat['proxy']['Unknown_Msg'] = 0
    Infos.new_stat_data['proxy'] =  False

    m.inc_counter('Unknown_Msg')
    m.close()
    m = MemoryStream(b'')
   
    assert m.new_data == {'status': True}
    assert Infos.new_stat_data == {'proxy': True}
    assert m.db.new_stat_data == {'proxy': True}
    assert c.db.new_stat_data == {'proxy': True}
    assert 1 == m.db.stat['proxy']['Unknown_Msg']
    assert 1 == c.db.stat['proxy']['Unknown_Msg']
    Infos.new_stat_data['proxy'] =  False

    c.inc_counter('Unknown_Msg')
    assert m.new_data == {'status': True}
    assert Infos.new_stat_data == {'proxy': True}
    assert m.db.new_stat_data == {'proxy': True}
    assert c.db.new_stat_data == {'proxy': True}
    assert 2 == m.db.stat['proxy']['Unknown_Msg']
    assert 2 == c.db.stat['proxy']['Unknown_Msg']
    Infos.new_stat_data['proxy'] =  False

    c.inc_counter('Modbus_Command')
    assert m.new_data == {'status': True}
    assert Infos.new_stat_data == {'proxy': True}
    assert m.db.new_stat_data == {'proxy': True}
    assert c.db.new_stat_data == {'proxy': True}
    assert 2 == m.db.stat['proxy']['Modbus_Command']
    assert 2 == c.db.stat['proxy']['Modbus_Command']

    Infos.new_stat_data['proxy'] =  False
    m.dec_counter('Unknown_Msg')
    assert m.new_data == {'status': True}
    assert Infos.new_stat_data == {'proxy': True}
    assert 1 == m.db.stat['proxy']['Unknown_Msg']
    m.close()

def test_msg_modbus_req(config_tsun_inv1, msg_modbus_cmd):
    _ = config_tsun_inv1
    m = MemoryStream(b'')
    m.id_str = b"R170000000000001" 
    m.state = State.up

    c = m.createClientStream(msg_modbus_cmd)
    
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
    assert c.ifc.fwd_fifo.get()==b''
    assert c.ifc.tx_fifo.get()==b''
    assert m.id_str == b"R170000000000001" 
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.sent_pdu == msg_modbus_cmd
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 1
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_msg_modbus_req2(config_tsun_inv1, msg_modbus_cmd):
    _ = config_tsun_inv1
    m = MemoryStream(b'')
    m.id_str = b"R170000000000001" 

    c = m.createClientStream(msg_modbus_cmd)
    
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
    assert c.ifc.fwd_fifo.get()==b''
    assert c.ifc.tx_fifo.get()==b''
    assert m.id_str == b"R170000000000001" 
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.sent_pdu == b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 1
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_msg_modbus_req3(config_tsun_inv1, msg_modbus_cmd_crc_err):
    _ = config_tsun_inv1
    m = MemoryStream(b'')
    m.id_str = b"R170000000000001" 
    c = m.createClientStream(msg_modbus_cmd_crc_err)
    
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
    assert c.ifc.fwd_fifo.get()==b''
    assert c.ifc.tx_fifo.get()==b''
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.sent_pdu ==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 1
    m.close()

def test_msg_modbus_rsp1(config_tsun_inv1, msg_modbus_rsp):
    '''Modbus response without a valid Modbus request must be dropped'''
    _ = config_tsun_inv1
    m = MemoryStream(msg_modbus_rsp)
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
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_msg_modbus_cloud_rsp(config_tsun_inv1, msg_modbus_rsp):
    '''Modbus response from TSUN without a valid Modbus request must be dropped'''
    _ = config_tsun_inv1
    m = MemoryStream(msg_modbus_rsp, (0,), False)
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
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Msg'] == 1
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_msg_modbus_rsp2(config_tsun_inv1, msg_modbus_rsp20):
    '''Modbus response with a valid Modbus request must be forwarded'''
    _ = config_tsun_inv1
    m = MemoryStream(msg_modbus_rsp20)
    m.append_msg(msg_modbus_rsp20)

    m.mb.rsp_handler = m.msg_forward
    m.mb.last_addr = 1
    m.mb.last_fcode = 3
    m.mb.last_len = 20
    m.mb.last_reg = 0x3008
    m.mb.req_pend = True
    m.mb.err = 0

    assert m.db.db == {'status': {'status': 'on'}}
    m.new_data['inverter'] = False

    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.mb.err == 5
    assert m.msg_count == 2
    assert m.ifc.fwd_fifo.get()==msg_modbus_rsp20
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.db == {'status': {'status': 'on'}, 'collector': {'Serial_Number': 'R170000000000001'}, 'inverter': {'Version': 'V5.1.09', 'Rated_Power': 300}, 'grid': {'Timestamp': m._utc(), 'Voltage': 225.9, 'Current': 0.41, 'Frequency': 49.99, 'Output_Power': 94.8}, 'env': {'Inverter_Temp': 22}, 'input': {'Timestamp': m._utc(), 'pv1': {'Voltage': 0.8, 'Current': 0.0, 'Power': 0.0}, 'pv2': {'Voltage': 34.5, 'Current': 2.89, 'Power': 99.8}, 'pv3': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}, 'pv4': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}}}
    assert m.db.get_db_value(Register.VERSION) == 'V5.1.09'
    assert m.db.get_db_value(Register.TS_GRID) == m._utc()
    assert m.new_data['inverter'] == True

    m.close()

def test_msg_modbus_rsp3(config_tsun_inv1, msg_modbus_rsp21):
    '''Modbus response with a valid Modbus request must be forwarded'''
    _ = config_tsun_inv1
    m = MemoryStream(msg_modbus_rsp21)
    m.append_msg(msg_modbus_rsp21)

    m.mb.rsp_handler = m.msg_forward
    m.mb.last_addr = 1
    m.mb.last_fcode = 3
    m.mb.last_len = 20
    m.mb.last_reg = 0x3008
    m.mb.req_pend = True
    m.mb.err = 0

    assert m.db.db == {'status': {'status': 'on'}}
    m.new_data['inverter'] = False

    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.mb.err == 5
    assert m.msg_count == 2
    assert m.ifc.fwd_fifo.get()==msg_modbus_rsp21
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.db == {'status': {'status': 'on'}, 'collector': {'Serial_Number': 'R170000000000001'}, 'inverter': {'Version': 'V5.1.0E', 'Rated_Power': 300}, 'grid': {'Timestamp': m._utc(), 'Voltage': 225.9, 'Current': 0.41, 'Frequency': 49.99, 'Output_Power': 94.8}, 'env': {'Inverter_Temp': 22}, 'input': {'Timestamp': m._utc(), 'pv1': {'Voltage': 0.8, 'Current': 0.0, 'Power': 0.0}, 'pv2': {'Voltage': 34.5, 'Current': 2.89, 'Power': 99.8}, 'pv3': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}, 'pv4': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}}}
    assert m.db.get_db_value(Register.VERSION) == 'V5.1.0E'
    assert m.db.get_db_value(Register.TS_GRID) == m._utc()
    assert m.new_data['inverter'] == True

    m.close()

def test_msg_modbus_rsp4(config_tsun_inv1, msg_modbus_rsp21):
    '''Modbus response with a valid Modbus but no new values request must be forwarded'''
    _ = config_tsun_inv1
    m = MemoryStream(msg_modbus_rsp21)
 
    m.mb.rsp_handler = m.msg_forward
    m.mb.last_addr = 1
    m.mb.last_fcode = 3
    m.mb.last_len = 20
    m.mb.last_reg = 0x3008
    m.mb.req_pend = True
    m.mb.err = 0
    db_values = {'collector': {'Serial_Number': 'R170000000000001'}, 'inverter': {'Version': 'V5.1.0E', 'Rated_Power': 300}, 'grid': {'Timestamp': m._utc(), 'Voltage': 225.9, 'Current': 0.41, 'Frequency': 49.99, 'Output_Power': 94.8}, 'env': {'Inverter_Temp': 22}, 'input': {'Timestamp': m._utc(), 'pv1': {'Voltage': 0.8, 'Current': 0.0, 'Power': 0.0}, 'pv2': {'Voltage': 34.5, 'Current': 2.89, 'Power': 99.8}, 'pv3': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}, 'pv4': {'Voltage': 0.0, 'Current': 0.0, 'Power': 0.0}}}
    m.db.db  = db_values
    m.new_data['inverter'] = False

    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.mb.err == 0
    assert m.msg_count == 1
    assert m.ifc.fwd_fifo.get()==msg_modbus_rsp21
    assert m.modbus_elms == 19
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.db == db_values
    assert m.db.get_db_value(Register.VERSION) == 'V5.1.0E'
    assert m.db.get_db_value(Register.TS_GRID) == m._utc()
    assert m.new_data['inverter'] == False

    m.close()

def test_msg_modbus_rsp_new(config_tsun_inv1, msg_modbus_rsp20_new):
    '''Modbus response in new format with a valid Modbus request must be forwarded'''
    _ = config_tsun_inv1
    m = MemoryStream(msg_modbus_rsp20_new)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==135
    assert m.header_len==23
    assert m.data_len==107
    assert m.ifc.fwd_fifo.get()==b''
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_msg_modbus_invalid(config_tsun_inv1, msg_modbus_inv):
    _ = config_tsun_inv1
    m = MemoryStream(msg_modbus_inv, (0,), False)
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
    assert m.ifc.fwd_fifo.get()==msg_modbus_inv
    assert m.ifc.tx_fifo.get()==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 1
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_msg_modbus_fragment(config_tsun_inv1, msg_modbus_rsp20):
    _ = config_tsun_inv1
    # receive more bytes than expected (7 bytes from the next msg)
    m = MemoryStream(msg_modbus_rsp20+b'\x00\x00\x00\x45\x10\x52\x31', (0,))
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
    assert m.ifc.fwd_fifo.get()==msg_modbus_rsp20
    assert m.ifc.tx_fifo.get() == b''
    assert m.mb.err == 0
    assert m.modbus_elms == 20-1  # register 0x300d is unknown, so one value can't be mapped
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_msg_build_modbus_req(config_tsun_inv1, msg_modbus_cmd):
    _ = config_tsun_inv1
    m = MemoryStream(b'', (0,), True)
    m.id_str = b"R170000000000001" 
    m.send_modbus_cmd(Modbus.WRITE_SINGLE_REG, 0x2008, 0, logging.DEBUG)
    assert 0 == m.send_msg_ofs
    assert m.ifc.fwd_fifo.get() == b''
    assert m.ifc.tx_fifo.get() == b''
    assert m.sent_pdu == b''

    m.state = State.up
    m.send_modbus_cmd(Modbus.WRITE_SINGLE_REG, 0x2008, 0, logging.DEBUG)
    assert 0 == m.send_msg_ofs
    assert m.ifc.fwd_fifo.get() == b''
    assert m.ifc.tx_fifo.get() == b''
    assert m.sent_pdu == msg_modbus_cmd
    m.close()

def test_modbus_no_polling(config_no_modbus_poll, msg_get_time):
    _ = config_no_modbus_poll
    m = MemoryStream(msg_get_time, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.modbus_polling = False
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
    assert m.ifc.fwd_fifo.get()==msg_get_time
    assert m.ifc.tx_fifo.get()==b'\x00\x00\x00\x1b\x10R170000000000001\x91"\x00\x00\x01\x89\xc6,_\x00'
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    m.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_modbus_polling(config_tsun_inv1, msg_inverter_ind):
    _ = config_tsun_inv1
    assert asyncio.get_running_loop()

    m = MemoryStream(msg_inverter_ind, (0,))
    assert asyncio.get_running_loop() == m.mb_timer.loop
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    assert m.mb_timer.tim == None
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert int(m.ctrl)==145
    assert m.msg_id==4
    assert m.header_len==23
    assert m.ts_offset==0
    assert m.data_len==120
    assert m.ifc.fwd_fifo.get()==msg_inverter_ind
    assert m.ifc.tx_fifo.get()==b'\x00\x00\x00\x14\x10R170000000000001\x99\x04\x01'
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0

    m.ifc.tx_clear() # clear send buffer for next test
    assert isclose(m.mb_timeout, 0.5)
    assert next(m.mb_timer.exp_count) == 0
    
    await asyncio.sleep(0.5)
    assert m.sent_pdu==b'\x00\x00\x00 \x10R170000000000001pw\x00\x01\xa3(\x08\x01\x030\x00\x000J\xde'
    assert m.ifc.tx_fifo.get()==b''
    
    await asyncio.sleep(0.5)
    assert m.sent_pdu==b'\x00\x00\x00 \x10R170000000000001pw\x00\x01\xa3(\x08\x01\x030\x00\x000J\xde'
    assert m.ifc.tx_fifo.get()==b''
    
    await asyncio.sleep(0.5)
    assert m.sent_pdu==b'\x00\x00\x00 \x10R170000000000001pw\x00\x01\xa3(\x08\x01\x03\x20\x00\x00`N"'
    assert m.ifc.tx_fifo.get()==b''
    assert next(m.mb_timer.exp_count) == 4
    m.close()

@pytest.mark.asyncio(loop_scope="session")
async def test_modbus_scaning(config_tsun_inv1, msg_inverter_ind, msg_modbus_rsp21):
    _ = config_tsun_inv1
    assert asyncio.get_running_loop()

    m = MemoryStream(msg_inverter_ind, (0x8f,0))
    m.append_msg(msg_modbus_rsp21)
    m.mb_scan = True
    m.mb_start_reg = 0x4560
    m.mb_bytes = 0x14
    assert asyncio.get_running_loop() == m.mb_timer.loop
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    assert m.mb_timer.tim == None
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert m.msg_recvd[0]['ctrl']==145
    assert m.msg_recvd[0]['msg_id']==4
    assert m.msg_recvd[0]['header_len']==23
    assert m.msg_recvd[0]['data_len']==120
    assert m.ifc.fwd_fifo.get()==msg_inverter_ind
    assert m.ifc.tx_fifo.get()==b'\x00\x00\x00\x14\x10R170000000000001\x99\x04\x01'
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0

    m.ifc.tx_clear() # clear send buffer for next test
    assert isclose(m.mb_timeout, 0.5)
    assert next(m.mb_timer.exp_count) == 0
    
    await asyncio.sleep(0.5)
    assert m.sent_pdu==b'\x00\x00\x00 \x10R170000000000001pw\x00\x01\xa3(\x08\x01\x03\x45\x60\x00\x14\x50\xd7'
    assert m.ifc.tx_fifo.get()==b''

    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 2
    assert m.msg_recvd[1]['ctrl']==145
    assert m.msg_recvd[1]['msg_id']==119
    assert m.msg_recvd[1]['header_len']==23
    assert m.msg_recvd[1]['data_len']==50
    assert m.mb.last_addr == 1
    assert m.mb.last_fcode == 3   
    assert m.mb.last_reg == 0x4560
    assert m.mb.last_len == 20
    assert m.mb.err == 0
    
    assert next(m.mb_timer.exp_count) == 2
    m.close()

def test_broken_recv_buf(config_tsun_allow_all, broken_recv_buf):
    _ = config_tsun_allow_all
    m = MemoryStream(broken_recv_buf, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    assert m.db.stat['proxy']['Invalid_Data_Type'] == 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert m.msg_recvd[0]['ctrl']==145
    assert m.msg_recvd[0]['msg_id']==4
    assert m.msg_recvd[0]['header_len']==23
    assert m.msg_recvd[0]['data_len']==1263
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Invalid_Data_Type'] == 1

    m.close()

def test_multiiple_recv_buf(config_tsun_allow_all, multiple_recv_buf):
    _ = config_tsun_allow_all
    m = MemoryStream(multiple_recv_buf, (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Invalid_Msg_Format'] = 0
    m.db.stat['proxy']['Invalid_Data_Type'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'
    assert m.msg_recvd[0]['ctrl']==145
    assert m.msg_recvd[0]['msg_id']==4
    assert m.msg_recvd[0]['header_len']==23
    assert m.msg_recvd[0]['data_len']==1263
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 1
    assert m.db.stat['proxy']['Invalid_Data_Type'] == 1

    m.close()

def test_timeout(config_tsun_inv1):
    _ = config_tsun_inv1
    m = MemoryStream(b'')
    assert m.state == State.init
    assert Talent.MAX_START_TIME == m._timeout()
    m.state = State.up
    m.modbus_polling = True
    assert Talent.MAX_INV_IDLE_TIME == m._timeout()
    m.modbus_polling = False
    assert Talent.MAX_DEF_IDLE_TIME == m._timeout()
    m.close()

def test_msg_inv_replay(config_tsun_inv1, msg_inverter_ind_0w, msg_inverter_ind_new2):
    '''replay must be ignores, since HA only supports realtime values'''
    _ = config_tsun_inv1

    m = MemoryStream(msg_inverter_ind_0w, (0,))   # realtime msg with 0.5W Output Power
    m.append_msg(msg_inverter_ind_new2)           # replay msg with 506.6W Output Power
    m.db.db['grid'] = {'Output_Power': 100}
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Invalid_Data_Type'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Invalid_Data_Type'] == 0
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 2
    assert m.msg_recvd[0]['ctrl']==145
    assert m.msg_recvd[0]['msg_id']==4
    assert m.msg_recvd[0]['header_len']==23
    assert m.msg_recvd[0]['data_len']==1263
    assert m.msg_recvd[1]['ctrl']==145
    assert m.msg_recvd[1]['msg_id']==4
    assert m.msg_recvd[1]['header_len']==23
    assert m.msg_recvd[1]['data_len']==1249
    assert m.id_str == b"R170000000000001" 
    assert m.unique_id == 'R170000000000001'

    assert m.db.get_db_value(Register.INVERTER_STATUS) == 1
    assert isclose(m.db.db['grid']['Output_Power'], 0.5)  # must be 0.5W not 100W nor 506.6W

    m.close()
    assert m.db.get_db_value(Register.INVERTER_STATUS) == 0
