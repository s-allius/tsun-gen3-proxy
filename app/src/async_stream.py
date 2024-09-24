import asyncio
import logging
import traceback
import time
from asyncio import StreamReader, StreamWriter
from typing import Self
from itertools import count

if __name__ == "app.src.async_stream":
    from app.src.byte_fifo import ByteFifo
    from app.src.async_ifc import AsyncIfc
    from app.src.infos import Infos
else:  # pragma: no cover
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


class StreamPtr():
    def __init__(self, stream):
        self.stream = stream


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
                 addr, async_publ_mqtt, async_create_remote,
                 rstream: "StreamPtr") -> None:
        AsyncIfcImpl.__init__(self)

        logger.debug('AsyncStream.__init__')

        self.remote = rstream
        self.tx_fifo.reg_trigger(self.__write_cb)
        self.async_create_remote = async_create_remote
        self._reader = reader
        self._writer = writer
        self.addr = addr
        self.r_addr = ''
        self.l_addr = ''
        self.proc_start = None  # start processing start timestamp
        self.proc_max = 0
        self.async_publ_mqtt = async_publ_mqtt

    def __write_cb(self):
        self._writer.write(self.tx_fifo.get())

    def __timeout(self) -> int:
        if self.timeout_cb is callable:
            return self.timeout_cb
        return 360

    async def publish_outstanding_mqtt(self):
        '''Publish all outstanding MQTT topics'''
        try:
            if self.unique_id:
                await self.async_publ_mqtt()
            await self._async_publ_mqtt_proxy_stat('proxy')
        except Exception:
            pass

    async def server_loop(self, addr: str) -> None:
        '''Loop for receiving messages from the inverter (server-side)'''
        logger.info(f'[{self.node_id}:{self.conn_no}] '
                    f'Accept connection from {addr}')
        Infos.inc_counter('Inverter_Cnt')
        await self.publish_outstanding_mqtt()
        await self.loop()
        Infos.dec_counter('Inverter_Cnt')
        await self.publish_outstanding_mqtt()
        logger.info(f'[{self.node_id}:{self.conn_no}] Server loop stopped for'
                    f' r{self.r_addr}')

        # if the server connection closes, we also have to disconnect
        # the connection to te TSUN cloud
        if self.remote.stream:
            logger.info(f'[{self.node_id}:{self.conn_no}] disc client '
                        f'connection: [{self.remote.stream.node_id}:'
                        f'{self.remote.stream.conn_no}]')
            await self.remote.stream._ifc.disc()

    async def client_loop(self, _: str) -> None:
        '''Loop for receiving messages from the TSUN cloud (client-side)'''
        client_stream = await self.remote.stream._ifc.loop()
        logger.info(f'[{client_stream.node_id}:{client_stream.conn_no}] '
                    'Client loop stopped for'
                    f' l{client_stream.l_addr}')

        # if the client connection closes, we don't touch the server
        # connection. Instead we erase the client connection stream,
        # thus on the next received packet from the inverter, we can
        # establish a new connection to the TSUN cloud

        # erase backlink to inverter
        client_stream.remote.stream = None

        if self.remote.stream == client_stream:
            # logging.debug(f'Client l{client_stream.l_addr} refs:'
            #               f' {gc.get_referrers(client_stream)}')
            # than erase client connection
            self.remote.stream = None

    async def loop(self) -> Self:
        """Async loop handler for precessing all received messages"""
        self.r_addr = self._writer.get_extra_info('peername')
        self.l_addr = self._writer.get_extra_info('sockname')
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

                # if self.unique_id:
                await self.__async_write()
                await self.__async_forward()
                await self.async_publ_mqtt()

            except asyncio.TimeoutError:
                logger.warning(f'[{self.node_id}:{self.conn_no}] Dead '
                               f'connection timeout ({dead_conn_to}s) '
                               f'for {self.l_addr}')
                await self.disc()
                self.close()
                return self

            except OSError as error:
                logger.error(f'[{self.node_id}:{self.conn_no}] '
                             f'{error} for l{self.l_addr} | '
                             f'r{self.r_addr}')
                await self.disc()
                self.close()
                return self

            except RuntimeError as error:
                logger.info(f'[{self.node_id}:{self.conn_no}] '
                            f'{error} for {self.l_addr}')
                await self.disc()
                self.close()
                return self

            except Exception:
                Infos.inc_counter('SW_Exception')
                logger.error(
                    f"Exception for {self.addr}:\n"
                    f"{traceback.format_exc()}")
            await asyncio.sleep(0)  # be cooperative to other task

    async def __async_write(self, headline: str = 'Transmit to ') -> None:
        """Async write handler to transmit the send_buffer"""
        if len(self.tx_fifo) > 0:
            self.tx_fifo.logging(logging.INFO, f'{headline}{self.addr}:')
            self._writer.write(self.tx_fifo.get())
            await self._writer.drain()

    async def disc(self) -> None:
        """Async disc handler for graceful disconnect"""
        if self._writer.is_closing():
            return
        logger.debug(f'AsyncStream.disc() l{self.l_addr} | r{self.r_addr}')
        self._writer.close()
        await self._writer.wait_closed()

    def close(self) -> None:
        """close handler for a no waiting disconnect

           hint: must be called before releasing the connection instance
        """
        self.tx_fifo.reg_trigger(None)
        self.async_create_remote = None
        self._reader.feed_eof()          # abort awaited read
        if self._writer.is_closing():
            return
        logger.debug(f'AsyncStream.close() l{self.l_addr} | r{self.r_addr}')
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

    async def __async_forward(self) -> None:
        """forward handler transmits data over the remote connection"""
        if len(self.fwd_fifo) == 0:
            return
        try:
            if not self.remote.stream:
                await self.async_create_remote()
                if self.remote.stream:
                    if self.remote.stream._init_new_client_conn():
                        await self.remote.stream._ifc.__async_write()

            if self.remote.stream:
                self.remote.stream._update_header(self.fwd_fifo.peek())
                self.fwd_fifo.logging(logging.INFO, 'Forward to '
                                      f'{self.remote.stream.addr}:')
                self.remote.stream._ifc._writer.write(self.fwd_fifo.get())
                await self.remote.stream._ifc._writer.drain()

        except OSError as error:
            if self.remote.stream:
                rmt = self.remote.stream
                self.remote.stream = None
                logger.error(f'[{rmt.node_id}:{rmt.conn_no}] Fwd: {error} for '
                             f'l{rmt._ifc.l_addr} | r{rmt._ifc.r_addr}')
                await rmt._ifc.disc()
                rmt._ifc.close()

        except RuntimeError as error:
            if self.remote.stream:
                rmt = self.remote.stream
                self.remote.stream = None
                logger.info(f'[{rmt.node_id}:{rmt.conn_no}] '
                            f'Fwd: {error} for {rmt._ifc.l_addr}')
                await rmt._ifc.disc()
                rmt._ifc.close()

        except Exception:
            Infos.inc_counter('SW_Exception')
            logger.error(
                f"Fwd Exception for {self.addr}:\n"
                f"{traceback.format_exc()}")

    def __del__(self):
        logger.debug(
            f"AsyncStream.__del__  l{self.l_addr} | r{self.r_addr}")
