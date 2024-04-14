# test_with_pytest.py
import pytest, json
from app.src.infos import Register, ClrAtMidnight
from app.src.gen3.infos_g3 import InfosG3

@pytest.fixture
def ContrDataSeq(): # Get Time Request message
    msg =   b'\x00\x00\x00\x15\x00\x09\x2b\xa8\x54\x10\x52\x53\x57\x5f\x34\x30\x30\x5f\x56\x31\x2e\x30\x30\x2e\x30\x36\x00\x09\x27\xc0\x54\x06\x52\x61\x79\x6d\x6f'
    msg +=  b'\x6e\x00\x09\x2f\x90\x54\x0b\x52\x53\x57\x2d\x31\x2d\x31\x30\x30\x30\x31\x00\x09\x5a\x88\x54\x0f\x74\x2e\x72\x61\x79\x6d\x6f\x6e\x69\x6f\x74\x2e\x63\x6f\x6d\x00\x09\x5a\xec\x54'
    msg +=  b'\x1c\x6c\x6f\x67\x67\x65\x72\x2e\x74\x61\x6c\x65\x6e\x74\x2d\x6d\x6f\x6e\x69\x74\x6f\x72\x69\x6e\x67\x2e\x63\x6f\x6d\x00\x0d\x00\x20\x49\x00\x00\x00\x01\x00\x0c\x35\x00\x49\x00'
    msg +=  b'\x00\x00\x64\x00\x0c\x96\xa8\x49\x00\x00\x00\x1d\x00\x0c\x7f\x38\x49\x00\x00\x00\x01\x00\x0c\xfc\x38\x49\x00\x00\x00\x01\x00\x0c\xf8\x50\x49\x00\x00\x01\x2c\x00\x0c\x63\xe0\x49'
    msg +=  b'\x00\x00\x00\x00\x00\x0c\x67\xc8\x49\x00\x00\x00\x00\x00\x0c\x50\x58\x49\x00\x00\x00\x01\x00\x09\x5e\x70\x49\x00\x00\x13\x8d\x00\x09\x5e\xd4\x49\x00\x00\x13\x8d\x00\x09\x5b\x50'
    msg +=  b'\x49\x00\x00\x00\x02\x00\x0d\x04\x08\x49\x00\x00\x00\x00\x00\x07\xa1\x84\x49\x00\x00\x00\x01\x00\x0c\x50\x59\x49\x00\x00\x00\x4c\x00\x0d\x1f\x60\x49\x00\x00\x00\x00'
    return msg

@pytest.fixture
def Contr2DataSeq(): # Get Time Request message
    msg  =  b'\x00\x00\x00\x39\x00\x09\x2b\xa8\x54\x10\x52'
    msg +=  b'\x53\x57\x5f\x34\x30\x30\x5f\x56\x31\x2e\x30\x30\x2e\x32\x30\x00'
    msg +=  b'\x09\x27\xc0\x54\x06\x52\x61\x79\x6d\x6f\x6e\x00\x09\x2f\x90\x54'
    msg +=  b'\x0b\x52\x53\x57\x2d\x31\x2d\x31\x30\x30\x30\x31\x00\x09\x5a\x88'
    msg +=  b'\x54\x0f\x74\x2e\x72\x61\x79\x6d\x6f\x6e\x69\x6f\x74\x2e\x63\x6f'
    msg +=  b'\x6d\x00\x09\x5a\xec\x54\x1c\x6c\x6f\x67\x67\x65\x72\x2e\x74\x61'
    msg +=  b'\x6c\x65\x6e\x74\x2d\x6d\x6f\x6e\x69\x74\x6f\x72\x69\x6e\x67\x2e'
    msg +=  b'\x63\x6f\x6d\x00\x0d\x2f\x00\x54\x10\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x32\xe8\x54\x10\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'
    msg +=  b'\x0d\x36\xd0\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\x00\x0d\x3a\xb8\x54\x10\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x3e\xa0\x54'
    msg +=  b'\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\x00\x0d\x42\x88\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x46\x70\x54\x10\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x4a'
    msg +=  b'\x58\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\x00\x0d\x4e\x40\x54\x10\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x52\x28\x54\x10\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'
    msg +=  b'\x0d\x56\x10\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\x00\x0d\x59\xf8\x54\x10\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x5d\xe0\x54'
    msg +=  b'\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\x00\x0d\x61\xc8\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x65\xb0\x54\x10\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x69'
    msg +=  b'\x98\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\x00\x0d\x6d\x80\x54\x10\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x71\x68\x54\x10\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'
    msg +=  b'\x0d\x75\x50\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\x00\x0d\x79\x38\x54\x10\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x7d\x20\x54'
    msg +=  b'\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\x00\x0d\x81\x08\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x84\xf0\x54\x10\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x88'
    msg +=  b'\xd8\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\x00\x0d\x8c\xc0\x54\x10\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x90\xa8\x54\x10\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'
    msg +=  b'\x0d\x94\x90\x54\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\x00\x0d\x98\x78\x54\x10\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0d\x9c\x60\x54'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    msg +=  b'\x00\x0d\x00\x20\x49\x00\x00\x00\x01\x00\x0c\x35\x00\x49\x00\x00'
    msg +=  b'\x00\x10\x00\x0c\x96\xa8\x49\x00\x00\x01\x4e\x00\x0c\x7f\x38\x49'
    msg +=  b'\x00\x00\x00\x01\x00\x0c\xfc\x38\x49\x00\x00\x00\x01\x00\x0c\xf8'
    msg +=  b'\x50\x49\x00\x00\x01\x2c\x00\x0c\x63\xe0\x49\x00\x00\x00\x00\x00'
    msg +=  b'\x0c\x67\xc8\x49\x00\x00\x00\x00\x00\x0c\x50\x58\x49\x00\x00\x00'
    msg +=  b'\x01\x00\x09\x5e\x70\x49\x00\x00\x13\x8d\x00\x09\x5e\xd4\x49\x00'
    msg +=  b'\x00\x13\x8d\x00\x09\x5b\x50\x49\x00\x00\x00\x02\x00\x0d\x04\x08'
    msg +=  b'\x49\x00\x00\x00\x00\x00\x07\xa1\x84\x49\x00\x00\x00\x01\x00\x0c'
    msg +=  b'\x50\x59\x49\x00\x00\x00\x33\x00\x0d\x1f\x60\x49\x00\x00\x00\x00'
    msg +=  b'\x00\x0d\x23\x48\x49\xff\xff\xff\xff\x00\x0d\x27\x30\x49\xff\xff'
    msg +=  b'\xff\xff\x00\x0d\x2b\x18\x4c\x00\x00\x00\x00\x00\x00\xff\xff\x00'
    msg +=  b'\x0c\xa2\x60\x49\x00\x00\x00\x00\x00\x0d\xa0\x48\x49\x00\x00\x00'
    msg +=  b'\x00\x00\x0d\xa4\x30\x49\x00\x00\x00\x00\x00\x0d\xa8\x18\x49\x00'
    msg +=  b'\x00\x00\x00'
    return msg

@pytest.fixture
def InvDataSeq(): # Data indication from the controller
    msg =   b'\x00\x00\x00\x06\x00\x00\x00\x0a\x54\x08\x4d\x69\x63\x72\x6f\x69\x6e\x76\x00\x00\x00\x14\x54\x04\x54\x53\x55\x4e\x00\x00\x00\x1E\x54\x07\x56\x35\x2e\x30\x2e\x31\x31\x00\x00\x00\x28'
    msg +=  b'\x54\x10T170000000000001\x00\x00\x00\x32\x54\x0a\x54\x53\x4f\x4c\x2d\x4d\x53\x36\x30\x30\x00\x00\x00\x3c\x54\x05\x41\x2c\x42\x2c\x43'
    return msg

@pytest.fixture
def InvalidDataSeq(): # Data indication from the controller
    msg =   b'\x00\x00\x00\x06\x00\x00\x00\x0a\x54\x08\x4d\x69\x63\x72\x6f\x69\x6e\x76\x00\x00\x00\x14\x64\x04\x54\x53\x55\x4e\x00\x00\x00\x1E\x54\x07\x56\x35\x2e\x30\x2e\x31\x31\x00\x00\x00\x28'
    msg +=  b'\x54\x10T170000000000001\x00\x00\x00\x32\x54\x0a\x54\x53\x4f\x4c\x2d\x4d\x53\x36\x30\x30\x00\x00\x00\x3c\x54\x05\x41\x2c\x42\x2c\x43'
    return msg

@pytest.fixture
def InvDataSeq2(): # Data indication from the controller
    msg =   b'\x00\x00\x00\xa3\x00\x00\x00\x64\x53\x00\x01\x00\x00\x00\xc8\x53\x00\x02\x00\x00\x01\x2c\x53\x00\x00\x00\x00\x01\x90\x49\x00\x00\x00\x00\x00\x00\x01\x91\x53\x00\x00'
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
def InvDataSeq2_Zero(): # Data indication from the controller
    msg =   b'\x00\x00\x00\xa3\x00\x00\x00\x64\x53\x00\x01\x00\x00\x00\xc8\x53\x00\x02\x00\x00\x01\x2c\x53\x00\x00\x00\x00\x01\x90\x49\x00\x00\x00\x00\x00\x00\x01\x91\x53\x00\x00'
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
    msg +=  b'\x00\x04\x4c\x46\x3e\xeb\x85\x1f\x00\x00\x04\xb0\x46\x42\x48\x14\x7b\x00\x00\x05\x14\x53\x00\x00\x00\x00\x05\x78\x53\x00\x00\x00\x00\x05\xdc\x53\x00\x00\x00\x00\x06'
    msg +=  b'\x40\x46\x42\xd3\x66\x66\x00\x00\x06\xa4\x46\x42\x06\x66\x66\x00\x00\x07\x08\x46\x3f\xf4\x7a\xe1\x00\x00\x07\x6c\x46\x00\x00\x00\x00\x00\x00\x07\xd0\x46\x42\x06\x00'
    msg +=  b'\x00\x00\x00\x08\x34\x46\x3f\xae\x14\x7b\x00\x00\x08\x98\x46\x00\x00\x00\x00\x00\x00\x08\xfc\x46\x00\x00\x00\x00\x00\x00\x09\x60\x46\x00\x00\x00\x00\x00\x00\x09\xc4'
    msg +=  b'\x46\x00\x00\x00\x00\x00\x00\x0a\x28\x46\x00\x00\x00\x00\x00\x00\x0a\x8c\x46\x00\x00\x00\x00\x00\x00\x0a\xf0\x46\x00\x00\x00\x00\x00\x00\x0b\x54\x46\x00\x00\x00\x00'
    msg +=  b'\x00\x00\x0b\xb8\x46\x00\x00\x00\x00\x00\x00\x0c\x1c\x46\x00\x00\x00\x00\x00\x00\x0c\x80\x46\x00\x00\x00\x00\x00\x00\x0c\xe4\x46\x00\x00\x00\x00\x00\x00\x0d\x48\x46'
    msg +=  b'\x00\x00\x00\x00\x00\x00\x0d\xac\x46\x00\x00\x00\x00\x00\x00\x0e\x10\x46\x00\x00\x00\x00\x00\x00\x0e\x74\x46\x00\x00\x00\x00\x00\x00\x0e\xd8\x46\x00\x00\x00\x00\x00'
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


def test_parse_control(ContrDataSeq):
    i = InfosG3()
    for key, result in i.parse (ContrDataSeq):
        pass

    assert json.dumps(i.db) == json.dumps(
{"collector": {"Collector_Fw_Version": "RSW_400_V1.00.06", "Chip_Type": "Raymon", "Chip_Model": "RSW-1-10001", "Trace_URL": "t.raymoniot.com", "Logger_URL": "logger.talent-monitoring.com"}, "controller": {"Collect_Interval": 1, "Signal_Strength": 100, "Power_On_Time": 29, "Communication_Type": 1, "Connect_Count": 1, "Data_Up_Interval": 300}})        

def test_parse_control2(Contr2DataSeq):
    i = InfosG3()
    for key, result in i.parse (Contr2DataSeq):
        pass

    assert json.dumps(i.db) == json.dumps(
{"collector": {"Collector_Fw_Version": "RSW_400_V1.00.20", "Chip_Type": "Raymon", "Chip_Model": "RSW-1-10001", "Trace_URL": "t.raymoniot.com", "Logger_URL": "logger.talent-monitoring.com"}, "controller": {"Collect_Interval": 1, "Signal_Strength": 16, "Power_On_Time": 334, "Communication_Type": 1, "Connect_Count": 1, "Data_Up_Interval": 300}})

def test_parse_inverter(InvDataSeq):
    i = InfosG3()
    for key, result in i.parse (InvDataSeq):
        pass

    assert json.dumps(i.db) == json.dumps(
{"inverter": {"Product_Name": "Microinv", "Manufacturer": "TSUN", "Version": "V5.0.11", "Serial_Number": "T170000000000001", "Equipment_Model": "TSOL-MS600"}})

def test_parse_cont_and_invert(ContrDataSeq, InvDataSeq):
    i = InfosG3()
    for key, result in i.parse (ContrDataSeq):
        pass

    for key, result in i.parse (InvDataSeq):
        pass

    assert json.dumps(i.db) == json.dumps(
    {
"collector": {"Collector_Fw_Version": "RSW_400_V1.00.06", "Chip_Type": "Raymon", "Chip_Model": "RSW-1-10001", "Trace_URL": "t.raymoniot.com", "Logger_URL": "logger.talent-monitoring.com"}, "controller": {"Collect_Interval": 1, "Signal_Strength": 100, "Power_On_Time": 29, "Communication_Type": 1, "Connect_Count": 1, "Data_Up_Interval": 300},
"inverter": {"Product_Name": "Microinv", "Manufacturer": "TSUN", "Version": "V5.0.11", "Serial_Number": "T170000000000001", "Equipment_Model": "TSOL-MS600"}})


def test_build_ha_conf1(ContrDataSeq):
    i = InfosG3()
    i.static_init()                # initialize counter

    tests = 0
    for d_json, comp, node_id, id in i.ha_confs(ha_prfx="tsun/", node_id="garagendach/", snr='123'):

        if id == 'out_power_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/grid", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "out_power_123", "val_tpl": "{{value_json['Output_Power'] | float}}", "unit_of_meas": "W", "dev": {"name": "Micro Inverter", "sa": "Micro Inverter", "via_device": "controller_123", "ids": ["inverter_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'daily_gen_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Daily Generation", "stat_t": "tsun/garagendach/total", "dev_cla": "energy", "stat_cla": "total_increasing", "uniq_id": "daily_gen_123", "val_tpl": "{{value_json['Daily_Generation'] | float}}", "unit_of_meas": "kWh", "ic": "mdi:solar-power-variant", "dev": {"name": "Micro Inverter", "sa": "Micro Inverter", "via_device": "controller_123", "ids": ["inverter_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv1_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv1_123", "val_tpl": "{{ (value_json['pv1']['Power'] | float)}}", "unit_of_meas": "W", "dev": {"name": "Module PV1", "sa": "Module PV1", "via_device": "inverter_123", "ids": ["input_pv1_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv2_123':
            assert False    # if we haven't received and parsed a control data msg, we don't know the number of inputs. In this case we only register the first one!!


        elif id == 'signal_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Signal Strength", "stat_t": "tsun/garagendach/controller", "dev_cla": None, "stat_cla": "measurement", "uniq_id": "signal_123", "val_tpl": "{{value_json[\'Signal_Strength\'] | int}}", "unit_of_meas": "%", "ic": "mdi:wifi", "dev": {"name": "Controller", "sa": "Controller", "via_device": "proxy", "ids": ["controller_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1
        elif id == 'inv_count_456':
            assert False

    assert tests==4


    for d_json, comp, node_id, id in i.ha_proxy_confs(ha_prfx="tsun/", node_id = 'proxy/', snr = '456'):

        if id == 'out_power_123':
            assert False
        elif id == 'daily_gen_123':
            assert False
        elif id == 'power_pv1_123':
            assert False
        elif id == 'power_pv2_123':
            assert False    # if we haven't received and parsed a control data msg, we don't know the number of inputs. In this case we only register the first one!!

        elif id == 'signal_123':
            assert False
        elif id == 'inv_count_456':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Active Inverter Connections", "stat_t": "tsun/proxy/proxy", "dev_cla": None, "stat_cla": None, "uniq_id": "inv_count_456", "val_tpl": "{{value_json['Inverter_Cnt'] | int}}", "ic": "mdi:counter", "dev": {"name": "Proxy", "sa": "Proxy", "mdl": "proxy", "mf": "Stefan Allius", "sw": "unknown", "ids": ["proxy"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

    assert tests==5

def test_build_ha_conf2(ContrDataSeq, InvDataSeq, InvDataSeq2):
    i = InfosG3()
    for key, result in i.parse (ContrDataSeq):
        pass
    for key, result in i.parse (InvDataSeq):
        pass
    for key, result in i.parse (InvDataSeq2):
        pass

    tests = 0
    for d_json, comp, node_id, id in i.ha_confs(ha_prfx="tsun/", node_id="garagendach/", snr='123', sug_area = 'roof'):

        if id == 'out_power_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/grid", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "out_power_123", "val_tpl": "{{value_json['Output_Power'] | float}}", "unit_of_meas": "W", "dev": {"name": "Micro Inverter - roof", "sa": "Micro Inverter - roof", "via_device": "controller_123", "mdl": "TSOL-MS600", "mf": "TSUN", "sw": "V5.0.11", "ids": ["inverter_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        if id == 'daily_gen_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Daily Generation", "stat_t": "tsun/garagendach/total", "dev_cla": "energy", "stat_cla": "total_increasing", "uniq_id": "daily_gen_123", "val_tpl": "{{value_json['Daily_Generation'] | float}}", "unit_of_meas": "kWh", "ic": "mdi:solar-power-variant", "dev": {"name": "Micro Inverter - roof", "sa": "Micro Inverter - roof", "via_device": "controller_123", "mdl": "TSOL-MS600", "mf": "TSUN", "sw": "V5.0.11", "ids": ["inverter_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv1_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv1_123", "val_tpl": "{{ (value_json['pv1']['Power'] | float)}}", "unit_of_meas": "W", "dev": {"name": "Module PV1 - roof", "sa": "Module PV1 - roof", "via_device": "inverter_123", "ids": ["input_pv1_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'power_pv2_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Power", "stat_t": "tsun/garagendach/input", "dev_cla": "power", "stat_cla": "measurement", "uniq_id": "power_pv2_123", "val_tpl": "{{ (value_json['pv2']['Power'] | float)}}", "unit_of_meas": "W", "dev": {"name": "Module PV2 - roof", "sa": "Module PV2 - roof", "via_device": "inverter_123", "ids": ["input_pv2_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1

        elif id == 'signal_123':
            assert comp == 'sensor'
            assert  d_json == json.dumps({"name": "Signal Strength", "stat_t": "tsun/garagendach/controller", "dev_cla": None, "stat_cla": "measurement", "uniq_id": "signal_123", "val_tpl": "{{value_json[\'Signal_Strength\'] | int}}", "unit_of_meas": "%", "ic": "mdi:wifi", "dev": {"name": "Controller - roof", "sa": "Controller - roof", "via_device": "proxy", "mdl": "RSW-1-10001", "mf": "Raymon", "sw": "RSW_400_V1.00.06", "ids": ["controller_123"]}, "o": {"name": "proxy", "sw": "unknown"}})
            tests +=1
    assert tests==5

def test_must_incr_total(InvDataSeq2, InvDataSeq2_Zero):
    i = InfosG3()
    tests = 0
    for key, update in i.parse (InvDataSeq2):
        if key == 'total' or key == 'inverter' or key == 'env':
            assert update == True
            tests +=1   
    assert tests==5
    assert json.dumps(i.db['total']) == json.dumps({'Daily_Generation': 1.7, 'Total_Generation': 17.36})
    assert json.dumps(i.db['input']) == json.dumps({"pv1": {"Voltage": 33.6, "Current": 1.91, "Power": 64.5, "Daily_Generation": 1.08, "Total_Generation": 9.74}, "pv2": {"Voltage": 33.5, "Current": 1.36, "Power": 45.7, "Daily_Generation": 0.62, "Total_Generation": 7.62}, "pv3": {"Voltage": 0.0, "Current": 0.0, "Power": 0.0}, "pv4": {"Voltage": 0.0, "Current": 0.0, "Power": 0.0}})
    assert json.dumps(i.db['env']) == json.dumps({"Inverter_Temp": 23})
    tests = 0
    for key, update in i.parse (InvDataSeq2):
        if key == 'total':
            assert update == False
            tests +=1   
        elif key == 'env':
            assert update == False
            tests +=1

    assert tests==3
    assert json.dumps(i.db['total']) == json.dumps({'Daily_Generation': 1.7, 'Total_Generation': 17.36})
    assert json.dumps(i.db['input']) == json.dumps({"pv1": {"Voltage": 33.6, "Current": 1.91, "Power": 64.5, "Daily_Generation": 1.08, "Total_Generation": 9.74}, "pv2": {"Voltage": 33.5, "Current": 1.36, "Power": 45.7, "Daily_Generation": 0.62, "Total_Generation": 7.62}, "pv3": {"Voltage": 0.0, "Current": 0.0, "Power": 0.0}, "pv4": {"Voltage": 0.0, "Current": 0.0, "Power": 0.0}})
    assert json.dumps(i.db['env']) == json.dumps({"Inverter_Temp": 23})
    assert json.dumps(i.db['inverter']) == json.dumps({"Rated_Power": 600, "No_Inputs": 2})
        
    tests = 0
    for key, update in i.parse (InvDataSeq2_Zero):
        if key == 'total':
            assert update == False
            tests +=1   
        elif key == 'env':
            assert update == True
            tests +=1   

    assert tests==3
    assert json.dumps(i.db['total']) == json.dumps({'Daily_Generation': 1.7, 'Total_Generation': 17.36})
    assert json.dumps(i.db['input']) == json.dumps({"pv1": {"Voltage": 33.6, "Current": 1.91, "Power": 0.0, "Daily_Generation": 1.08, "Total_Generation": 9.74}, "pv2": {"Voltage": 33.5, "Current": 1.36, "Power": 0.0, "Daily_Generation": 0.62, "Total_Generation": 7.62}, "pv3": {"Voltage": 0.0, "Current": 0.0, "Power": 0.0}, "pv4": {"Voltage": 0.0, "Current": 0.0, "Power": 0.0}})
    assert json.dumps(i.db['env']) == json.dumps({"Inverter_Temp": 0})

def test_must_incr_total2(InvDataSeq2, InvDataSeq2_Zero):
    i = InfosG3()
    tests = 0
    for key, update in i.parse (InvDataSeq2_Zero):
        if key == 'total':
            assert update == False
            tests +=1   
        elif key == 'env':
            assert update == True
            tests +=1

    assert tests==3
    assert json.dumps(i.db['total']) == json.dumps({})
    assert json.dumps(i.db['input']) == json.dumps({"pv1": {"Voltage": 33.6, "Current": 1.91, "Power": 0.0}, "pv2": {"Voltage": 33.5, "Current": 1.36, "Power": 0.0}, "pv3": {"Voltage": 0.0, "Current": 0.0, "Power": 0.0}, "pv4": {"Voltage": 0.0, "Current": 0.0, "Power": 0.0}})
    assert json.dumps(i.db['env']) == json.dumps({"Inverter_Temp": 0})
    
    tests = 0
    for key, update in i.parse (InvDataSeq2_Zero):
        if key == 'total':
            assert update == False
            tests +=1   
        elif key == 'env':
            assert update == False
            tests +=1

    assert tests==3
    assert json.dumps(i.db['total']) == json.dumps({})
    assert json.dumps(i.db['input']) == json.dumps({"pv1": {"Voltage": 33.6, "Current": 1.91, "Power": 0.0}, "pv2": {"Voltage": 33.5, "Current": 1.36, "Power": 0.0}, "pv3": {"Voltage": 0.0, "Current": 0.0, "Power": 0.0}, "pv4": {"Voltage": 0.0, "Current": 0.0, "Power": 0.0}})
    assert json.dumps(i.db['env']) == json.dumps({"Inverter_Temp": 0})

    tests = 0
    for key, update in i.parse (InvDataSeq2):
        if key == 'total':
            assert update == True
            tests +=1   
        elif key == 'env':
            assert update == True
            tests +=1

    assert tests==3
    assert json.dumps(i.db['total']) == json.dumps({'Daily_Generation': 1.7, 'Total_Generation': 17.36})
    assert json.dumps(i.db['input']) == json.dumps({"pv1": {"Voltage": 33.6, "Current": 1.91, "Power": 64.5, "Daily_Generation": 1.08, "Total_Generation": 9.74}, "pv2": {"Voltage": 33.5, "Current": 1.36, "Power": 45.7, "Daily_Generation": 0.62, "Total_Generation": 7.62}, "pv3": {"Voltage": 0.0, "Current": 0.0, "Power": 0.0}, "pv4": {"Voltage": 0.0, "Current": 0.0, "Power": 0.0}})
    assert json.dumps(i.db['env']) == json.dumps({"Inverter_Temp": 23})


def test_statistic_counter():
    i = InfosG3()
    val = i.dev_value("Test-String")
    assert val == "Test-String"

    val = i.dev_value(0xffffffff)  # invalid addr
    assert val == None
    
    val = i.dev_value(Register.INVERTER_CNT)  # valid addr but not initiliazed
    assert val == None or val == 0

    i.static_init()                # initialize counter
    assert json.dumps(i.stat) == json.dumps({"proxy": {"Inverter_Cnt": 0, "Unknown_SNR": 0, "Unknown_Msg": 0, "Invalid_Data_Type": 0, "Internal_Error": 0,"Unknown_Ctrl": 0, "OTA_Start_Msg": 0, "SW_Exception": 0, "Invalid_Msg_Format": 0, "AT_Command": 0}})
                                            
    val = i.dev_value(Register.INVERTER_CNT)  # valid and initiliazed addr
    assert val == 0

    i.inc_counter('Inverter_Cnt')
    assert json.dumps(i.stat) == json.dumps({"proxy": {"Inverter_Cnt": 1, "Unknown_SNR": 0, "Unknown_Msg": 0, "Invalid_Data_Type": 0, "Internal_Error": 0,"Unknown_Ctrl": 0, "OTA_Start_Msg": 0, "SW_Exception": 0, "Invalid_Msg_Format": 0, "AT_Command": 0}})
    val = i.dev_value(Register.INVERTER_CNT)
    assert val == 1

    i.dec_counter('Inverter_Cnt')
    val = i.dev_value(Register.INVERTER_CNT)
    assert val == 0

def test_dep_rules():
    i = InfosG3()
    i.static_init()                # initialize counter

    res = i.ignore_this_device({})
    assert res == True

    res = i.ignore_this_device({'reg':0xffffffff})
    assert res == True

    i.inc_counter('Inverter_Cnt')    # is 1
    val = i.dev_value(Register.INVERTER_CNT)
    assert val == 1
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT})
    assert res == True
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT, 'less_eq': 2})
    assert res == False
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT, 'gte': 2})
    assert res == True

    i.inc_counter('Inverter_Cnt')   # is 2
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT, 'less_eq': 2})
    assert res == False
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT, 'gte': 2})
    assert res == False

    i.inc_counter('Inverter_Cnt')   # is 3
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT, 'less_eq': 2})
    assert res == True
    res = i.ignore_this_device({'reg': Register.INVERTER_CNT, 'gte': 2})
    assert res == False

def test_table_definition():
    i = InfosG3()
    i.static_init()                # initialize counter

    val = i.dev_value(Register.INTERNAL_ERROR)  # check internal error counter
    assert val == 0

    for d_json, comp, node_id, id in i.ha_confs(ha_prfx="tsun/", node_id="garagendach/", snr='123', sug_area = 'roof'):
        pass

    for d_json, comp, node_id, id in i.ha_proxy_confs(ha_prfx="tsun/", node_id = 'proxy/', snr = '456'):
        pass

    val = i.dev_value(Register.INTERNAL_ERROR)  # check internal error counter
    assert val == 0

    # test missing 'fmt' value
    i.info_defs[Register.TEST_REG1] =  {'name':['proxy', 'Internal_Test1'],  'singleton': True, 'ha':{'dev':'proxy', 'dev_cla': None,       'stat_cla': None, 'id':'intern_test1_'}}

    tests = 0
    for d_json, comp, node_id, id in i.ha_proxy_confs(ha_prfx="tsun/", node_id = 'proxy/', snr = '456'):
        if id == 'intern_test1_456':
            tests +=1

    assert tests == 1

    val = i.dev_value(Register.INTERNAL_ERROR)  # check internal error counter
    assert val == 1

    # test missing 'dev' value
    i.info_defs[Register.TEST_REG1] =  {'name':['proxy', 'Internal_Test2'],  'singleton': True, 'ha':{'dev_cla': None,       'stat_cla': None, 'id':'intern_test2_',  'fmt':'| int'}}
    tests = 0
    for d_json, comp, node_id, id in i.ha_proxy_confs(ha_prfx="tsun/", node_id = 'proxy/', snr = '456'):
        if id == 'intern_test2_456':
            tests +=1

    assert tests == 1

    val = i.dev_value(Register.INTERNAL_ERROR)  # check internal error counter
    assert val == 2



    # test invalid 'via' value
    i.info_devs['test_dev'] = {'via':'xyz',   'name':'Module PV1'}

    i.info_defs[Register.TEST_REG1] =  {'name':['proxy', 'Internal_Test2'],  'singleton': True, 'ha':{'dev':'test_dev', 'dev_cla': None,       'stat_cla': None, 'id':'intern_test2_',  'fmt':'| int'}}
    tests = 0
    for d_json, comp, node_id, id in i.ha_proxy_confs(ha_prfx="tsun/", node_id = 'proxy/', snr = '456'):
        if id == 'intern_test2_456':
            tests +=1

    assert tests == 1

    val = i.dev_value(Register.INTERNAL_ERROR)  # check internal error counter
    assert val == 3


def test_invalid_data_type(InvalidDataSeq):
    i = InfosG3()
    i.static_init()                # initialize counter

    val = i.dev_value(Register.INVALID_DATA_TYPE)  # check invalid data type counter
    assert val == 0


    for key, result in i.parse (InvalidDataSeq):
        pass
    assert json.dumps(i.db) == json.dumps({"inverter": {"Product_Name": "Microinv"}})

    val = i.dev_value(Register.INVALID_DATA_TYPE)  # check invalid data type counter
    assert val == 1

def test_clr_at_midnight():
    i = InfosG3()
    i.static_init()                # initialize counter
    i.set_db_def_value(Register.NO_INPUTS, 2)
    val = i.dev_value(Register.NO_INPUTS)  # valid addr but not initiliazed     
    assert val == 2
    i.info_defs[Register.TEST_REG1] = {  # add a entry with incomplete ha definition 
        'name': ['test', 'grp', 'REG_1'], 'ha': {'dev_cla': None }
        }
    i.reg_clr_at_midnight('tsun/inv_1/')
    # tsun/inv_2/input
    assert json.dumps(ClrAtMidnight.db['tsun/inv_1/total']) == json.dumps({'Daily_Generation': 0})
    assert json.dumps(ClrAtMidnight.db['tsun/inv_1/input']) == json.dumps({"pv1": {"Daily_Generation": 0}, "pv2": {"Daily_Generation": 0}})

    i.reg_clr_at_midnight('tsun/inv_1/')
    assert json.dumps(ClrAtMidnight.db['tsun/inv_1/total']) == json.dumps({'Daily_Generation': 0})
    assert json.dumps(ClrAtMidnight.db['tsun/inv_1/input']) == json.dumps({"pv1": {"Daily_Generation": 0}, "pv2": {"Daily_Generation": 0}})

    test = 0
    for key, data in ClrAtMidnight.elm():
        if key == 'tsun/inv_1/total':
            assert json.dumps(data) == json.dumps({'Daily_Generation': 0})
            test += 1
        elif key == 'tsun/inv_1/input':
            assert json.dumps(data) == json.dumps({"pv1": {"Daily_Generation": 0}, "pv2": {"Daily_Generation": 0}})
            test += 1
    assert test == 2
    assert json.dumps(ClrAtMidnight.db) == json.dumps({})

    i.reg_clr_at_midnight('tsun/inv_1/')




def test_pv_module_config():
    i = InfosG3()
    # i.set_db_def_value(Register.NO_INPUTS, 2)

    dt = {
        'pv1':{'manufacturer':'TSUN1','type': 'Module 100W'},
        'pv2':{'manufacturer':'TSUN2'},
        'pv3':{'manufacturer':'TSUN3','type': 'Module 300W'},
        'pv4':{'type': 'Module 400W'},
        'pv5':{},
                 }
    i.set_pv_module_details(dt)
    assert 'TSUN1' == i.dev_value(Register.PV1_MANUFACTURER)
    assert 'TSUN2' == i.dev_value(Register.PV2_MANUFACTURER)
    assert 'TSUN3' == i.dev_value(Register.PV3_MANUFACTURER)
    assert None == i.dev_value(Register.PV4_MANUFACTURER)
    assert None == i.dev_value(Register.PV5_MANUFACTURER)
    assert 'Module 100W' == i.dev_value(Register.PV1_MODEL)
    assert  None == i.dev_value(Register.PV2_MODEL)
    assert 'Module 300W' == i.dev_value(Register.PV3_MODEL)
    assert 'Module 400W' == i.dev_value(Register.PV4_MODEL)
    assert  None == i.dev_value(Register.PV5_MODEL)

def test_broken_info_defs():
    i = InfosG3()
    val = i.get_db_value(Register.NO_INPUTS, 666)
    assert val == 666
    i.info_defs[Register.TEST_REG1] = 'test'  # add a string instead of a dict 
    val = i.get_db_value(Register.TEST_REG1, 666)
    assert val == 666
    i.set_db_def_value(Register.TEST_REG1, 2)

