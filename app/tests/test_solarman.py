import pytest
import struct
import time
import asyncio
import logging
from math import isclose
from app.src.gen3plus.solarman_v5 import SolarmanV5
from app.src.config import Config
from app.src.infos import Infos, Register
from app.src.modbus import Modbus
from app.src.messages import State


pytest_plugins = ('pytest_asyncio',)

# initialize the proxy statistics
Infos.static_init()

timestamp = int(time.time())  # 1712861197
heartbeat = 60         

class Writer():
    def __init__(self):
        self.sent_pdu = b''

    def write(self, pdu: bytearray):
        self.sent_pdu = pdu


class Mqtt():
    def __init__(self):
        self.key = ''
        self.data = ''

    async def publish(self, key, data):
        self.key = key
        self.data = data


class MemoryStream(SolarmanV5):
    def __init__(self, msg, chunks = (0,), server_side: bool = True):
        super().__init__(server_side, client_mode=False)
        if server_side:
            self.mb.timeout = 0.4   # overwrite for faster testing
        self.mb_first_timeout = 0.5
        self.mb_timeout = 0.5
        self.writer = Writer()
        self.mqtt = Mqtt()
        self.__msg = msg
        self.__msg_len = len(msg)
        self.__chunks = chunks
        self.__offs = 0
        self.__chunk_idx = 0
        self.msg_count = 0
        self.addr = 'Test: SrvSide'
        self.db.stat['proxy']['Invalid_Msg_Format'] = 0
        self.db.stat['proxy']['AT_Command'] = 0
        self.db.stat['proxy']['AT_Command_Blocked'] = 0
        self.test_exception_async_write = False
        self.entity_prfx = ''
        self.at_acl = {'mqtt': {'allow': ['AT+'], 'block': ['AT+WEBU']}, 'tsun': {'allow': ['AT+Z', 'AT+UPURL', 'AT+SUPDATE', 'AT+TIME'], 'block': ['AT+WEBU']}}
        self.key = ''
        self.data = ''
        self.msg_recvd = []

    def _timestamp(self):
        return timestamp
    
    def _heartbeat(self) -> int:
        return heartbeat

    def append_msg(self, msg):
        self.__msg += msg
        self.__msg_len += len(msg)    
        self.__chunk_idx = 0

    def publish_mqtt(self, key, data):
        self.key = key
        self.data = data

    def _read(self) -> int:
        copied_bytes = 0
        try:    
            if (self.__offs < self.__msg_len):
                chunk_len = self.__chunks[self.__chunk_idx]
                self.__chunk_idx += 1
                if chunk_len!=0:
                    self._recv_buffer += self.__msg[self.__offs:chunk_len]
                    copied_bytes = chunk_len - self.__offs
                    self.__offs = chunk_len
                else:
                    self._recv_buffer += self.__msg[self.__offs:]
                    copied_bytes = self.__msg_len - self.__offs
                    self.__offs = self.__msg_len
        except Exception:
            pass   # ignore exceptions here
        return copied_bytes
    
    async def async_write(self, headline=''):
        if self.test_exception_async_write:
            raise RuntimeError("Peer closed.")

    def createClientStream(self, msg, chunks = (0,)):
        c = MemoryStream(msg, chunks, False)
        self.remote_stream = c
        c. remote_stream = self
        return c

    def _SolarmanV5__flush_recv_msg(self) -> None:
        self.msg_recvd.append(
            {
                'control': self.control,
                'seq': str(self.seq),
                'data_len': self.data_len
            }
        )
        super()._SolarmanV5__flush_recv_msg()
        self.msg_count += 1


def get_sn() -> bytes:
    return b'\x21\x43\x65\x7b'

def get_sn_int() -> int:
    return 2070233889

def get_inv_no() -> bytes:
    return b'T170000000000001'

def get_invalid_sn():
    return b'R170000000000002'

def total():
    ts = timestamp
    # convert int to little-endian bytes
    return struct.pack('<L',ts)

def hb():
    hb = heartbeat
    # convert int to little-endian bytes
    return struct.pack('<L',hb)

def correct_checksum(buf):
    checksum = sum(buf[1:]) & 0xff
    return checksum.to_bytes(length=1)

def incorrect_checksum(buf):
    checksum = (sum(buf[1:])+1) & 0xff
    return checksum.to_bytes(length=1)

@pytest.fixture
def device_ind_msg(): # 0x4110
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
def device_rsp_msg():  # 0x1110
    msg  = b'\xa5\x0a\x00\x10\x11\x01\x01' +get_sn()  +b'\x02\x01'
    msg += total()  
    msg += hb()
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def invalid_start_byte(): # 0x4110
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
def invalid_stop_byte(): # 0x4110
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
def invalid_checksum(): # 0x4110
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
def inverter_ind_msg():  # 0x4210
    msg  = b'\xa5\x99\x01\x10\x42\x01\x02' +get_sn()  +b'\x01\xb0\x02\xbc\xc8'
    msg += b'\x24\x32\x6c\x1f\x00\x00\xa0\x47\xe4\x33\x01\x00\x03\x08\x00\x00'
    msg += b'\x59\x31\x37\x45\x37\x41\x30\x46\x30\x31\x30\x42\x30\x31\x33\x45'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x01\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x40\x10\x08\xc8\x00\x49\x13\x8d\x00\x36\x00\x00\x02\x58\x06\x7a'
    msg += b'\x01\x61\x00\xa8\x02\x54\x01\x5a\x00\x8a\x01\xe4\x01\x5a\x00\xbd'
    msg += b'\x02\x8f\x00\x11\x00\x01\x00\x00\x00\x0b\x00\x00\x27\x98\x00\x04'
    msg += b'\x00\x00\x0c\x04\x00\x03\x00\x00\x0a\xe7\x00\x05\x00\x00\x0c\x75'
    msg += b'\x00\x00\x00\x00\x06\x16\x02\x00\x00\x00\x55\xaa\x00\x01\x00\x00'
    msg += b'\x00\x00\x00\x00\xff\xff\x07\xd0\x00\x03\x04\x00\x04\x00\x04\x00'
    msg += b'\x04\x00\x00\x01\xff\xff\x00\x01\x00\x06\x00\x68\x00\x68\x05\x00'
    msg += b'\x09\xcd\x07\xb6\x13\x9c\x13\x24\x00\x01\x07\xae\x04\x0f\x00\x41'
    msg += b'\x00\x0f\x0a\x64\x0a\x64\x00\x06\x00\x06\x09\xf6\x12\x8c\x12\x8c'
    msg += b'\x00\x10\x00\x10\x14\x52\x14\x52\x00\x10\x00\x10\x01\x51\x00\x05'
    msg += b'\x04\x00\x00\x01\x13\x9c\x0f\xa0\x00\x4e\x00\x66\x03\xe8\x04\x00'
    msg += b'\x09\xce\x07\xa8\x13\x9c\x13\x26\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x04\x00\x04\x00\x00\x00\x00\x00\xff\xff\x00\x00'
    msg += b'\x00\x00\x00\x00'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def inverter_ind_msg1600():  # 0x4210 rated Power 1600W 
    msg  = b'\xa5\x99\x01\x10\x42\xe6\x9e' +get_sn()  +b'\x01\xb0\x02\xbc\xc8'
    msg += b'\x24\x32\x6c\x1f\x00\x00\xa0\x47\xe4\x33\x01\x00\x03\x08\x00\x00'
    msg += b'\x59\x31\x37\x45\x37\x41\x30\x46\x30\x31\x30\x42\x30\x31\x33\x45'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x01\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg +=  b'\x40\x10\x08\xc8\x00\x49\x13\x8d\x00\x36\x00\x00\x06\x40\x06\x7a'
    msg += b'\x01\x61\x00\xa8\x02\x54\x01\x5a\x00\x8a\x01\xe4\x01\x5a\x00\xbd'
    msg += b'\x02\x8f\x00\x11\x00\x01\x00\x00\x00\x0b\x00\x00\x27\x98\x00\x04'
    msg += b'\x00\x00\x0c\x04\x00\x03\x00\x00\x0a\xe7\x00\x05\x00\x00\x0c\x75'
    msg += b'\x00\x00\x00\x00\x06\x16\x02\x00\x00\x00\x55\xaa\x00\x01\x00\x00'
    msg +=  b'\x00\x00\x00\x00\xff\xff\x06\x40\x00\x03\x04\x00\x04\x00\x04\x00'
    msg += b'\x04\x00\x00\x01\xff\xff\x00\x01\x00\x06\x00\x68\x00\x68\x05\x00'
    msg += b'\x09\xcd\x07\xb6\x13\x9c\x13\x24\x00\x01\x07\xae\x04\x0f\x00\x41'
    msg += b'\x00\x0f\x0a\x64\x0a\x64\x00\x06\x00\x06\x09\xf6\x12\x8c\x12\x8c'
    msg += b'\x00\x10\x00\x10\x14\x52\x14\x52\x00\x10\x00\x10\x01\x51\x00\x05'
    msg += b'\x04\x00\x00\x01\x13\x9c\x0f\xa0\x00\x4e\x00\x66\x03\xe8\x04\x00'
    msg += b'\x09\xce\x07\xa8\x13\x9c\x13\x26\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x04\x00\x04\x00\x00\x00\x00\x00\xff\xff\x00\x00'
    msg += b'\x00\x00\x00\x00'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def inverter_ind_msg1800():  # 0x4210 rated Power 1800W 
    msg  = b'\xa5\x99\x01\x10\x42\xe6\x9e' +get_sn()  +b'\x01\xb0\x02\xbc\xc8'
    msg += b'\x24\x32\x6c\x1f\x00\x00\xa0\x47\xe4\x33\x01\x00\x03\x08\x00\x00'
    msg += b'\x59\x31\x37\x45\x37\x41\x30\x46\x30\x31\x30\x42\x30\x31\x33\x45'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x01\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg +=  b'\x40\x10\x08\xc8\x00\x49\x13\x8d\x00\x36\x00\x00\x07\x08\x06\x7a'
    msg += b'\x01\x61\x00\xa8\x02\x54\x01\x5a\x00\x8a\x01\xe4\x01\x5a\x00\xbd'
    msg += b'\x02\x8f\x00\x11\x00\x01\x00\x00\x00\x0b\x00\x00\x27\x98\x00\x04'
    msg += b'\x00\x00\x0c\x04\x00\x03\x00\x00\x0a\xe7\x00\x05\x00\x00\x0c\x75'
    msg += b'\x00\x00\x00\x00\x06\x16\x02\x00\x00\x00\x55\xaa\x00\x01\x00\x00'
    msg +=  b'\x00\x00\x00\x00\xff\xff\x07\x08\x00\x03\x04\x00\x04\x00\x04\x00'
    msg += b'\x04\x00\x00\x01\xff\xff\x00\x01\x00\x06\x00\x68\x00\x68\x05\x00'
    msg += b'\x09\xcd\x07\xb6\x13\x9c\x13\x24\x00\x01\x07\xae\x04\x0f\x00\x41'
    msg += b'\x00\x0f\x0a\x64\x0a\x64\x00\x06\x00\x06\x09\xf6\x12\x8c\x12\x8c'
    msg += b'\x00\x10\x00\x10\x14\x52\x14\x52\x00\x10\x00\x10\x01\x51\x00\x05'
    msg += b'\x04\x00\x00\x01\x13\x9c\x0f\xa0\x00\x4e\x00\x66\x03\xe8\x04\x00'
    msg += b'\x09\xce\x07\xa8\x13\x9c\x13\x26\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x04\x00\x04\x00\x00\x00\x00\x00\xff\xff\x00\x00'
    msg += b'\x00\x00\x00\x00'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def inverter_ind_msg2000():  # 0x4210 rated Power 2000W 
    msg  = b'\xa5\x99\x01\x10\x42\xe6\x9e' +get_sn()  +b'\x01\xb0\x02\xbc\xc8'
    msg += b'\x24\x32\x6c\x1f\x00\x00\xa0\x47\xe4\x33\x01\x00\x03\x08\x00\x00'
    msg += b'\x59\x31\x37\x45\x37\x41\x30\x46\x30\x31\x30\x42\x30\x31\x33\x45'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x01\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg +=  b'\x40\x10\x08\xc8\x00\x49\x13\x8d\x00\x36\x00\x00\x07\xd0\x06\x7a'
    msg += b'\x01\x61\x00\xa8\x02\x54\x01\x5a\x00\x8a\x01\xe4\x01\x5a\x00\xbd'
    msg += b'\x02\x8f\x00\x11\x00\x01\x00\x00\x00\x0b\x00\x00\x27\x98\x00\x04'
    msg += b'\x00\x00\x0c\x04\x00\x03\x00\x00\x0a\xe7\x00\x05\x00\x00\x0c\x75'
    msg += b'\x00\x00\x00\x00\x06\x16\x02\x00\x00\x00\x55\xaa\x00\x01\x00\x00'
    msg += b'\x00\x00\x00\x00\xff\xff\x07\xd0\x00\x03\x04\x00\x04\x00\x04\x00'
    msg += b'\x04\x00\x00\x01\xff\xff\x00\x01\x00\x06\x00\x68\x00\x68\x05\x00'
    msg += b'\x09\xcd\x07\xb6\x13\x9c\x13\x24\x00\x01\x07\xae\x04\x0f\x00\x41'
    msg += b'\x00\x0f\x0a\x64\x0a\x64\x00\x06\x00\x06\x09\xf6\x12\x8c\x12\x8c'
    msg += b'\x00\x10\x00\x10\x14\x52\x14\x52\x00\x10\x00\x10\x01\x51\x00\x05'
    msg += b'\x04\x00\x00\x01\x13\x9c\x0f\xa0\x00\x4e\x00\x66\x03\xe8\x04\x00'
    msg += b'\x09\xce\x07\xa8\x13\x9c\x13\x26\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x04\x00\x04\x00\x00\x00\x00\x00\xff\xff\x00\x00'
    msg += b'\x00\x00\x00\x00'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def inverter_ind_msg800():  # 0x4210 rated Power 800W 
    msg  = b'\xa5\x99\x01\x10\x42\xe6\x9e' +get_sn()  +b'\x01\xb0\x02\xbc\xc8'
    msg += b'\x24\x32\x6c\x1f\x00\x00\xa0\x47\xe4\x33\x01\x00\x03\x08\x00\x00'
    msg += b'\x59\x31\x37\x45\x37\x41\x30\x46\x30\x31\x30\x42\x30\x31\x33\x45'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x01\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg +=  b'\x40\x10\x08\xc8\x00\x49\x13\x8d\x00\x36\x00\x00\x03\x20\x06\x7a'
    msg += b'\x01\x61\x00\xa8\x02\x54\x01\x5a\x00\x8a\x01\xe4\x01\x5a\x00\xbd'
    msg += b'\x02\x8f\x00\x11\x00\x01\x00\x00\x00\x0b\x00\x00\x27\x98\x00\x04'
    msg += b'\x00\x00\x0c\x04\x00\x03\x00\x00\x0a\xe7\x00\x05\x00\x00\x0c\x75'
    msg += b'\x00\x00\x00\x00\x06\x16\x02\x00\x00\x00\x55\xaa\x00\x01\x00\x00'
    msg += b'\x00\x00\x00\x00\xff\xff\x03\x20\x00\x03\x04\x00\x04\x00\x04\x00'
    msg += b'\x04\x00\x00\x01\xff\xff\x00\x01\x00\x06\x00\x68\x00\x68\x05\x00'
    msg += b'\x09\xcd\x07\xb6\x13\x9c\x13\x24\x00\x01\x07\xae\x04\x0f\x00\x41'
    msg += b'\x00\x0f\x0a\x64\x0a\x64\x00\x06\x00\x06\x09\xf6\x12\x8c\x12\x8c'
    msg += b'\x00\x10\x00\x10\x14\x52\x14\x52\x00\x10\x00\x10\x01\x51\x00\x05'
    msg += b'\x04\x00\x00\x01\x13\x9c\x0f\xa0\x00\x4e\x00\x66\x03\xe8\x04\x00'
    msg += b'\x09\xce\x07\xa8\x13\x9c\x13\x26\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x04\x00\x04\x00\x00\x00\x00\x00\xff\xff\x00\x00'
    msg += b'\x00\x00\x00\x00'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def inverter_ind_msg_81():  # 0x4210 fcode 0x81
    msg  = b'\xa5\x99\x01\x10\x42\x02\x03' +get_sn()  +b'\x81\xb0\x02\xbc\xc8'
    msg += b'\x24\x32\x6c\x1f\x00\x00\xa0\x07\x04\x03\x01\x00\x03\x08\x00\x00'
    msg += b'\x59\x31\x37\x45\x37\x41\x30\x46\x30\x31\x30\x42\x30\x31\x33\x45'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x01\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x40\x10\x08\xc8\x00\x49\x13\x8d\x00\x36\x00\x00\x02\x58\x06\x7a'
    msg += b'\x01\x61\x00\xa8\x02\x54\x01\x5a\x00\x8a\x01\xe4\x01\x5a\x00\xbd'
    msg += b'\x02\x8f\x00\x11\x00\x01\x00\x00\x00\x0b\x00\x00\x27\x98\x00\x04'
    msg += b'\x00\x00\x0c\x04\x00\x03\x00\x00\x0a\xe7\x00\x05\x00\x00\x0c\x75'
    msg += b'\x00\x00\x00\x00\x06\x16\x02\x00\x00\x00\x55\xaa\x00\x01\x00\x00'
    msg += b'\x00\x00\x00\x00\xff\xff\x07\xd0\x00\x03\x04\x00\x04\x00\x04\x00'
    msg += b'\x04\x00\x00\x01\xff\xff\x00\x01\x00\x06\x00\x68\x00\x68\x05\x00'
    msg += b'\x09\xcd\x07\xb6\x13\x9c\x13\x24\x00\x01\x07\xae\x04\x0f\x00\x41'
    msg += b'\x00\x0f\x0a\x64\x0a\x64\x00\x06\x00\x06\x09\xf6\x12\x8c\x12\x8c'
    msg += b'\x00\x10\x00\x10\x14\x52\x14\x52\x00\x10\x00\x10\x01\x51\x00\x05'
    msg += b'\x04\x00\x00\x01\x13\x9c\x0f\xa0\x00\x4e\x00\x66\x03\xe8\x04\x00'
    msg += b'\x09\xce\x07\xa8\x13\x9c\x13\x26\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x04\x00\x04\x00\x00\x00\x00\x00\xff\xff\x00\x00'
    msg += b'\x00\x00\x00\x00'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def inverter_rsp_msg():  # 0x1210
    msg  = b'\xa5\x0a\x00\x10\x12\x02\02' +get_sn()  +b'\x01\x01'
    msg += total()  
    msg += hb()
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def inverter_rsp_msg_81():  # 0x1210 fcode 0x81
    msg  = b'\xa5\x0a\x00\x10\x12\x03\03' +get_sn()  +b'\x81\x01'
    msg += total()  
    msg += hb()
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def unknown_msg():  # 0x5110
    msg  = b'\xa5\x0a\x00\x10\x51\x10\x84' +get_sn()  +b'\x01\x01\x69\x6f\x09'
    msg += b'\x66\x78\x00\x00\x00'               
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def sync_start_ind_msg():  # 0x4310
    msg  = b'\xa5\x2f\x00\x10\x43\x0c\x0d' +get_sn()  +b'\x81\x7a\x0b\x2e\x32'
    msg += b'\x39\x00\x00\x00\x00\x00\x00\x00\x0c\x00\x41\x6c\x6c\x69\x75\x73'
    msg += b'\x2d\x48\x6f\x6d\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x61\x01'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def sync_start_rsp_msg():  # 0x1310
    msg  = b'\xa5\x0a\x00\x10\x13\x0d\x0d' +get_sn()  +b'\x81\x01'
    msg += total()  
    msg += hb()
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def sync_start_fwd_msg():  # 0x4310
    msg  = b'\xa5\x2f\x00\x10\x43\x0d\x0e' +get_sn()  +b'\x81\x7a\x0b\x2e\x32'
    msg += b'\x39\x00\x00\x00\x00\x00\x00\x00\x0c\x00\x41\x6c\x6c\x69\x75\x73'
    msg += b'\x2d\x48\x6f\x6d\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x61\x01'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg


@pytest.fixture
def at_command_ind_msg():  # 0x4510
    msg  = b'\xa5\x27\x00\x10\x45\x03\x02' +get_sn() +b'\x01\x02\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'           
    msg += b'AT+TIME=214028,1,60,120\r'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def at_command_ind_msg_block():  # 0x4510
    msg  = b'\xa5\x17\x00\x10\x45\x03\x02' +get_sn() +b'\x01\x02\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'           
    msg += b'AT+WEBU\r'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def at_command_rsp_msg():  # 0x1510
    msg  = b'\xa5\x11\x00\x10\x15\x03\x03' +get_sn()  +b'\x01\x01'
    msg += total()  
    msg += hb()
    msg += b'\x00\x00\x00\x00+ok'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def heartbeat_ind_msg():  # 0x4710
    msg  = b'\xa5\x01\x00\x10\x47\x10\x84' +get_sn()
    msg += b'\x00'               
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def heartbeat_rsp_msg():  # 0x1710
    msg  = b'\xa5\x0a\x00\x10\x17\x11\x84' +get_sn()  +b'\x00\x01'
    msg += total()  
    msg += hb()
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def sync_end_ind_msg():  # 0x4810
    msg  = b'\xa5\x3c\x00\x10\x48\x06\x07' +get_sn() +b'\x01\xa5\x3c\x2e\x32'
    msg += b'\x2c\x00\x00\x00\xc1\x01\xec\x33\x01\x05\x2c\xff\xff\xff\xff\xff'
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg += b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg += b'\xff\xff\xff\xff\xff\xff\xff'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def sync_end_rsp_msg():  # 0x1810
    msg  = b'\xa5\x0a\x00\x10\x18\x07\x07' +get_sn()  +b'\x01\x01'
    msg += total()  
    msg += hb()
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def msg_modbus_cmd():
    msg  = b'\xa5\x17\x00\x10\x45\x03\x02' +get_sn()  +b'\x02\xb0\x02'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x06\x20\x08'
    msg += b'\x00\x00\x03\xc8'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def msg_modbus_cmd_fwd():
    msg  = b'\xa5\x17\x00\x10\x45\x01\x00' +get_sn()  +b'\x02\xb0\x02'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x06\x20\x08'
    msg += b'\x00\x00\x03\xc8'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def msg_modbus_cmd_crc_err():
    msg  = b'\xa5\x17\x00\x10\x45\x03\x02' +get_sn()  +b'\x02\xb0\x02'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x06\x20\x08'
    msg += b'\x00\x00\x04\xc8'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def msg_modbus_rsp():  # 0x1510
    msg  = b'\xa5\x3b\x00\x10\x15\x03\x03' +get_sn()  +b'\x02\x01'
    msg += total()  
    msg += hb()
    msg += b'\x0a\xe2\xfa\x33\x01\x03\x28\x40\x10\x08\xd8'
    msg += b'\x00\x00\x13\x87\x00\x31\x00\x68\x02\x58\x00\x00\x01\x53\x00\x02'
    msg += b'\x00\x00\x01\x52\x00\x02\x00\x00\x01\x53\x00\x03\x00\x00\x00\x04'
    msg += b'\x00\x01\x00\x00\x6c\x68'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def msg_modbus_invalid():  # 0x1510
    msg  = b'\xa5\x3b\x00\x10\x15\x03\x03' +get_sn()  +b'\x02\x00'
    msg += total()  
    msg += hb()
    msg += b'\x0a\xe2\xfa\x33\x01\x03\x28\x40\x10\x08\xd8'
    msg += b'\x00\x00\x13\x87\x00\x31\x00\x68\x02\x58\x00\x00\x01\x53\x00\x02'
    msg += b'\x00\x00\x01\x52\x00\x02\x00\x00\x01\x53\x00\x03\x00\x00\x00\x04'
    msg += b'\x00\x01\x00\x00\x6c\x68'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def msg_unknown_cmd():
    msg  = b'\xa5\x17\x00\x10\x45\x03\x02' +get_sn()  +b'\x03\xb0\x02'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x06\x20\x08'
    msg += b'\x00\x00\x03\xc8'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def msg_unknown_cmd_rsp():  # 0x1510
    msg  = b'\xa5\x3b\x00\x10\x15\x03\x03' +get_sn()  +b'\x03\x01'
    msg += total()  
    msg += hb()
    msg += b'\x0a\xe2\xfa\x33\x01\x03\x28\x40\x10\x08\xd8'
    msg += b'\x00\x00\x13\x87\x00\x31\x00\x68\x02\x58\x00\x00\x01\x53\x00\x02'
    msg += b'\x00\x00\x01\x52\x00\x02\x00\x00\x01\x53\x00\x03\x00\x00\x00\x04'
    msg += b'\x00\x01\x00\x00\x6c\x68'
    msg += correct_checksum(msg)
    msg += b'\x15'
    return msg

@pytest.fixture
def config_tsun_allow_all():
    Config.act_config = {'solarman':{'enabled': True}, 'inverters':{'allow_all':True}}

@pytest.fixture
def config_no_tsun_inv1():
    Config.act_config = {'solarman':{'enabled': False},'inverters':{'Y170000000000001':{'monitor_sn': 2070233889, 'node_id':'inv1', 'modbus_polling': True, 'suggested_area':'roof'}}}

@pytest.fixture
def config_tsun_inv1():
    Config.act_config = {'solarman':{'enabled': True},'inverters':{'Y170000000000001':{'monitor_sn': 2070233889, 'node_id':'inv1', 'modbus_polling': True, 'suggested_area':'roof'}}}

def test_read_message(device_ind_msg):
    m = MemoryStream(device_ind_msg, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == None
    assert m.control == 0x4110
    assert str(m.seq) == '01:00'
    assert m.data_len == 0xd4
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_invalid_start_byte(invalid_start_byte, device_ind_msg):
    # received a message with wrong start byte plus an valid message
    # the complete receive buffer must be cleared to 
    # find the next valid message
    m = MemoryStream(invalid_start_byte, (0,))
    m.append_msg(device_ind_msg)
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since start byte is wrong
    assert m.msg_count == 0
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == 0
    assert m.control == 0x4110
    assert str(m.seq) == '01:00'
    assert m.data_len == 0xd4
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 1
    m.close()

def test_invalid_stop_byte(invalid_stop_byte):
    # received a message with wrong stop byte
    # the complete receive buffer must be cleared to 
    # find the next valid message
    m = MemoryStream(invalid_stop_byte, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since start byte is wrong
    assert m.msg_count == 1     # msg flush was called
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == 0
    assert m.control == 0x4110
    assert str(m.seq) == '01:00'
    assert m.data_len == 0xd4
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 1
    m.close()

def test_invalid_stop_byte2(invalid_stop_byte, device_ind_msg):
    # received a message with wrong stop byte plus an valid message
    # only the first message must be discarded
    m = MemoryStream(invalid_stop_byte, (0,))
    m.append_msg(device_ind_msg)

    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 2
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.msg_recvd[0]['control']==0x4110
    assert m.msg_recvd[0]['seq']=='01:00'
    assert m.msg_recvd[0]['data_len']==0xd4
    assert m.msg_recvd[1]['control']==0x4110
    assert m.msg_recvd[1]['seq']=='01:00'
    assert m.msg_recvd[1]['data_len']==0xd4

    assert m.unique_id == None
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 1
    m.close()

def test_invalid_stop_start_byte(invalid_stop_byte, invalid_start_byte):
    # received a message with wrong stop byte plus an invalid message
    # with fron start byte
    # the complete receive buffer must be cleared to 
    # find the next valid message
    m = MemoryStream(invalid_stop_byte, (0,))
    m.append_msg(invalid_start_byte)
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since start byte is wrong
    assert m.msg_count == 1     # msg flush was called
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == 0
    assert m.control == 0x4110
    assert str(m.seq) == '01:00'
    assert m.data_len == 0xd4
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 1
    m.close()

def test_invalid_checksum(invalid_checksum, device_ind_msg):
    # received a message with wrong checksum plus an valid message
    # only the first message must be discarded
    m = MemoryStream(invalid_checksum, (0,))
    m.append_msg(device_ind_msg)

    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 2
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == None
    assert m.msg_recvd[0]['control']==0x4110
    assert m.msg_recvd[0]['seq']=='01:00'
    assert m.msg_recvd[0]['data_len']==0xd4
    assert m.msg_recvd[1]['control']==0x4110
    assert m.msg_recvd[1]['seq']=='01:00'
    assert m.msg_recvd[1]['data_len']==0xd4
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 1
    m.close()

def test_read_message_twice(config_no_tsun_inv1, device_ind_msg, device_rsp_msg):
    config_no_tsun_inv1
    m = MemoryStream(device_ind_msg, (0,))
    m.append_msg(device_ind_msg)
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 2
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == '2070233889'
    assert m.msg_recvd[0]['control']==0x4110
    assert m.msg_recvd[0]['seq']=='01:01'
    assert m.msg_recvd[0]['data_len']==0xd4
    assert m.msg_recvd[1]['control']==0x4110
    assert m.msg_recvd[1]['seq']=='01:01'
    assert m.msg_recvd[1]['data_len']==0xd4
    assert m._send_buffer==device_rsp_msg+device_rsp_msg
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_read_message_in_chunks(device_ind_msg):
    m = MemoryStream(device_ind_msg, (4,11,0))
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
    assert str(m.seq) == '01:00'
    assert m.data_len == 0xd4
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.read()    # read rest of message
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_read_message_in_chunks2(config_tsun_inv1, device_ind_msg):
    config_tsun_inv1
    m = MemoryStream(device_ind_msg, (4,10,0))
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
    assert str(m.seq) == '01:01'
    assert m.data_len == 0xd4
    assert m.msg_count == 1
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.read()        # read rest of message
    assert m.msg_count == 1
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_read_two_messages(config_tsun_allow_all, device_ind_msg, device_rsp_msg, inverter_ind_msg, inverter_rsp_msg):
    config_tsun_allow_all
    m = MemoryStream(device_ind_msg, (0,))
    m.append_msg(inverter_ind_msg)

    m._init_new_client_conn()
    m.read()         # read complete msg, and dispatch msg
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 2
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == '2070233889'
    assert m.msg_recvd[0]['control']==0x4110
    assert m.msg_recvd[0]['seq']=='01:01'
    assert m.msg_recvd[0]['data_len']==0xd4
    assert m.msg_recvd[1]['control']==0x4210
    assert m.msg_recvd[1]['seq']=='02:02'
    assert m.msg_recvd[1]['data_len']==0x199
    assert m._forward_buffer==device_ind_msg+inverter_ind_msg
    assert m._send_buffer==device_rsp_msg+inverter_rsp_msg

    m._send_buffer = bytearray(0) # clear send buffer for next test    
    m._init_new_client_conn()
    assert m._send_buffer==b''
    m.close()

def test_read_two_messages2(config_tsun_allow_all, inverter_ind_msg, inverter_ind_msg_81, inverter_rsp_msg, inverter_rsp_msg_81):
    config_tsun_allow_all
    m = MemoryStream(inverter_ind_msg, (0,))
    m.append_msg(inverter_ind_msg_81)
    m.read()         # read complete msg, and dispatch msg
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 2
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == '2070233889'
    assert m.msg_recvd[0]['control']==0x4210
    assert m.msg_recvd[0]['seq']=='02:02'
    assert m.msg_recvd[0]['data_len']==0x199
    assert m.msg_recvd[1]['control']==0x4210
    assert m.msg_recvd[1]['seq']=='03:03'
    assert m.msg_recvd[1]['data_len']==0x199
    assert m.time_ofs == 0x33e447a0
    assert m._forward_buffer==inverter_ind_msg+inverter_ind_msg_81
    assert m._send_buffer==inverter_rsp_msg+inverter_rsp_msg_81

    m._send_buffer = bytearray(0) # clear send buffer for next test    
    m._init_new_client_conn()
    assert m._send_buffer==b''
    m.close()

def test_unkown_message(config_tsun_inv1, unknown_msg):
    config_tsun_inv1
    m = MemoryStream(unknown_msg, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == '2070233889'
    assert m.control == 0x5110
    assert str(m.seq) == '84:10'
    assert m.data_len == 0x0a
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==unknown_msg
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_device_rsp(config_tsun_inv1, device_rsp_msg):
    config_tsun_inv1
    m = MemoryStream(device_rsp_msg, (0,), False)
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == '2070233889'
    assert m.control == 0x1110
    assert str(m.seq) == '01:01'
    assert m.data_len == 0x0a
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_inverter_rsp(config_tsun_inv1, inverter_rsp_msg):
    config_tsun_inv1
    m = MemoryStream(inverter_rsp_msg, (0,), False)
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == '2070233889'
    assert m.control == 0x1210
    assert str(m.seq) == '02:02'
    assert m.data_len == 0x0a
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_heartbeat_ind(config_tsun_inv1, heartbeat_ind_msg, heartbeat_rsp_msg):
    config_tsun_inv1
    m = MemoryStream(heartbeat_ind_msg, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.control == 0x4710
    assert str(m.seq) == '84:11'  # value after sending response
    assert m.data_len == 0x01
    assert m._recv_buffer==b''
    assert m._send_buffer==heartbeat_rsp_msg
    assert m._forward_buffer==heartbeat_ind_msg
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_heartbeat_ind2(config_tsun_inv1, heartbeat_ind_msg, heartbeat_rsp_msg):
    config_tsun_inv1
    m = MemoryStream(heartbeat_ind_msg, (0,))
    m.no_forwarding = True
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.control == 0x4710
    assert str(m.seq) == '84:11'  # value after sending response
    assert m.data_len == 0x01
    assert m._recv_buffer==b''
    assert m._send_buffer==heartbeat_rsp_msg
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_heartbeat_rsp(config_tsun_inv1, heartbeat_rsp_msg):
    config_tsun_inv1
    m = MemoryStream(heartbeat_rsp_msg, (0,), False)
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == '2070233889'
    assert m.control == 0x1710
    assert str(m.seq) == '11:84'  # value after sending response
    assert m.data_len == 0x0a
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_sync_start_ind(config_tsun_inv1, sync_start_ind_msg, sync_start_rsp_msg, sync_start_fwd_msg):
    config_tsun_inv1
    m = MemoryStream(sync_start_ind_msg, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.control == 0x4310
    assert str(m.seq) == '0d:0d'  # value after sending response
    assert m.data_len == 47
    assert m._recv_buffer==b''
    assert m._send_buffer==sync_start_rsp_msg
    assert m._forward_buffer==sync_start_ind_msg
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0

    m.seq.server_side = False  # simulate forawding to TSUN cloud
    m._update_header(m._forward_buffer)
    assert str(m.seq) == '0d:0e'  # value after forwarding indication
    assert m._forward_buffer==sync_start_fwd_msg

    m.close()

def test_sync_start_rsp(config_tsun_inv1, sync_start_rsp_msg):
    config_tsun_inv1
    m = MemoryStream(sync_start_rsp_msg, (0,), False)
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == '2070233889'
    assert m.control == 0x1310
    assert str(m.seq) == '0d:0d'  # value after sending response
    assert m.data_len == 0x0a
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_sync_end_ind(config_tsun_inv1, sync_end_ind_msg, sync_end_rsp_msg):
    config_tsun_inv1
    m = MemoryStream(sync_end_ind_msg, (0,))
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.control == 0x4810
    assert str(m.seq) == '07:07'  # value after sending response
    assert m.data_len == 60
    assert m._recv_buffer==b''
    assert m._send_buffer==sync_end_rsp_msg
    assert m._forward_buffer==sync_end_ind_msg
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_sync_end_rsp(config_tsun_inv1, sync_end_rsp_msg):
    config_tsun_inv1
    m = MemoryStream(sync_end_rsp_msg, (0,), False)
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.unique_id == '2070233889'
    assert m.control == 0x1810
    assert str(m.seq) == '07:07'  # value after sending response
    assert m.data_len == 0x0a
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_build_modell_600(config_tsun_allow_all, inverter_ind_msg):
    config_tsun_allow_all
    m = MemoryStream(inverter_ind_msg, (0,))
    assert 0 == m.db.get_db_value(Register.MAX_DESIGNED_POWER, 0)
    assert None == m.db.get_db_value(Register.RATED_POWER, None)
    assert None == m.db.get_db_value(Register.INVERTER_TEMP, None)
    m.read()         # read complete msg, and dispatch msg
    assert 2000 == m.db.get_db_value(Register.MAX_DESIGNED_POWER, 0)
    assert 600 == m.db.get_db_value(Register.RATED_POWER, 0)
    assert 'TSOL-MS2000(600)' == m.db.get_db_value(Register.EQUIPMENT_MODEL, 0)

    m._send_buffer = bytearray(0) # clear send buffer for next test    
    m._init_new_client_conn()
    assert m._send_buffer==b''
    m.close()

def test_build_modell_1600(config_tsun_allow_all, inverter_ind_msg1600):
    config_tsun_allow_all
    m = MemoryStream(inverter_ind_msg1600, (0,))
    assert 0 == m.db.get_db_value(Register.MAX_DESIGNED_POWER, 0)
    assert None == m.db.get_db_value(Register.RATED_POWER, None)
    assert None == m.db.get_db_value(Register.INVERTER_TEMP, None)
    m.read()         # read complete msg, and dispatch msg
    assert 1600 == m.db.get_db_value(Register.MAX_DESIGNED_POWER, 0)
    assert 1600 == m.db.get_db_value(Register.RATED_POWER, 0)
    assert 'TSOL-MS1600' == m.db.get_db_value(Register.EQUIPMENT_MODEL, 0)
    m.close()

def test_build_modell_1800(config_tsun_allow_all, inverter_ind_msg1800):
    config_tsun_allow_all
    m = MemoryStream(inverter_ind_msg1800, (0,))
    assert 0 == m.db.get_db_value(Register.MAX_DESIGNED_POWER, 0)
    assert None == m.db.get_db_value(Register.RATED_POWER, None)
    assert None == m.db.get_db_value(Register.INVERTER_TEMP, None)
    m.read()         # read complete msg, and dispatch msg
    assert 1800 == m.db.get_db_value(Register.MAX_DESIGNED_POWER, 0)
    assert 1800 == m.db.get_db_value(Register.RATED_POWER, 0)
    assert 'TSOL-MS1800' == m.db.get_db_value(Register.EQUIPMENT_MODEL, 0)
    m.close()

def test_build_modell_2000(config_tsun_allow_all, inverter_ind_msg2000):
    config_tsun_allow_all
    m = MemoryStream(inverter_ind_msg2000, (0,))
    assert 0 == m.db.get_db_value(Register.MAX_DESIGNED_POWER, 0)
    assert None == m.db.get_db_value(Register.RATED_POWER, None)
    assert None == m.db.get_db_value(Register.INVERTER_TEMP, None)
    m.read()         # read complete msg, and dispatch msg
    assert 2000 == m.db.get_db_value(Register.MAX_DESIGNED_POWER, 0)
    assert 2000 == m.db.get_db_value(Register.RATED_POWER, 0)
    assert 'TSOL-MS2000' == m.db.get_db_value(Register.EQUIPMENT_MODEL, 0)
    m.close()

def test_build_modell_800(config_tsun_allow_all, inverter_ind_msg800):
    config_tsun_allow_all
    m = MemoryStream(inverter_ind_msg800, (0,))
    assert 0 == m.db.get_db_value(Register.MAX_DESIGNED_POWER, 0)
    assert None == m.db.get_db_value(Register.RATED_POWER, None)
    assert None == m.db.get_db_value(Register.INVERTER_TEMP, None)
    m.read()         # read complete msg, and dispatch msg
    assert 800 == m.db.get_db_value(Register.MAX_DESIGNED_POWER, 0)
    assert 800 == m.db.get_db_value(Register.RATED_POWER, 0)
    assert 'TSOL-MSxx00' == m.db.get_db_value(Register.EQUIPMENT_MODEL, 0)
    m.close()

def test_build_logger_modell(config_tsun_allow_all, device_ind_msg):
    config_tsun_allow_all
    m = MemoryStream(device_ind_msg, (0,))
    assert 0 == m.db.get_db_value(Register.COLLECTOR_FW_VERSION, 0)
    assert 'IGEN TECH' == m.db.get_db_value(Register.CHIP_TYPE, None)
    assert None == m.db.get_db_value(Register.CHIP_MODEL, None)
    m.read()         # read complete msg, and dispatch msg
    assert 'LSW5BLE_17_02B0_1.05' == m.db.get_db_value(Register.CHIP_MODEL, 0)
    assert 'V1.1.00.0B' == m.db.get_db_value(Register.COLLECTOR_FW_VERSION, 0).rstrip('\00')
    m.close()

def test_msg_iterator():
    m1 = SolarmanV5(server_side=True, client_mode=False)
    m2 = SolarmanV5(server_side=True, client_mode=False)
    m3 = SolarmanV5(server_side=True, client_mode=False)
    m3.close()
    del m3
    test1 = 0
    test2 = 0
    for key in SolarmanV5:
        if key == m1:
            test1+=1
        elif key == m2:
            test2+=1
        elif type(key) != SolarmanV5:
            continue
        else:
            assert False
    assert test1 == 1
    assert test2 == 1

def test_proxy_counter():
    m = SolarmanV5(server_side=True, client_mode=False)
    assert m.new_data == {}
    m.db.stat['proxy']['Unknown_Msg'] = 0
    Infos.new_stat_data['proxy'] =  False

    m.inc_counter('Unknown_Msg')
    assert m.new_data == {}
    assert Infos.new_stat_data == {'proxy': True}
    assert 1 == m.db.stat['proxy']['Unknown_Msg']

    Infos.new_stat_data['proxy'] =  False
    m.dec_counter('Unknown_Msg')
    assert m.new_data == {}
    assert Infos.new_stat_data == {'proxy': True}
    assert 0 == m.db.stat['proxy']['Unknown_Msg']
    m.close()

@pytest.mark.asyncio
async def test_msg_build_modbus_req(config_tsun_inv1, device_ind_msg, device_rsp_msg, inverter_ind_msg, inverter_rsp_msg, msg_modbus_cmd):
    config_tsun_inv1
    m = MemoryStream(device_ind_msg, (0,), True)
    m.read()
    assert m.control == 0x4110
    assert str(m.seq) == '01:01'
    assert m._send_buffer==device_rsp_msg
    assert m._forward_buffer==device_ind_msg

    m._send_buffer = bytearray(0) # clear send buffer for next test    
    m._forward_buffer = bytearray(0) # clear send buffer for next test    
    await m.send_modbus_cmd(Modbus.WRITE_SINGLE_REG, 0x2008, 0, logging.DEBUG)
    assert 0 == m.send_msg_ofs
    assert m._forward_buffer == b''
    assert m.writer.sent_pdu == b'' # modbus command must be ignore, cause connection is still not up
    assert m._send_buffer == b''    # modbus command must be ignore, cause connection is still not up

    m.append_msg(inverter_ind_msg)
    m.read()
    assert m.control == 0x4210
    assert str(m.seq) == '02:02'
    assert m.msg_recvd[0]['control']==0x4110
    assert m.msg_recvd[0]['seq']=='01:01'
    assert m.msg_recvd[1]['control']==0x4210
    assert m.msg_recvd[1]['seq']=='02:02'
    assert m._recv_buffer==b''
    assert m._send_buffer==inverter_rsp_msg
    assert m._forward_buffer==inverter_ind_msg

    m._send_buffer = bytearray(0) # clear send buffer for next test    
    m._forward_buffer = bytearray(0) # clear send buffer for next test    
    await m.send_modbus_cmd(Modbus.WRITE_SINGLE_REG, 0x2008, 0, logging.DEBUG)
    assert 0 == m.send_msg_ofs
    assert m._forward_buffer == b''
    assert m.writer.sent_pdu == msg_modbus_cmd
    assert m._send_buffer == b''

    m._send_buffer = bytearray(0) # clear send buffer for next test    
    m.test_exception_async_write = True
    await m.send_modbus_cmd(Modbus.WRITE_SINGLE_REG, 0x2008, 0, logging.DEBUG)
    assert 0 == m.send_msg_ofs
    assert m._forward_buffer == b''
    assert m._send_buffer == b''
    m.close()

@pytest.mark.asyncio
async def test_at_cmd(config_tsun_allow_all, device_ind_msg, device_rsp_msg, inverter_ind_msg, inverter_rsp_msg, at_command_ind_msg, at_command_rsp_msg):
    config_tsun_allow_all
    m = MemoryStream(device_ind_msg, (0,), True)
    m.read()   # read device ind
    assert m.control == 0x4110
    assert str(m.seq) == '01:01'
    assert m._send_buffer==device_rsp_msg
    assert m._forward_buffer==device_ind_msg

    m._send_buffer = bytearray(0) # clear send buffer for next test    
    m._forward_buffer = bytearray(0) # clear send buffer for next test    
    await m.send_at_cmd('AT+TIME=214028,1,60,120')
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert str(m.seq) == '01:01'
    assert m.mqtt.key == ''
    assert m.mqtt.data == ""

    m.append_msg(inverter_ind_msg)
    m.read() # read inverter ind
    assert m.control == 0x4210
    assert str(m.seq) == '02:02'
    assert m._send_buffer==inverter_rsp_msg
    assert m._forward_buffer==inverter_ind_msg
    
    m._send_buffer = bytearray(0) # clear send buffer for next test    
    m._forward_buffer = bytearray(0) # clear send buffer for next test    
    await m.send_at_cmd('AT+TIME=214028,1,60,120')
    assert m._send_buffer==at_command_ind_msg
    assert m._forward_buffer==b''
    assert str(m.seq) == '02:03'
    assert m.mqtt.key == ''
    assert m.mqtt.data == ""

    m._send_buffer = bytearray(0) # clear send buffer for next test    
    m.append_msg(at_command_rsp_msg)
    m.read() # read at resp
    assert m.control == 0x1510
    assert str(m.seq) == '03:03'
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert m.key == 'at_resp'
    assert m.data == "+ok"

    m.test_exception_async_write = True
    await m.send_at_cmd('AT+TIME=214028,1,60,120')
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert str(m.seq) == '03:04'
    assert m.forward_at_cmd_resp == False
    assert m.mqtt.key == ''
    assert m.mqtt.data == ""
    m.close()

@pytest.mark.asyncio
async def test_at_cmd_blocked(config_tsun_allow_all, device_ind_msg, device_rsp_msg, inverter_ind_msg, inverter_rsp_msg, at_command_ind_msg):
    config_tsun_allow_all
    m = MemoryStream(device_ind_msg, (0,), True)
    m.read()
    assert m.control == 0x4110
    assert str(m.seq) == '01:01'
    assert m._send_buffer==device_rsp_msg
    assert m._forward_buffer==device_ind_msg

    m._send_buffer = bytearray(0) # clear send buffer for next test    
    m._forward_buffer = bytearray(0) # clear send buffer for next test    
    await m.send_at_cmd('AT+WEBU')
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert str(m.seq) == '01:01'
    assert m.mqtt.key == ''
    assert m.mqtt.data == ""

    m.append_msg(inverter_ind_msg)
    m.read()
    assert m.control == 0x4210
    assert str(m.seq) == '02:02'
    assert m._recv_buffer==b''
    assert m._send_buffer==inverter_rsp_msg
    assert m._forward_buffer==inverter_ind_msg
    
    m._send_buffer = bytearray(0) # clear send buffer for next test    
    m._forward_buffer = bytearray(0) # clear send buffer for next test    
    await m.send_at_cmd('AT+WEBU')
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert str(m.seq) == '02:02'
    assert m.forward_at_cmd_resp == False
    assert m.mqtt.key == 'at_resp'
    assert m.mqtt.data == "'AT+WEBU' is forbidden"
    m.close()

def test_at_cmd_ind(config_tsun_inv1, at_command_ind_msg):
    config_tsun_inv1
    m = MemoryStream(at_command_ind_msg, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['AT_Command'] = 0
    m.db.stat['proxy']['AT_Command_Blocked'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.control == 0x4510
    assert str(m.seq) == '03:02'
    assert m.data_len == 39
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==at_command_ind_msg
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    assert m.db.stat['proxy']['AT_Command'] == 1
    assert m.db.stat['proxy']['AT_Command_Blocked'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_at_cmd_ind_block(config_tsun_inv1, at_command_ind_msg_block):
    config_tsun_inv1
    m = MemoryStream(at_command_ind_msg_block, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['AT_Command'] = 0
    m.db.stat['proxy']['AT_Command_Blocked'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.control == 0x4510
    assert str(m.seq) == '03:02'
    assert m.data_len == 23
    assert m._recv_buffer==b''
    assert m._send_buffer==b''
    assert m._forward_buffer==b''
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    assert m.db.stat['proxy']['AT_Command'] == 0
    assert m.db.stat['proxy']['AT_Command_Blocked'] == 1
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_msg_at_command_rsp1(config_tsun_inv1, at_command_rsp_msg):
    config_tsun_inv1
    m = MemoryStream(at_command_rsp_msg)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.forward_at_cmd_resp = True
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.control == 0x1510
    assert str(m.seq) == '03:03'
    assert m.header_len==11
    assert m.data_len==17
    assert m._forward_buffer==at_command_rsp_msg
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_msg_at_command_rsp2(config_tsun_inv1, at_command_rsp_msg):
    config_tsun_inv1
    m = MemoryStream(at_command_rsp_msg)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.forward_at_cmd_resp = False
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.control == 0x1510
    assert str(m.seq) == '03:03'
    assert m.header_len==11
    assert m.data_len==17
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_msg_modbus_req(config_tsun_inv1, msg_modbus_cmd, msg_modbus_cmd_fwd):
    config_tsun_inv1
    m = MemoryStream(b'')
    m.snr = get_sn_int()
    m.state = State.up
    c = m.createClientStream(msg_modbus_cmd)

    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['AT_Command'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.db.stat['proxy']['Invalid_Msg_Format'] = 0
    c.read()         # read complete msg, and dispatch msg
    assert not c.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert c.msg_count == 1
    assert c.control == 0x4510
    assert str(c.seq) == '03:02'
    assert c.header_len==11
    assert c.data_len==23
    assert c._forward_buffer==b''
    assert c._send_buffer==b''
    assert m.writer.sent_pdu == msg_modbus_cmd_fwd
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['AT_Command'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 1
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_msg_modbus_req2(config_tsun_inv1, msg_modbus_cmd_crc_err):
    config_tsun_inv1
    m = MemoryStream(b'')
    m.snr = get_sn_int()
    m.state = State.up
    c = m.createClientStream(msg_modbus_cmd_crc_err)

    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['AT_Command'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.db.stat['proxy']['Invalid_Msg_Format'] = 0
    c.read()         # read complete msg, and dispatch msg
    assert not c.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert c.msg_count == 1
    assert c.control == 0x4510
    assert str(c.seq) == '03:02'
    assert c.header_len==11
    assert c.data_len==23
    assert c._forward_buffer==b''
    assert c._send_buffer==b''
    assert m.writer.sent_pdu==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['AT_Command'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 1
    m.close()

def test_msg_unknown_cmd_req(config_tsun_inv1, msg_unknown_cmd):
    config_tsun_inv1
    m = MemoryStream(msg_unknown_cmd, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['AT_Command'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.db.stat['proxy']['Invalid_Msg_Format'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.control == 0x4510
    assert str(m.seq) == '03:02'
    assert m.header_len==11
    assert m.data_len==23
    assert m._forward_buffer==msg_unknown_cmd
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['AT_Command'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0
    m.close()

def test_msg_modbus_rsp1(config_tsun_inv1, msg_modbus_rsp):
    '''Modbus response without a valid Modbus request must be dropped'''
    config_tsun_inv1
    m = MemoryStream(msg_modbus_rsp)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.control == 0x1510
    assert str(m.seq) == '03:03'
    assert m.header_len==11
    assert m.data_len==59
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_msg_modbus_rsp2(config_tsun_inv1, msg_modbus_rsp):
    '''Modbus response with a valid Modbus request must be forwarded'''
    config_tsun_inv1  # setup config structure
    m = MemoryStream(msg_modbus_rsp)

    m.mb.rsp_handler = m._SolarmanV5__forward_msg
    m.mb.last_addr = 1
    m.mb.last_fcode = 3
    m.mb.last_len = 20
    m.mb.last_reg = 0x3008
    m.mb.req_pend = True
    m.mb.err = 0
    m.new_data['inverter'] = False

    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.mb.err == 0
    assert m.msg_count == 1
    assert m._forward_buffer==msg_modbus_rsp
    assert m._send_buffer==b''
    assert m.db.get_db_value(Register.VERSION) == 'V4.0.10'
    assert m.new_data['inverter'] == True
    m.new_data['inverter'] = False

    m.mb.req_pend = True
    m._forward_buffer = bytearray()
    m.append_msg(msg_modbus_rsp)
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.mb.err == 0
    assert m.msg_count == 2
    assert m._forward_buffer==msg_modbus_rsp
    assert m._send_buffer==b''
    assert m.db.get_db_value(Register.VERSION) == 'V4.0.10'
    assert m.new_data['inverter'] == False

    m.close()

def test_msg_modbus_rsp3(config_tsun_inv1, msg_modbus_rsp):
    '''Modbus response with a valid Modbus request must be forwarded'''
    config_tsun_inv1
    m = MemoryStream(msg_modbus_rsp)

    m.mb.rsp_handler = m._SolarmanV5__forward_msg
    m.mb.last_addr = 1
    m.mb.last_fcode = 3
    m.mb.last_len = 20
    m.mb.last_reg = 0x3008
    m.mb.req_pend = True
    m.mb.err = 0
    m.new_data['inverter'] = False

    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.mb.err == 0
    assert m.msg_count == 1
    assert m._forward_buffer==msg_modbus_rsp
    assert m._send_buffer==b''
    assert m.db.get_db_value(Register.VERSION) == 'V4.0.10'
    assert m.new_data['inverter'] == True
    m.new_data['inverter'] = False

    m._forward_buffer = bytearray()
    m.append_msg(msg_modbus_rsp)
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.mb.err == 5
    assert m.msg_count == 2
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.db.get_db_value(Register.VERSION) == 'V4.0.10'
    assert m.new_data['inverter'] == False

    m.close()

def test_msg_unknown_rsp(config_tsun_inv1, msg_unknown_cmd_rsp):
    config_tsun_inv1
    m = MemoryStream(msg_unknown_cmd_rsp)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.control == 0x1510
    assert str(m.seq) == '03:03'
    assert m.header_len==11
    assert m.data_len==59
    assert m._forward_buffer==msg_unknown_cmd_rsp
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_msg_modbus_invalid(config_tsun_inv1, msg_modbus_invalid):
    config_tsun_inv1
    m = MemoryStream(msg_modbus_invalid, (0,), False)
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m._forward_buffer==b''
    assert m._send_buffer==b''
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

def test_msg_modbus_fragment(config_tsun_inv1, msg_modbus_rsp):
    config_tsun_inv1
    # receive more bytes than expected (7 bytes from the next msg)
    m = MemoryStream(msg_modbus_rsp+b'\x00\x00\x00\x45\x10\x52\x31', (0,))
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    m.db.stat['proxy']['Modbus_Command'] = 0
    m.mb.rsp_handler = m._SolarmanV5__forward_msg
    m.mb.last_addr = 1
    m.mb.last_fcode = 3
    m.mb.last_len = 20
    m.mb.last_reg = 0x3008
    m.mb.req_pend = True
    m.mb.err = 0

    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m._forward_buffer==msg_modbus_rsp
    assert m._send_buffer == b''
    assert m.mb.err == 0
    assert m.modbus_elms == 20-1  # register 0x300d is unknown, so one value can't be mapped
    assert m.db.stat['proxy']['Unknown_Ctrl'] == 0
    assert m.db.stat['proxy']['Modbus_Command'] == 0
    m.close()

@pytest.mark.asyncio
async def test_modbus_polling(config_tsun_inv1, heartbeat_ind_msg, heartbeat_rsp_msg):
    config_tsun_inv1
    assert asyncio.get_running_loop()
    m = MemoryStream(heartbeat_ind_msg, (0,))
    assert asyncio.get_running_loop() == m.mb_timer.loop
    m.db.stat['proxy']['Unknown_Ctrl'] = 0
    assert m.mb_timer.tim == None
    m.read()         # read complete msg, and dispatch msg
    assert not m.header_valid  # must be invalid, since msg was handled and buffer flushed
    assert m.msg_count == 1
    assert m.header_len==11
    assert m.snr == 2070233889
    assert m.control == 0x4710
    assert str(m.seq) == '84:11'  # value after sending response
    assert m.data_len == 0x01
    assert m._recv_buffer==b''
    assert m._send_buffer==heartbeat_rsp_msg
    assert m._forward_buffer==heartbeat_ind_msg
    assert m.db.stat['proxy']['Invalid_Msg_Format'] == 0

    m._send_buffer = bytearray(0) # clear send buffer for next test
    assert m.state == State.up
    assert isclose(m.mb_timeout, 0.5)
    assert next(m.mb_timer.exp_count) == 0
    
    await asyncio.sleep(0.5)
    assert m.writer.sent_pdu==bytearray(b'\xa5\x17\x00\x10E\x12\x84!Ce{\x02\xb0\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x03\x30\x00\x000J\xde\x86\x15')
    assert m._send_buffer==b''
    
    await asyncio.sleep(0.5)
    assert m.writer.sent_pdu==bytearray(b'\xa5\x17\x00\x10E\x13\x84!Ce{\x02\xb0\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x03\x30\x00\x000J\xde\x87\x15')
    assert m._send_buffer==b''
    m.state = State.closed
    m.writer.sent_pdu = bytearray()
    await asyncio.sleep(0.5)
    assert m.writer.sent_pdu==bytearray(b'')
    assert m._send_buffer==b''
    assert next(m.mb_timer.exp_count) == 4
    m.close()

@pytest.mark.asyncio
async def test_start_client_mode(config_tsun_inv1):
    config_tsun_inv1
    assert asyncio.get_running_loop()
    m = MemoryStream(b'')
    assert m.state == State.init
    assert m.no_forwarding == False
    assert m.mb_timer.tim == None
    assert asyncio.get_running_loop() == m.mb_timer.loop
    await m.send_start_cmd(get_sn_int(), '192.168.1.1', m.mb_first_timeout)
    assert m.writer.sent_pdu==bytearray(b'\xa5\x17\x00\x10E\x01\x00!Ce{\x02\xb0\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x030\x00\x000J\xde\xf1\x15')
    assert m.db.get_db_value(Register.IP_ADDRESS) == '192.168.1.1'
    assert isclose(m.db.get_db_value(Register.POLLING_INTERVAL), 0.5)
    assert m.db.get_db_value(Register.HEARTBEAT_INTERVAL) == 120

    assert m.state == State.up
    assert m.no_forwarding == True

    assert m._send_buffer==b''
    assert isclose(m.mb_timeout, 0.5)
    assert next(m.mb_timer.exp_count) == 0
    
    await asyncio.sleep(0.5)
    assert m.writer.sent_pdu==bytearray(b'\xa5\x17\x00\x10E\x02\x00!Ce{\x02\xb0\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x030\x00\x000J\xde\xf2\x15')
    assert m._send_buffer==b''
    
    await asyncio.sleep(0.5)
    assert m.writer.sent_pdu==bytearray(b'\xa5\x17\x00\x10E\x03\x00!Ce{\x02\xb0\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x030\x00\x000J\xde\xf3\x15')
    assert m._send_buffer==b''
    assert next(m.mb_timer.exp_count) == 3
    m.close()
