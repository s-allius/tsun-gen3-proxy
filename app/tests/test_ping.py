# test_with_pytest.py
import pytest
import asyncio
import gc

from inverter_base import InverterBase
from async_stream import AsyncStreamServer

from test_modbus_tcp import FakeReader, FakeWriter
from test_inverter_base import config_conn, patch_open_connection

pytest_plugins = ('pytest_asyncio',)


@pytest.mark.asyncio(loop_scope="session")
async def test_ping():
    assert asyncio.get_running_loop()
    reader = FakeReader()
    reader.test  = FakeReader.RD_TEST_BUFFER
    reader.buf = b'ping'
    reader.on_recv.set()
    writer =  FakeWriter()
    def timeout():
        return 0.1
    ifc =  AsyncStreamServer(reader, writer, None, None, None)
    ifc.prot_set_timeout_cb(timeout)
    # ifc.rx_set_cb(app_read)
    await ifc.server_loop()
    print('End loop')
    assert 0 == ifc.rx_len()
    assert 0 == ifc.tx_len()
    assert b'ping' == writer.buf
    del ifc

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0