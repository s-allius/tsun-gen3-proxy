# test_with_pytest.py
import pytest
import asyncio
import gc
import time

from infos import Infos
from inverter_base import InverterBase
from async_stream import AsyncStreamServer, AsyncStreamClient, StreamPtr
from messages import Message

from test_modbus_tcp import FakeReader, FakeWriter
from test_inverter_base import config_conn, patch_open_connection

pytest_plugins = ('pytest_asyncio',)

# initialize the proxy statistics
Infos.static_init()

class FakeProto(Message):
    def __init__(self, ifc, server_side):
        super().__init__('G3F', ifc, server_side, None, 10)
        self.conn_no = 0

    def mb_timout_cb(self, exp_cnt):
        pass  # empty callback

def fake_reader_fwd():
    reader = FakeReader()
    reader.test  = FakeReader.RD_TEST_13_BYTES
    reader.on_recv.set()
    return reader

def test_timeout_cb():
    reader = FakeReader()
    writer =  FakeWriter()
    def timeout():
        return 13
    
    ifc =  AsyncStreamClient(reader, writer, None, None)
    assert 360 == ifc._AsyncStream__timeout()
    ifc.prot_set_timeout_cb(timeout)
    assert 13 == ifc._AsyncStream__timeout()
    ifc.prot_set_timeout_cb(None)
    assert 360 == ifc._AsyncStream__timeout()

    # call healthy outside the contexter manager (__exit__() was called)
    assert ifc.healthy()
    del ifc

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

def test_health():
    reader = FakeReader()
    writer =  FakeWriter()
    
    ifc =  AsyncStreamClient(reader, writer, None, None)
    ifc.proc_start = time.time()
    assert ifc.healthy()
    ifc.proc_start = time.time() -10
    assert not ifc.healthy()
    ifc.proc_start = None
    assert ifc.healthy()

    del ifc

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

@pytest.mark.asyncio
async def test_close_cb():
    assert asyncio.get_running_loop()
    reader = FakeReader()
    writer =  FakeWriter()
    cnt = 0
    def timeout():
        return 0.1
    def closed():
        nonlocal cnt
        ifc.close()  # clears the closed callback
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamClient(reader, writer, None, closed)
    ifc.prot_set_timeout_cb(timeout)
    await ifc.client_loop('')
    assert cnt == 1
    ifc.prot_set_timeout_cb(timeout)
    await ifc.client_loop('')
    assert cnt == 1         # check that the closed method would not be called 
    del ifc

    cnt = 0
    ifc =  AsyncStreamClient(reader, writer, None, None)
    ifc.prot_set_timeout_cb(timeout)
    await ifc.client_loop('')
    assert cnt == 0
    del ifc

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

@pytest.mark.asyncio
async def test_read():
    assert asyncio.get_running_loop()
    reader = FakeReader()
    reader.test  = FakeReader.RD_TEST_13_BYTES
    reader.on_recv.set()
    writer =  FakeWriter()
    cnt = 0
    def timeout():
        return 1
    def closed():
        nonlocal cnt
        ifc.close()  # clears the closed callback
        cnt += 1
    def app_read():
        ifc.proc_start -= 3
        return 0.01  # async wait of 0.01 
    cnt = 0
    ifc =  AsyncStreamClient(reader, writer, None, closed)
    ifc.proc_max = 0
    ifc.prot_set_timeout_cb(timeout)
    ifc.rx_set_cb(app_read)
    await ifc.client_loop('')
    print('End loop')
    assert ifc.proc_max >= 3
    assert 13 == ifc.rx_len()
    assert cnt == 1
    del ifc

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

@pytest.mark.asyncio
async def test_write():
    assert asyncio.get_running_loop()
    reader = FakeReader()
    reader.test  = FakeReader.RD_TEST_13_BYTES
    reader.on_recv.set()
    writer =  FakeWriter()
    cnt = 0
    def timeout():
        return 1
    def closed():
        nonlocal cnt
        ifc.close()  # clears the closed callback
        cnt += 1
    def app_read():
        ifc.proc_start -= 3
        return 0.01  # async wait of 0.01 
    
    cnt = 0
    ifc =  AsyncStreamClient(reader, writer, None, closed)
    ifc.proc_max = 10
    ifc.prot_set_timeout_cb(timeout)
    ifc.rx_set_cb(app_read)
    ifc.tx_add(b'test-data-resp')
    assert 14 == ifc.tx_len()
    await ifc.client_loop('')
    print('End loop')
    assert ifc.proc_max >= 3
    assert 13 == ifc.rx_len()
    assert 0 == ifc.tx_len()
    assert cnt == 1
    del ifc

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

@pytest.mark.asyncio
async def test_publ_mqtt_cb():
    assert asyncio.get_running_loop()
    reader = FakeReader()
    reader.test  = FakeReader.RD_TEST_13_BYTES
    reader.on_recv.set()
    writer =  FakeWriter()
    cnt = 0
    def timeout():
        return 0.1
    async def publ_mqtt():
        nonlocal cnt
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamServer(reader, writer, publ_mqtt, None, None)
    assert ifc.async_publ_mqtt
    ifc.prot_set_timeout_cb(timeout)
    await ifc.server_loop()
    assert cnt == 3     # 2 calls in server_loop() and 1 in loop()
    assert ifc.async_publ_mqtt
    ifc.close()  # clears the closed callback
    assert not ifc.async_publ_mqtt
    del ifc

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

@pytest.mark.asyncio
async def test_create_remote_cb():
    assert asyncio.get_running_loop()
    reader = FakeReader()
    writer =  FakeWriter()
    cnt = 0
    def timeout():
        return 0.1
    async def create_remote():
        nonlocal cnt
        ifc.close()  # clears the closed callback
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamServer(reader, writer, None, create_remote, None)
    assert ifc.create_remote
    await ifc.create_remote()
    assert cnt == 1
    ifc.prot_set_timeout_cb(timeout)
    await ifc.server_loop()
    assert not ifc.create_remote
    del ifc

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

@pytest.mark.asyncio
async def test_sw_exception():
    assert asyncio.get_running_loop()
    reader = FakeReader()
    reader.test  = FakeReader.RD_TEST_SW_EXCEPT
    reader.on_recv.set()
    writer =  FakeWriter()
    cnt = 0
    def timeout():
        return 1
    def closed():
        nonlocal cnt
        ifc.close()  # clears the closed callback
        cnt += 1
    cnt = 0
    ifc =  AsyncStreamClient(reader, writer, None, closed)
    ifc.prot_set_timeout_cb(timeout)
    await ifc.client_loop('')
    print('End loop')
    assert cnt == 1
    del ifc

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

@pytest.mark.asyncio
async def test_os_error():
    assert asyncio.get_running_loop()
    reader = FakeReader()
    reader.test  = FakeReader.RD_TEST_OS_ERROR

    reader.on_recv.set()
    writer =  FakeWriter()
    cnt = 0
    ifc = None
    def timeout():
        return 1
    def closed():
        nonlocal cnt
        ifc.close()  # clears the closed callback
        cnt += 1
    cnt = 0
    ifc =  AsyncStreamClient(reader, writer, None, closed)
    ifc.prot_set_timeout_cb(timeout)
    await ifc.client_loop('')
    print('End loop')
    assert cnt == 1
    del ifc

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0

class TestType():
    FWD_NO_EXCPT = 1
    FWD_SW_EXCPT = 2
    FWD_TIMEOUT = 3
    FWD_OS_ERROR = 4
    FWD_OS_ERROR_NO_STREAM = 5
    FWD_RUNTIME_ERROR = 6
    FWD_RUNTIME_ERROR_NO_STREAM = 7

def create_remote(remote, test_type, with_close_hdr:bool = False):
    def update_hdr(buf):
        return
    def callback():
        if test_type == TestType.FWD_SW_EXCPT:
            remote.unknown_var += 1    
        elif test_type == TestType.FWD_TIMEOUT:
            raise TimeoutError
        elif test_type == TestType.FWD_OS_ERROR:
            raise ConnectionRefusedError
        elif test_type == TestType.FWD_OS_ERROR_NO_STREAM:
            remote.stream = None
            raise ConnectionRefusedError
        elif test_type == TestType.FWD_RUNTIME_ERROR:
            raise RuntimeError("Peer closed")
        elif test_type == TestType.FWD_RUNTIME_ERROR_NO_STREAM:
            remote.stream = None
            raise RuntimeError("Peer closed")
        return True

    def close():
        return
    if with_close_hdr:
        close_hndl = close
    else:
        close_hndl = None
    
    remote.ifc = AsyncStreamClient(
        FakeReader(), FakeWriter(), StreamPtr(None), close_hndl)
    remote.ifc.prot_set_update_header_cb(update_hdr)
    remote.ifc.prot_set_init_new_client_conn_cb(callback)
    remote.stream = FakeProto(remote.ifc, False)

@pytest.mark.asyncio
async def test_forward():
    assert asyncio.get_running_loop()
    remote = StreamPtr(None)
    cnt = 0
    ifc = None
    async def _create_remote():
        nonlocal cnt
        create_remote(remote, TestType.FWD_NO_EXCPT)
        ifc.fwd_add(b'test-forward_msg2 ')
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamServer(fake_reader_fwd(), FakeWriter(), None, _create_remote, remote)
    ifc.fwd_add(b'test-forward_msg')
    await ifc.server_loop()
    assert cnt == 1
    del ifc

@pytest.mark.asyncio
async def test_forward_with_conn():
    assert asyncio.get_running_loop()
    remote = StreamPtr(None)
    cnt = 0

    async def _create_remote():
        nonlocal cnt
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamServer(fake_reader_fwd(), FakeWriter(), None, _create_remote, remote)
    create_remote(remote, TestType.FWD_NO_EXCPT)
    ifc.fwd_add(b'test-forward_msg')
    await ifc.server_loop()
    assert cnt == 0
    del ifc

@pytest.mark.asyncio
async def test_forward_no_conn():
    assert asyncio.get_running_loop()
    remote = StreamPtr(None)
    cnt = 0

    async def _create_remote():
        nonlocal cnt
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamServer(fake_reader_fwd(), FakeWriter(), None, _create_remote, remote)
    ifc.fwd_add(b'test-forward_msg')
    await ifc.server_loop()
    assert cnt == 1
    del ifc

@pytest.mark.asyncio
async def test_forward_sw_except():
    assert asyncio.get_running_loop()
    remote = StreamPtr(None)
    cnt = 0

    async def _create_remote():
        nonlocal cnt
        create_remote(remote, TestType.FWD_SW_EXCPT)
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamServer(fake_reader_fwd(), FakeWriter(), None, _create_remote, remote)
    ifc.fwd_add(b'test-forward_msg')
    await ifc.server_loop()
    assert cnt == 1
    del ifc

@pytest.mark.asyncio
async def test_forward_os_error():
    assert asyncio.get_running_loop()
    remote = StreamPtr(None)
    cnt = 0

    async def _create_remote():
        nonlocal cnt
        create_remote(remote, TestType.FWD_OS_ERROR)
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamServer(fake_reader_fwd(), FakeWriter(), None, _create_remote, remote)
    ifc.fwd_add(b'test-forward_msg')
    await ifc.server_loop()
    assert cnt == 1
    del ifc

@pytest.mark.asyncio
async def test_forward_os_error2():
    assert asyncio.get_running_loop()
    remote = StreamPtr(None)
    cnt = 0

    async def _create_remote():
        nonlocal cnt
        create_remote(remote, TestType.FWD_OS_ERROR, True)
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamServer(fake_reader_fwd(), FakeWriter(), None, _create_remote, remote)
    ifc.fwd_add(b'test-forward_msg')
    await ifc.server_loop()
    assert cnt == 1
    del ifc

@pytest.mark.asyncio
async def test_forward_os_error3():
    assert asyncio.get_running_loop()
    remote = StreamPtr(None)
    cnt = 0

    async def _create_remote():
        nonlocal cnt
        create_remote(remote, TestType.FWD_OS_ERROR_NO_STREAM)
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamServer(fake_reader_fwd(), FakeWriter(), None, _create_remote, remote)
    ifc.fwd_add(b'test-forward_msg')
    await ifc.server_loop()
    assert cnt == 1
    del ifc

@pytest.mark.asyncio
async def test_forward_runtime_error():
    assert asyncio.get_running_loop()
    remote = StreamPtr(None)
    cnt = 0

    async def _create_remote():
        nonlocal cnt
        create_remote(remote, TestType.FWD_RUNTIME_ERROR)
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamServer(fake_reader_fwd(), FakeWriter(), None, _create_remote, remote)
    ifc.fwd_add(b'test-forward_msg')
    await ifc.server_loop()
    assert cnt == 1
    del ifc

@pytest.mark.asyncio
async def test_forward_runtime_error2():
    assert asyncio.get_running_loop()
    remote = StreamPtr(None)
    cnt = 0

    async def _create_remote():
        nonlocal cnt
        create_remote(remote, TestType.FWD_RUNTIME_ERROR, True)
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamServer(fake_reader_fwd(), FakeWriter(), None, _create_remote, remote)
    ifc.fwd_add(b'test-forward_msg')
    await ifc.server_loop()
    assert cnt == 1
    del ifc

@pytest.mark.asyncio
async def test_forward_runtime_error3():
    assert asyncio.get_running_loop()
    remote = StreamPtr(None)
    cnt = 0

    async def _create_remote():
        nonlocal cnt
        create_remote(remote, TestType.FWD_RUNTIME_ERROR_NO_STREAM, True)
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamServer(fake_reader_fwd(), FakeWriter(), None, _create_remote, remote)
    ifc.fwd_add(b'test-forward_msg')
    await ifc.server_loop()
    assert cnt == 1
    del ifc

@pytest.mark.asyncio
async def test_forward_resp():
    assert asyncio.get_running_loop()
    remote = StreamPtr(None)
    cnt = 0

    def _close_cb():
        nonlocal cnt
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamClient(fake_reader_fwd(), FakeWriter(), remote, _close_cb)
    create_remote(remote, TestType.FWD_NO_EXCPT)
    ifc.fwd_add(b'test-forward_msg')
    await ifc.client_loop('')
    assert cnt == 1
    del ifc

@pytest.mark.asyncio
async def test_forward_resp2():
    assert asyncio.get_running_loop()
    remote = StreamPtr(None)
    cnt = 0

    def _close_cb():
        nonlocal cnt
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamClient(fake_reader_fwd(), FakeWriter(), None, _close_cb)
    create_remote(remote, TestType.FWD_NO_EXCPT)
    ifc.fwd_add(b'test-forward_msg')
    await ifc.client_loop('')
    assert cnt == 1
    del ifc
