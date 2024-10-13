# test_with_pytest.py

from app.src.byte_fifo import ByteFifo

def test_fifo():
    read = ByteFifo()
    assert 0 == len(read)
    read += b'12'
    assert 2 == len(read)
    read += bytearray("34", encoding='UTF8')
    assert 4 == len(read)
    assert b'12' == read.peek(2)
    assert 4 == len(read)
    assert b'1234' == read.peek()
    assert 4 == len(read)
    assert b'12' == read.get(2)
    assert 2 == len(read)
    assert b'34' == read.get()
    assert 0 == len(read)

def test_fifo_fmt():
    read = ByteFifo()
    read += b'1234'
    assert b'1234' == read.peek()
    assert "  0000 | 31 32 33 34                                      | 1234" == f'{read}'

def test_fifo_observer():
    read = ByteFifo()

    def _read():
        assert b'1234' == read.get(4)

    read += b'12'
    assert 2 == len(read)
    read()
    read.reg_trigger(_read)
    read += b'34'
    assert 4 == len(read)
    read()
    assert 0 == len(read)
    assert b'' == read.peek(2)
    assert b'' == read.get(2)
    assert 0 == len(read)
