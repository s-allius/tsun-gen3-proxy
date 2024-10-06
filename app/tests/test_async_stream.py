# test_with_pytest.py
import pytest
import asyncio
import gc
import time

from app.src.infos import Infos
from app.src.inverter_base import InverterBase
from app.src.async_stream import AsyncStreamServer, AsyncStreamClient

from app.tests.test_modbus_tcp import FakeReader, FakeWriter
from app.tests.test_inverter_base import config_conn, patch_open_connection

pytest_plugins = ('pytest_asyncio',)

# initialize the proxy statistics
Infos.static_init()

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
        nonlocal ifc
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
    global test
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
        nonlocal ifc
        ifc.close()  # clears the closed callback
        cnt += 1
    def app_read():
        nonlocal ifc
        ifc.proc_start -= 3
        return 0.01  # async wait of 0.01 
    cnt = 0
    ifc =  AsyncStreamClient(reader, writer, None, closed)
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
    global test
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
        nonlocal ifc
        ifc.close()  # clears the closed callback
        cnt += 1
    
    cnt = 0
    ifc =  AsyncStreamClient(reader, writer, None, closed)
    ifc.prot_set_timeout_cb(timeout)
    ifc.tx_add(b'test-data-resp')
    assert 14 == ifc.tx_len()
    await ifc.client_loop('')
    print('End loop')
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
        nonlocal ifc
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
        nonlocal ifc
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
    global test
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
        nonlocal ifc
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
    global test
    assert asyncio.get_running_loop()
    reader = FakeReader()
    reader.test  = FakeReader.RD_TEST_OS_ERROR

    reader.on_recv.set()
    writer =  FakeWriter()
    cnt = 0
    def timeout():
        return 1
    def closed():
        nonlocal cnt
        nonlocal ifc
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
