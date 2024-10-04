import asyncio
import logging
import traceback
import time
from asyncio import StreamReader, StreamWriter
from typing import Self
from itertools import count

if __name__ == "app.src.async_stream":
    from app.src.proxy import Proxy
    from app.src.byte_fifo import ByteFifo
    from app.src.async_ifc import AsyncIfc
    from app.src.infos import Infos
else:  # pragma: no cover
    from proxy import Proxy
    from byte_fifo import ByteFifo
    from async_ifc import AsyncIfc
    from infos import Infos


import gc
logger = logging.getLogger('conn')


class AsyncIfcImpl(AsyncIfc):
    _ids = count(0)

    def __init__(self) -> None:
        logger.debug('AsyncIfcImpl.__init__')
        self.fwd_fifo = ByteFifo()
        self.tx_fifo = ByteFifo()
        self.rx_fifo = ByteFifo()
        self.conn_no = next(self._ids)
        self.node_id = ''
        self.timeout_cb = None
        self.init_new_client_conn_cb = None
        self.update_header_cb = None

    def close(self):
        self.timeout_cb = None
        self.fwd_fifo.reg_trigger(None)
        self.tx_fifo.reg_trigger(None)
        self.rx_fifo.reg_trigger(None)

    def set_node_id(self, value: str):
        self.node_id = value

    def get_conn_no(self):
        return self.conn_no

    def tx_add(self, data: bytearray):
        ''' add data to transmit queue'''
        self.tx_fifo += data

    def tx_flush(self):
        ''' send transmit queue and clears it'''
        self.tx_fifo()

    def tx_get(self, size: int = None) -> bytearray:
        '''removes size numbers of bytes and return them'''
        return self.tx_fifo.get(size)

    def tx_peek(self, size: int = None) -> bytearray:
        '''returns size numbers of byte without removing them'''
        return self.tx_fifo.peek(size)

    def tx_log(self, level, info):
        ''' log the transmit queue'''
        self.tx_fifo.logging(level, info)

    def tx_clear(self):
        ''' clear transmit queue'''
        self.tx_fifo.clear()

    def tx_len(self):
        ''' get numner of bytes in the transmit queue'''
        return len(self.tx_fifo)

    def fwd_add(self, data: bytearray):
        ''' add data to forward queue'''
        self.fwd_fifo += data

    def fwd_flush(self):
        ''' send forward queue and clears it'''
        self.fwd_fifo()

    def fwd_log(self, level, info):
        ''' log the forward queue'''
        self.fwd_fifo.logging(level, info)

    def fwd_clear(self):
        ''' clear forward queue'''
        self.fwd_fifo.clear()

    def rx_get(self, size: int = None) -> bytearray:
        '''removes size numbers of bytes and return them'''
        return self.rx_fifo.get(size)

    def rx_peek(self, size: int = None) -> bytearray:
        '''returns size numbers of byte without removing them'''
        return self.rx_fifo.peek(size)

    def rx_log(self, level, info):
        ''' logs the receive queue'''
        self.rx_fifo.logging(level, info)

    def rx_clear(self):
        ''' clear receive queue'''
        self.rx_fifo.clear()

    def rx_len(self):
        ''' get numner of bytes in the receive queue'''
        return len(self.rx_fifo)

    def rx_set_cb(self, callback):
        self.rx_fifo.reg_trigger(callback)

    def prot_set_timeout_cb(self, callback):
        self.timeout_cb = callback

    def prot_set_init_new_client_conn_cb(self, callback):
        self.init_new_client_conn_cb = callback

    def prot_set_update_header_cb(self, callback):
        self.update_header_cb = callback


class StreamPtr():
    '''Descr StreamPtr'''
    def __init__(self, _stream, _ifc=None):
        self.stream = _stream
        self.ifc = _ifc

    def __str__(self) -> str:
        return f'ifc:{self._ifc}, stream: {self._stream}'

    @property
    def ifc(self):
        return self._ifc

    @ifc.setter
    def ifc(self, value):
        self._ifc = value

    @property
    def stream(self):
        return self._stream

    @stream.setter
    def stream(self, value):
        self._stream = value


class AsyncStream(AsyncIfcImpl):
    MAX_PROC_TIME = 2
    '''maximum processing time for a received msg in sec'''
    MAX_START_TIME = 400
    '''maximum time without a received msg in sec'''
    MAX_INV_IDLE_TIME = 120
    '''maximum time without a received msg from the inverter in sec'''
    MAX_DEF_IDLE_TIME = 360
    '''maximum default time without a received msg in sec'''

    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 rstream: "StreamPtr") -> None:
        AsyncIfcImpl.__init__(self)

        logger.debug('AsyncStream.__init__')

        self.remote = rstream
        self.tx_fifo.reg_trigger(self.__write_cb)
        self._reader = reader
        self._writer = writer
        self.r_addr = writer.get_extra_info('peername')
        self.l_addr = writer.get_extra_info('sockname')
        self.proc_start = None  # start processing start timestamp
        self.proc_max = 0
        self.async_publ_mqtt = None  # will be set AsyncStreamServer only

    def __write_cb(self):
        self._writer.write(self.tx_fifo.get())

    def __timeout(self) -> int:
        if self.timeout_cb is callable:
            return self.timeout_cb
        return 360

    async def loop(self) -> Self:
        """Async loop handler for precessing all received messages"""
        self.proc_start = time.time()
        while True:
            try:
                proc = time.time() - self.proc_start
                if proc > self.proc_max:
                    self.proc_max = proc
                self.proc_start = None
                dead_conn_to = self.__timeout()
                await asyncio.wait_for(self.__async_read(),
                                       dead_conn_to)

                await self.__async_write()
                await self.__async_forward()
                if self.async_publ_mqtt:
                    await self.async_publ_mqtt()

            except asyncio.TimeoutError:
                logger.warning(f'[{self.node_id}:{self.conn_no}] Dead '
                               f'connection timeout ({dead_conn_to}s) '
                               f'for {self.l_addr}')
                await self.disc()
                return self

            except OSError as error:
                logger.error(f'[{self.node_id}:{self.conn_no}] '
                             f'{error} for l{self.l_addr} | '
                             f'r{self.r_addr}')
                await self.disc()
                return self

            except RuntimeError as error:
                logger.info(f'[{self.node_id}:{self.conn_no}] '
                            f'{error} for {self.l_addr}')
                await self.disc()
                return self

            except Exception:
                Infos.inc_counter('SW_Exception')
                logger.error(
                    f"Exception for {self.r_addr}:\n"
                    f"{traceback.format_exc()}")
            await asyncio.sleep(0)  # be cooperative to other task

    async def disc(self) -> None:
        """Async disc handler for graceful disconnect"""
        self.remote = None
        if self._writer.is_closing():
            return
        logger.debug(f'AsyncStream.disc() l{self.l_addr} | r{self.r_addr}')
        self._writer.close()
        await self._writer.wait_closed()

    def close(self) -> None:
        logging.debug(f'AsyncStream.close() l{self.l_addr} | r{self.r_addr}')
        """close handler for a no waiting disconnect

           hint: must be called before releasing the connection instance
        """
        super().close()
        self._reader.feed_eof()          # abort awaited read
        if self._writer.is_closing():
            return
        self._writer.close()

    def healthy(self) -> bool:
        elapsed = 0
        if self.proc_start is not None:
            elapsed = time.time() - self.proc_start
        if elapsed > self.MAX_PROC_TIME:
            logging.debug(f'[{self.node_id}:{self.conn_no}:'
                          f'{type(self).__name__}]'
                          f' act:{round(1000*elapsed)}ms'
                          f' max:{round(1000*self.proc_max)}ms')
            logging.debug(f'Healthy()) refs: {gc.get_referrers(self)}')
        return elapsed < 5

    '''
    Our private methods
    '''
    async def __async_read(self) -> None:
        """Async read handler to read received data from TCP stream"""
        data = await self._reader.read(4096)
        if data:
            self.proc_start = time.time()
            self.rx_fifo += data
            wait = self.rx_fifo()                # call read in parent class
            if wait > 0:
                await asyncio.sleep(wait)
        else:
            raise RuntimeError("Peer closed.")

    async def __async_write(self, headline: str = 'Transmit to ') -> None:
        """Async write handler to transmit the send_buffer"""
        if len(self.tx_fifo) > 0:
            self.tx_fifo.logging(logging.INFO, f'{headline}{self.r_addr}:')
            self._writer.write(self.tx_fifo.get())
            await self._writer.drain()

    async def __async_forward(self) -> None:
        """forward handler transmits data over the remote connection"""
        if len(self.fwd_fifo) == 0:
            return
        try:
            await self._async_forward()

        except OSError as error:
            if self.remote.stream:
                rmt = self.remote
                logger.error(f'[{rmt.stream.node_id}:{rmt.stream.conn_no}] '
                             f'Fwd: {error} for '
                             f'l{rmt.ifc.l_addr} | r{rmt.ifc.r_addr}')
                await rmt.ifc.disc()
                if rmt.ifc.close_cb:
                    rmt.ifc.close_cb()

        except RuntimeError as error:
            if self.remote.stream:
                rmt = self.remote
                logger.info(f'[{rmt.stream.node_id}:{rmt.stream.conn_no}] '
                            f'Fwd: {error} for {rmt.ifc.l_addr}')
                await rmt.ifc.disc()
                if rmt.ifc.close_cb:
                    rmt.ifc.close_cb()

        except Exception:
            Infos.inc_counter('SW_Exception')
            logger.error(
                f"Fwd Exception for {self.r_addr}:\n"
                f"{traceback.format_exc()}")

    def __del__(self):
        logger.info(
            f"AsyncStream.__del__  l{self.l_addr} | r{self.r_addr}")


class AsyncStreamServer(AsyncStream):
    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 async_publ_mqtt, create_remote,
                 rstream: "StreamPtr") -> None:
        AsyncStream.__init__(self, reader, writer, rstream)
        self.create_remote = create_remote
        self.async_publ_mqtt = async_publ_mqtt

    def close(self) -> None:
        logging.debug('AsyncStreamServer.close()')
        self.create_remote = None
        self.async_publ_mqtt = None
        super().close()

    async def server_loop(self) -> None:
        '''Loop for receiving messages from the inverter (server-side)'''
        logger.info(f'[{self.node_id}:{self.conn_no}] '
                    f'Accept connection from {self.r_addr}')
        Infos.inc_counter('Inverter_Cnt')
        await self.publish_outstanding_mqtugt()
        await self.loop()
        Infos.dec_counter('Inverter_Cnt')
        await self.publish_outstanding_mqtt()
        logger.info(f'[{self.node_id}:{self.conn_no}] Server loop stopped for'
                    f' r{self.r_addr}')

        # if the server connection closes, we also have to disconnect
        # the connection to te TSUN cloud
        if self.remote and self.remote.stream:
            logger.info(f'[{self.node_id}:{self.conn_no}] disc client '
                        f'connection: [{self.remote.ifc.node_id}:'
                        f'{self.remote.ifc.conn_no}]')
            await self.remote.ifc.disc()

    async def _async_forward(self) -> None:
        """forward handler transmits data over the remote connection"""
        if not self.remote.stream:
            await self.create_remote()
            if self.remote.stream and \
               self.remote.ifc.init_new_client_conn_cb():
                await self.remote.ifc._AsyncStream__async_write()
        if self.remote.stream:
            self.remote.ifc.update_header_cb(self.fwd_fifo.peek())
            self.fwd_fifo.logging(logging.INFO, 'Forward to '
                                  f'{self.remote.ifc.r_addr}:')
            self.remote.ifc._writer.write(self.fwd_fifo.get())
            await self.remote.ifc._writer.drain()

    async def publish_outstanding_mqtt(self):
        '''Publish all outstanding MQTT topics'''
        try:
            await self.async_publ_mqtt()
            await Proxy._async_publ_mqtt_proxy_stat('proxy')
        except Exception:
            pass


class AsyncStreamClient(AsyncStream):
    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 rstream: "StreamPtr", close_cb) -> None:
        AsyncStream.__init__(self, reader, writer, rstream)
        self.close_cb = close_cb

    def close(self) -> None:
        logging.debug('AsyncStreamClient.close()')
        self.close_cb = None
        super().close()

    async def client_loop(self, _: str) -> None:
        '''Loop for receiving messages from the TSUN cloud (client-side)'''
        await self.loop()
        logger.info(f'[{self.node_id}:{self.conn_no}] '
                    'Client loop stopped for'
                    f' l{self.l_addr}')

        if self.close_cb:
            self.close_cb()

    async def _async_forward(self) -> None:
        """forward handler transmits data over the remote connection"""
        if self.remote.stream:
            self.remote.ifc.update_header_cb(self.fwd_fifo.peek())
            self.fwd_fifo.logging(logging.INFO, 'Forward to '
                                  f'{self.remote.ifc.r_addr}:')
            self.remote.ifc._writer.write(self.fwd_fifo.get())
            await self.remote.ifc._writer.drain()
