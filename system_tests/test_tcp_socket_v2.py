# test_with_pytest.py and scapy
#
import pytest, socket, time, os
from dotenv import load_dotenv

#from scapy.all import *
#from scapy.layers.inet import IP, TCP, TCP_client

load_dotenv()

SOLARMAN_SNR = os.getenv('SOLARMAN_SNR', '00000080')

def get_sn() -> bytes:
    return bytes.fromhex(SOLARMAN_SNR)

def get_inv_no() -> bytes:
    return b'T170000000000001'

def get_invalid_sn():
    return b'R170000000000002'


@pytest.fixture
def MsgContactInfo(): # Contact Info message
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

@pytest.fixture
def MsgContactResp(): # Contact Response message
    msg  = b'\xa5\x0a\x00\x10\x11\x01\x01' +get_sn()  +b'\x02\x01\x6a\xfd\x8f'
    msg += b'\x65\x3c\x00\x00\x00\x75\x15'
    return msg



@pytest.fixture(scope="session")
def ClientConnection():
    #host = '172.16.30.7'
    host = 'logger.talent-monitoring.com'
    #host = 'iot.talent-monitoring.com'
    #host = '127.0.0.1'
    port = 10000
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.settimeout(1)
        yield s
        s.close()

def checkResponse(data, Msg):
    check = bytearray(data)
    check[5]= Msg[5]            # ignore seq
    check[13:17]= Msg[13:17]    # ignore timestamp
    check[21]= Msg[21]          # ignore crc
    assert check == Msg


def tempClientConnection():
    #host = '172.16.30.7'
    host = 'logger.talent-monitoring.com'
    #host = 'iot.talent-monitoring.com'
    #host = '127.0.0.1'
    port = 10000
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.settimeout(1)
        yield s
        time.sleep(2.5)
        s.close()

def test_open_close():
    try:
        for s in tempClientConnection():
            pass
    except:
        assert False
    assert True

def test_conn_msg(ClientConnection,MsgContactInfo, MsgContactResp):
    s = ClientConnection
    try:
        s.sendall(MsgContactInfo)
        # time.sleep(2.5)
        data = s.recv(1024)
    except TimeoutError:
        pass
    # time.sleep(2.5)
    checkResponse(data, MsgContactResp)