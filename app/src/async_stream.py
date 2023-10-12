import logging, traceback
from config import Config
#import gc
from messages import Message, hex_dump_memory

logger = logging.getLogger('conn')

class AsyncStream(Message):

    def __init__(self, reader, writer, addr, remote_stream, server_side: bool) -> None:
        super().__init__()
        self.reader = reader
        self.writer = writer
        self.remoteStream = remote_stream
        self.server_side = server_side
        self.addr = addr
        
    '''
    Our puplic methods
    '''
    async def loop(self) -> None:
        
        while True:
            try:
                await self.__async_read()     
                            
                if self.unique_id: 
                    await self.__async_write()     
                    await self.__async_forward()
                    await self.async_publ_mqtt()
                
      
            except (ConnectionResetError,
                    ConnectionAbortedError,
                    RuntimeError) as error:
                logger.warning(f'In loop for {self.addr}: {error}')
                self.close()
                return
            except Exception:
                logger.error(
                    f"Exception for {self.addr}:\n"
                    f"{traceback.format_exc()}")
                self.close()
                return
            
    def disc(self) -> None:
        logger.debug(f'in AsyncStream.disc() {self.addr}')
        self.writer.close()
            
        
    def close(self):
        logger.debug(f'in AsyncStream.close() {self.addr}')
        self.writer.close()
        super().close()         # call close handler in the parent class

#        logger.info (f'AsyncStream refs: {gc.get_referrers(self)}')

    
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
            
    async def __async_write(self) -> None:
        if self._send_buffer:
            hex_dump_memory(logging.INFO, f'Transmit to {self.addr}:', self._send_buffer, len(self._send_buffer))
            self.writer.write(self._send_buffer)
            await self.writer.drain()
            self._send_buffer = bytearray(0)  #self._send_buffer[sent:]
            
    async def __async_forward(self) -> None:
        if self._forward_buffer:
            if not self.remoteStream:
                await self.async_create_remote()  # only implmeneted for server side => syncServerStream
                
            if self.remoteStream:
                hex_dump_memory(logging.DEBUG, f'Forward to {self.remoteStream.addr}:', self._forward_buffer, len(self._forward_buffer))
                self.remoteStream.writer.write (self._forward_buffer)
                await self.remoteStream.writer.drain()                    
                self._forward_buffer = bytearray(0)

    async def async_create_remote(self) -> None:
        pass

    async def async_publ_mqtt(self) -> None:
        pass       


    def __del__ (self):
        logging.debug (f"AsyncStream.__del__  {self.addr}")     


