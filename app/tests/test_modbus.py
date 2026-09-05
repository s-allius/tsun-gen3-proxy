# test_with_pytest.py
import pytest
import asyncio
from modbus import Modbus
from infos import Infos, Register

class ModbusTestHelper(Modbus):
    def __init__(self):
        super().__init__(self.send_cb)
        self.db = Infos()
        self.pdu = None
        self.send_calls = 0
        self.recv_responses = 0
    def send_cb(self, pdu: bytearray, log_lvl: int, state: str):
        self.pdu = pdu
        self.send_calls += 1
    def resp_handler(self):
        self.recv_responses += 1

@pytest.mark.asyncio(loop_scope="module")
async def test_modbus_crc():
    '''Check CRC-16 calculation'''
    mb = Modbus(None)
    assert 0x0b02 == mb._Modbus__calc_crc(b'\x01\x06\x20\x08\x00\x04')
    assert 0 == mb._Modbus__calc_crc(b'\x01\x06\x20\x08\x00\x04\x02\x0b')
    assert mb._Modbus__check_crc(b'\x01\x06\x20\x08\x00\x04\x02\x0b')

    assert 0xc803 == mb._Modbus__calc_crc(b'\x01\x06\x20\x08\x00\x00')
    assert 0 == mb._Modbus__calc_crc(b'\x01\x06\x20\x08\x00\x00\x03\xc8')
    assert mb._Modbus__check_crc(b'\x01\x06\x20\x08\x00\x00\x03\xc8')

    assert 0x5c75 == mb._Modbus__calc_crc(b'\x01\x03\x08\x01\x2c\x00\x2c\x02\x2c\x2c\x46')
    msg = b'\x01\x03\x28\x51'
    msg += b'\x0e\x08\xd3\x00\x29\x13\x87\x00\x3e\x00\x00\x01\x2c\x03\xb4\x00'
    msg += b'\x08\x00\x00\x00\x00\x01\x59\x01\x21\x03\xe6\x00\x00\x00\x00\x00'
    msg += b'\x00\x00\x00\x00\x00\x00\x00\xe6\xef'
    assert 0 == mb._Modbus__calc_crc(msg)

    assert mb._Modbus__calc_crc(b'\xA1\x01\x00\x0B\xB8\x00\x02\x00\x20') == 0xd33f
    assert mb._Modbus__calc_crc(b'\xA1\x01\x00\x0B\xB8\x00\x02\x00\x20\x3F\xd3') == 0
class TestModbusProtocol:

    @pytest.mark.asyncio(loop_scope="module")
    async def test_build_modbus_pdu(self):
        '''Check building and sending a MODBUS RTU'''
        mb = ModbusTestHelper()
        mb.build_msg(1,6,0x2000,0x12)
        assert mb.pdu == b'\x01\x06\x20\x00\x00\x12\x02\x07'
        assert mb._Modbus__check_crc(mb.pdu)
        assert mb.last_addr == 1
        assert mb.last_fcode == 6   
        assert mb.last_reg == 0x2000
        assert mb.last_len == 18
        assert mb.err == 0
    
    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_req(self):
        '''Receive a valid request, which must transmitted'''
        mb = ModbusTestHelper()
        assert mb.recv_req(b'\x01\x06\x20\x00\x00\x12\x02\x07')
        assert mb.last_fcode == 6
        assert mb.last_reg == 0x2000
        assert mb.last_len == 0x12
        assert mb.err == 0

    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_req_crc_err(self):
        '''Receive a request with invalid CRC, which must be dropped'''
        mb = ModbusTestHelper()
        assert not mb.recv_req(b'\x01\x06\x20\x00\x00\x12\x02\x08')
        assert mb.pdu == None
        assert mb.last_fcode == 0   
        assert mb.last_reg == 0
        assert mb.last_len == 0
        assert mb.err == Modbus.ERR_CRC

    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_resp_crc_err(self):
        '''Receive a response with invalid CRC, which must be dropped'''
        mb = ModbusTestHelper()
        # simulate a transmitted request
        mb.req_pend = True
        mb.last_addr = 1
        mb.last_fcode = 3   
        mb.last_reg = 0x300e
        mb.last_len = 2
        mb.set_node_id('test')
        # check matching response, but with CRC error
        call = 0
        for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x04\x01\x2c\x00\x46\xbb\xf3'):
            call += 1
        assert mb.err == Modbus.ERR_CRC
        assert call == 0
        assert mb.req_pend == True
        # cleanup queue
        mb._Modbus__stop_timer()
        assert not mb.req_pend

    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_resp_invalid_addr(self):
        '''Receive a response with wrong server addr, which must be dropped'''
        mb = ModbusTestHelper()
        mb.req_pend = True
        # simulate a transmitted request
        mb.last_addr = 1
        mb.last_fcode = 3   
        mb.last_reg = 0x300e
        mb.last_len = 2
        mb.set_node_id('test')

        # check not matching response, with wrong server addr
        call = 0
        for key, update in mb.recv_resp(mb.db, b'\x02\x03\x04\x01\x2c\x00\x46\x88\xf4'):
            call += 1
        assert mb.err == Modbus.ERR_WRONG_ADDR
        assert call == 0
        assert mb.req_pend == True
        assert mb.que.qsize() == 0

        # cleanup queue
        mb._Modbus__stop_timer()
        assert not mb.req_pend

    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_recv_fcode(self):
        '''Receive a response with wrong function code, which must be dropped'''
        mb = ModbusTestHelper()
        mb.build_msg(1,4,0x300e,2)
        assert mb.que.qsize() == 0
        assert mb.req_pend
    
        # check not matching response, with wrong function code
        call = 0
        mb.set_node_id('test')
        for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x04\x01\x2c\x00\x46\xbb\xf4'):
            call += 1

        assert mb.err == Modbus.ERR_UNEXPECTED_FCODE
        assert call == 0
        assert mb.req_pend == True
        assert mb.que.qsize() == 0

        # cleanup queue
        mb._Modbus__stop_timer()
        assert not mb.req_pend

    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_resp_len(self):
        '''Receive a response with wrong data length, which must be dropped'''
        mb = ModbusTestHelper()
        mb.build_msg(1,3,0x300e,3)
        assert mb.que.qsize() == 0
        assert mb.req_pend
        assert mb.last_len == 3

        # check not matching response, with wrong data length
        call = 0
        mb.set_node_id('test')
        for key, update, _ in mb.recv_resp(mb.db, b'\x01\x03\x04\x01\x2c\x00\x46\xbb\xf4'):
            call += 1

        assert mb.err == Modbus.ERR_UNEXPECTED_LEN
        assert call == 0
        assert mb.req_pend == True
        assert mb.que.qsize() == 0

        # cleanup queue
        mb._Modbus__stop_timer()
        assert not mb.req_pend

    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_unexpect_resp(self):
        '''Receive a response when we havn't sent a request'''
        mb = ModbusTestHelper()
        assert not mb.req_pend
    
        # check unexpected response, which must be dropped
        call = 0
        mb.set_node_id('test')
        for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x04\x01\x2c\x00\x46\xbb\xf4'):
            call += 1

        assert mb.err == Modbus.ERR_NO_REQ_PENDING
        assert call == 0
        assert mb.req_pend == False
        assert mb.que.qsize() == 0

    @pytest.mark.asyncio(loop_scope="module")
    async def test_parse_resp(self):
        '''Receive matching response and parse the values'''
        mb = ModbusTestHelper()
        mb.build_msg(1,3,0x3007,6)
        assert mb.que.qsize() == 0
        assert mb.req_pend

        call = 0
        mb.set_node_id('test')
        exp_result = ['V0.0.2C', 4.4, 0.7, 0.7, 30]
        for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x0c\x01\x2c\x00\x2c\x00\x2c\x00\x46\x00\x46\x00\x46\x32\xc8'):
            if key == 'grid':
                assert update == True
            elif key == 'inverter':
                assert update == True
            elif key == 'env':
                assert update == True
            else:
                pytest.fail(f'Unexpected key {key}')
            assert exp_result[call] == val
            call += 1
        assert mb.err == 0
        assert call == 5
        assert mb.que.qsize() == 0
        assert not mb.req_pend


class TestNativeProtocol:
    '''Test the native protocol parsing'''

    @pytest.mark.asyncio(loop_scope="module")
    async def test_build_native_modbus_pdu(self):
        '''Check building and sending a MODBUS RTU'''
        mb = ModbusTestHelper()
        mb.build_native_msg(Modbus.NATIVE_READ_VALUES,3000,32)
        assert mb.pdu == b'\xA1\x01\x00\x0B\xB8\x00\x02\x00\x20\xD3\x3F'
        assert mb._Modbus__check_crc(mb.pdu, swap_crc=True)
        assert mb.last_fcode == 0xA1   
        assert mb.last_addr == 1
        assert mb.last_reg == 3000
        assert mb.last_len == 64
        assert mb.err == 0

    @pytest.mark.asyncio(loop_scope="module")
    async def test_parse_native_resp(self):
        '''Receive matching native response and parse the values'''
        mb = ModbusTestHelper()
        mb.build_native_msg(Modbus.NATIVE_READ_VALUES,0x3007,16)
        assert mb.que.qsize() == 0
        assert mb.req_pend

        call = 0
        mb.set_node_id('test')
        exp_result = ['V0.0.03', 0.03, 6.9, 0.41, 0.02, -40, 30.0, 2188, 39.8, 0.01]
        for key, update, val in mb.recv_native_resp(mb.db, b'\xA1\x81\x01\x0B\xBF\x00\x20\x6E\x11\x03\x00\x19\x10\x03\x00' +
            b'\x29\x09\x45\x00\x29\x00\x86\x13\x02\x00\x5E\x00\x00\x00\x19\x10' +
            b'\xB8\x0B\x8C\x08\x8E\x01\x01\x00\x0B\x4A'):

            if key == 'grid':
                assert update == True
            elif key == 'inverter':
                assert update == True
            elif key == 'env':
                assert update == True
            elif key == 'total':
                assert update == True
            elif key == 'other':
                assert update == True
            else:
                pytest.fail(f'Unexpected key {key}')
            assert exp_result[call] == val
            call += 1
        assert mb.err == 0
        assert call == 10
        assert mb.que.qsize() == 0
        assert not mb.req_pend

    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_native_resp_crc_err(self):
        '''Receive a response with invalid CRC, which must be dropped'''
        mb = ModbusTestHelper()
        # simulate a transmitted request
        mb.build_native_msg(Modbus.NATIVE_READ_VALUES,0x3000,1)
        mb.set_node_id('test')
        assert mb.req_pend
    
        # check matching response, but with CRC error
        call = 0
        for key, update, val in mb.recv_native_resp(mb.db, b'\xA1\x81\x01\x0b\xb8\x00\x02\x6a\x04'):
            call += 1
        assert mb.err == Modbus.ERR_CRC
        assert call == 0
        assert mb.req_pend
        # cleanup queue
        mb._Modbus__stop_timer()
        assert not mb.req_pend

    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_native_resp_invalid_fcode(self):
        '''Receive a response with invalid function code, which must be dropped'''
        mb = ModbusTestHelper()
        # simulate a transmitted request
        mb.build_native_msg(Modbus.NATIVE_READ_VALUES,0x3000,1)
        mb.set_node_id('test')
        assert mb.req_pend
    
        # check matching response, but with CRC error
        call = 0
        for key, update, val in mb.recv_native_resp(mb.db, b'\xA7\x81\x01\x0b\xb8\x00\x02\xdb\xed'):
            call += 1
        assert mb.err == Modbus.ERR_UNEXPECTED_FCODE
        assert call == 0
        assert mb.req_pend
        # cleanup queue
        mb._Modbus__stop_timer()
        assert not mb.req_pend

    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_native_resp_wrong_len(self):
        '''Receive a response with a wrong element count, which must be dropped'''
        mb = ModbusTestHelper()
        # simulate a transmitted request
        mb.build_native_msg(Modbus.NATIVE_READ_VALUES,0x3000,2)
        mb.set_node_id('test')
        assert mb.req_pend
    
        # check matching response, but with CRC error
        call = 0
        for key, update, val in mb.recv_native_resp(mb.db, b'\xA1\x81\x01\x0b\xb8\x00\x02\xdb\x8b'):
            call += 1
        assert mb.err == Modbus.ERR_UNEXPECTED_LEN
        assert call == 0
        assert mb.req_pend
        # cleanup queue
        mb._Modbus__stop_timer()
        assert not mb.req_pend

    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_native_resp_unexpected(self):
        '''Receive a unexpected response, which must be dropped'''
        mb = ModbusTestHelper()
        assert not mb.req_pend
    
        # check matching response, but with CRC error
        call = 0
        for key, update, val in mb.recv_native_resp(mb.db, b'\xA1\x81\x01\x0b\xb8\x00\x02\xdb\x8b'):
            call += 1
        assert mb.err == Modbus.ERR_NO_REQ_PENDING
        assert call == 0

    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_native_unknown_addr(self):
        '''Receive a response with unknown address, which must be dropped'''
        mb = ModbusTestHelper()
        # simulate a transmitted request
        mb.build_native_msg(Modbus.NATIVE_READ_VALUES,0x3000,2)
        mb.set_node_id('test')
        assert mb.req_pend
    
        # check matching response, but with CRC error
        call = 0
        for key, update, val in mb.recv_native_resp(mb.db, b'\xA1\x81\x11\x0b\xb8\x00\x02\x00\x00\x6a\x37'):
            call += 1
        assert mb.err == Modbus.ERR_UNKNOWN_ADDR
        assert call == 0
        assert mb.req_pend
        # cleanup queue
        mb._Modbus__stop_timer()
        assert not mb.req_pend

    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_native_invalid_length(self):
        '''Receive a response with invalid length requested, which must be dropped'''
        mb = ModbusTestHelper()
        # simulate a transmitted request
        mb.build_native_msg(Modbus.NATIVE_READ_VALUES,0x3000,2)
        mb.set_node_id('test')
        assert mb.req_pend
    
        # check matching response, but with CRC error
        call = 0
        for key, update, val in mb.recv_native_resp(mb.db, b'\xA1\x81\x12\x0b\xb8\x00\x02\x00\x00\x6a\x04'):
            call += 1
        assert mb.err == Modbus.ERR_INVALID_LEN
        assert call == 0
        assert mb.req_pend
        # cleanup queue
        mb._Modbus__stop_timer()
        assert not mb.req_pend

    @pytest.mark.asyncio(loop_scope="module")
    async def test_recv_native_unknown_status(self):
        '''Receive a response with unknown status code, which must be dropped'''
        mb = ModbusTestHelper()
        # simulate a transmitted request
        mb.build_native_msg(Modbus.NATIVE_READ_VALUES,0x3000,2)
        mb.set_node_id('test')
        assert mb.req_pend
    
        # check matching response, but with CRC error
        call = 0
        for key, update, val in mb.recv_native_resp(mb.db, b'\xA1\x81\x21\x0b\xb8\x00\x02\x00\x00\x69\x07'):
            call += 1
        assert mb.err == Modbus.ERR_UNKNOWN_STATUS
        assert call == 0
        assert mb.req_pend
        # cleanup queue
        mb._Modbus__stop_timer()
        assert not mb.req_pend

@pytest.mark.asyncio(loop_scope="module")
async def test_queue():
    mb = ModbusTestHelper()
    mb.build_msg(1,3,0x3022,4)
    assert mb.que.qsize() == 0
    assert mb.req_pend

    assert mb.send_calls == 1
    assert mb.pdu == b'\x01\x030"\x00\x04\xeb\x03'
    mb.pdu = None
    assert mb.send_calls == 1
    assert mb.pdu == None

    assert mb.que.qsize() == 0

    # cleanup queue
    mb._Modbus__stop_timer()
    assert not mb.req_pend

@pytest.mark.asyncio(loop_scope="module")
async def test_queue2():
    '''Check queue handling for build_msg() calls'''
    mb = ModbusTestHelper()
    mb.build_msg(1,3,0x3007,6)
    mb.build_msg(1,6,0x2008,4)
    assert mb.que.qsize() == 1
    assert mb.req_pend
    mb.build_msg(1,3,0x3007,6)
    assert mb.que.qsize() == 2
    assert mb.req_pend

    assert mb.send_calls == 1
    assert mb.pdu == b'\x01\x030\x07\x00\x06{\t'
    call = 0
    mb.set_node_id('test')
    exp_result = ['V0.0.2C', 4.4, 0.7, 0.7, 30]
    for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x0c\x01\x2c\x00\x2c\x00\x2c\x00\x46\x00\x46\x00\x46\x32\xc8'):
        if key == 'grid':
            assert update == True
        elif key == 'inverter':
            assert update == True
        elif key == 'env':
            assert update == True
        else:
            assert False
        assert exp_result[call] == val
        call += 1
    assert 0 == mb.err
    assert 5 == call

    assert mb.que.qsize() == 1
    assert mb.send_calls == 2
    assert mb.pdu == b'\x01\x06\x20\x08\x00\x04\x02\x0b'

    for key, update, val in mb.recv_resp(mb.db, b'\x01\x06\x20\x08\x00\x04\x02\x0b'):
        pass  # call generator mb.recv_resp()

    assert mb.que.qsize() == 0
    assert mb.send_calls == 3
    assert mb.pdu == b'\x01\x030\x07\x00\x06{\t'
    call = 0
    for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x0c\x01\x2c\x00\x2c\x00\x2c\x00\x46\x00\x46\x00\x46\x32\xc8'):
        call += 1
    assert 0 == mb.err
    assert 5 == call

    assert mb.que.qsize() == 0
    assert not mb.req_pend

@pytest.mark.asyncio(loop_scope="module")
async def test_queue3():
    '''Check queue handling for recv_req() calls'''
    mb = ModbusTestHelper()
    assert mb.recv_req(b'\x01\x03\x30\x07\x00\x06{\t', mb.resp_handler)
    assert mb.recv_req(b'\x01\x06\x20\x08\x00\x04\x02\x0b', mb.resp_handler)
    assert mb.que.qsize() == 1
    assert mb.req_pend
    assert mb.recv_req(b'\x01\x03\x30\x07\x00\x06{\t')
    assert mb.que.qsize() == 2
    assert mb.req_pend

    assert mb.send_calls == 1
    assert mb.pdu == b'\x01\x030\x07\x00\x06{\t'
    assert mb.recv_responses == 0

    call = 0
    mb.set_node_id('test')
    exp_result = ['V0.0.2C', 4.4, 0.7, 0.7, 30]
    for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x0c\x01\x2c\x00\x2c\x00\x2c\x00\x46\x00\x46\x00\x46\x32\xc8'):
        if key == 'grid':
            assert update == True
        elif key == 'inverter':
            assert update == True
        elif key == 'env':
            assert update == True
        else:
            assert False
        assert exp_result[call] == val
        call += 1
    assert 0 == mb.err
    assert 5 == call
    assert mb.recv_responses == 1

    assert mb.que.qsize() == 1
    assert mb.send_calls == 2
    assert mb.pdu == b'\x01\x06\x20\x08\x00\x04\x02\x0b'

    for key, update, val in mb.recv_resp(mb.db, b'\x01\x06\x20\x08\x00\x04\x02\x0b'):
        pass  # no code in loop is OK; calling the generator is the purpose
    assert 0 == mb.err
    assert mb.recv_responses == 2

    assert mb.que.qsize() == 0
    assert mb.send_calls == 3
    assert mb.pdu == b'\x01\x030\x07\x00\x06{\t'
    call = 0
    for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x0c\x01\x2c\x00\x2c\x00\x2c\x00\x46\x00\x46\x00\x46\x32\xc8'):
        call += 1
    assert 0 == mb.err
    assert mb.recv_responses == 2
    assert 5 == call


    assert mb.que.qsize() == 0
    assert not mb.req_pend

@pytest.mark.asyncio(loop_scope="module")
async def test_timeout(my_loop):
    '''Test MODBUS response timeout and RTU retransmitting'''
    assert asyncio.get_running_loop()
    mb = ModbusTestHelper()
    mb.max_retries = 2
    mb.timeout = 0.01  # 10ms timeout for fast testing, expect a time resolution of at least 10ms
    assert asyncio.get_running_loop() == mb.loop
    mb.build_msg(1,3,0x3007,6)
    mb.build_msg(1,6,0x2008,4)

    assert mb.que.qsize() == 1
    assert mb.req_pend
    assert mb.retry_cnt == 0
    assert mb.send_calls == 1
    assert mb.pdu == b'\x01\x030\x07\x00\x06{\t'

    mb.pdu = None
    await asyncio.sleep(0.011)    # wait for first timeout and retransmittion
    assert mb.que.qsize() == 1
    assert mb.req_pend
    assert mb.retry_cnt == 1
    assert mb.send_calls == 2
    assert mb.pdu == b'\x01\x030\x07\x00\x06{\t'

    mb.pdu = None
    await asyncio.sleep(0.011)    # wait for second timeout and retransmittion
    assert mb.que.qsize() == 1
    assert mb.req_pend
    assert mb.retry_cnt == 2
    assert mb.send_calls == 3
    assert mb.pdu == b'\x01\x030\x07\x00\x06{\t'

    mb.pdu = None
    await asyncio.sleep(0.011)    # wait for third timeout and next pdu
    assert mb.que.qsize() == 0
    assert mb.req_pend
    assert mb.retry_cnt == 0
    assert mb.send_calls == 4
    assert mb.pdu == b'\x01\x06\x20\x08\x00\x04\x02\x0b'

    mb.max_retries = 0          # next pdu without retranmsission
    await asyncio.sleep(0.011)    # wait for fourth timout
    assert mb.que.qsize() == 0
    assert not mb.req_pend
    assert mb.retry_cnt == 0
    assert mb.send_calls == 4

@pytest.mark.asyncio(loop_scope="module")
async def test_recv_unknown_data():
    '''Receive a response with an unknwon register'''
    mb = ModbusTestHelper()
    assert 0x9000 not in mb.mb_reg_mapping
    mb.mb_reg_mapping[0x9000] = {'reg': Register.TEST_REG1,   'fmt': '!H', 'ratio':  1}

    mb.build_msg(1,3,0x9000,2)

    # check matching response, but with CRC error
    call = 0
    mb.set_node_id('test')
    for key, update, val in mb.recv_resp(mb.db, b'\x01\x03\x04\x01\x2c\x00\x46\xbb\xf4'):
        call += 1
    assert mb.err == 0
    assert 0 == call
    assert not mb.req_pend

    del mb.mb_reg_mapping[0x9000]

@pytest.mark.asyncio(loop_scope="module")
async def test_close():
    '''Check queue handling for build_msg() calls'''
    mb = ModbusTestHelper()
    mb.build_msg(1,3,0x3007,6)
    mb.build_msg(1,6,0x2008,4)
    assert mb.que.qsize() == 1
    mb.build_msg(1,3,0x3007,6)
    assert mb.que.qsize() == 2
    assert mb.que.empty() == False 
    mb.close()
    assert mb.que.qsize() == 0
    assert mb.que.empty() == True 
