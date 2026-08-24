# test_with_pytest.py
import pytest
import asyncio
import gc

from inverter_base import InverterBase
from async_stream import AsyncStreamServer

from test_modbus_tcp import FakeReader, FakeWriter
from test_inverter_base import config_conn, patch_open_connection


@pytest.mark.asyncio(loop_scope="module")
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
    assert ifc.rx_len() == 0
    assert ifc.tx_len() == 0
    assert writer.buf == b'ping'
    del ifc

    cnt = 0
    for inv in InverterBase:
        print(f'InverterBase refs:{gc.get_referrers(inv)}')
        cnt += 1
    assert cnt == 0