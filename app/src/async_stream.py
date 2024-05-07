import logging
import traceback
from messages import hex_dump_memory

logger = logging.getLogger('conn')


class AsyncStream():

    def __init__(self, reader, writer, addr) -> None:
        logger.debug('AsyncStream.__init__')
        self.reader = reader
        self.writer = writer
        self.addr = addr
        self.r_addr = ''
        self.l_addr = ''

    async def server_loop(self, addr):
        '''Loop for receiving messages from the inverter (server-side)'''
        logging.info(f'Accept connection from  {addr}')
        self.inc_counter('Inverter_Cnt')
        await self.loop()
        self.dec_counter('Inverter_Cnt')
        logging.info(f'Server loop stopped for r{self.r_addr}')

        # if the server connection closes, we also have to disconnect
        # the connection to te TSUN cloud
        if self.remoteStream:
            logging.debug("disconnect client connection")
            self.remoteStream.disc()
        try:
            await self._async_publ_mqtt_proxy_stat('proxy')
        except Exception:
            pass

    async def client_loop(self, addr):
        '''Loop for receiving messages from the TSUN cloud (client-side)'''
        clientStream = await self.remoteStream.loop()
        logging.info(f'Client loop stopped for l{clientStream.l_addr}')

        # if the client connection closes, we don't touch the server
        # connection. Instead we erase the client connection stream,
        # thus on the next received packet from the inverter, we can
        # establish a new connection to the TSUN cloud

        # erase backlink to inverter
        clientStream.remoteStream = None

        if self.remoteStream == clientStream:
            # logging.debug(f'Client l{clientStream.l_addr} refs:'
            #               f' {gc.get_referrers(clientStream)}')
            # than erase client connection
            self.remoteStream = None

    async def loop(self):
        self.r_addr = self.writer.get_extra_info('peername')
        self.l_addr = self.writer.get_extra_info('sockname')

        while True:
            try:
                await self.__async_read()

                if self.unique_id:
                    await self.async_write()
                    await self.__async_forward()
                    await self.async_publ_mqtt()

            except (ConnectionResetError,
                    ConnectionAbortedError,
                    BrokenPipeError,
                    RuntimeError) as error:
                logger.warning(f'In loop for l{self.l_addr} | '
                               f'r{self.r_addr}: {error}')
                self.close()
                return self
            except Exception:
                self.inc_counter('SW_Exception')
                logger.error(
                    f"Exception for {self.addr}:\n"
                    f"{traceback.format_exc()}")
                self.close()
                return self

    def disc(self) -> None:
        logger.debug(f'AsyncStream.disc() l{self.l_addr} | r{self.r_addr}')
        self.writer.close()

    def close(self):
        logger.debug(f'AsyncStream.close() l{self.l_addr} | r{self.r_addr}')
        self.writer.close()

    '''
    Our private methods
    '''
    async def __async_read(self) -> None:
        data = await self.reader.read(4096)
        if data:
            self._recv_buffer += data
            self.read()                # call read in parent class
        else:
            raise RuntimeError("Peer closed.")

    async def async_write(self, headline='Transmit to ') -> None:
        if self._send_buffer:
            hex_dump_memory(logging.INFO, f'{headline}{self.addr}:',
                            self._send_buffer, len(self._send_buffer))
            self.writer.write(self._send_buffer)
            await self.writer.drain()
            self._send_buffer = bytearray(0)  # self._send_buffer[sent:]

    async def __async_forward(self) -> None:
        if self._forward_buffer:
            if not self.remoteStream:
                await self.async_create_remote()
                if self.remoteStream:
                    if self.remoteStream._init_new_client_conn():
                        await self.remoteStream.async_write()

            if self.remoteStream:
                self.remoteStream._update_header(self._forward_buffer)
                hex_dump_memory(logging.INFO,
                                f'Forward to {self.remoteStream.addr}:',
                                self._forward_buffer,
                                len(self._forward_buffer))
                self.remoteStream.writer.write(self._forward_buffer)
                await self.remoteStream.writer.drain()
                self._forward_buffer = bytearray(0)

    def __del__(self):
        logger.debug(
            f"AsyncStream.__del__  l{self.l_addr} | r{self.r_addr}")
