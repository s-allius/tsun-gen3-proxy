import logging, traceback
from config import Config
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
        self.unique_id = 0
        self.node_id = ''
        
    '''
    Our puplic methods
    '''
    def set_serial_no(self, serial_no : str):
        logger.info(f'SerialNo: {serial_no}')
       
        if self.unique_id != serial_no: 
       
            inverters = Config.get('inverters')
            #logger.debug(f'Inverters: {inverters}')
                
            if serial_no in inverters:
                logger.debug(f'SerialNo {serial_no} allowed!')
                inv = inverters[serial_no]
                self.node_id = inv['node_id']
                self.sug_area    = inv['suggested_area']
            else:    
                logger.debug(f'SerialNo {serial_no} not known!')
                self.node_id = ''
                self.sug_area    = ''
                if not inverters['allow_all']:
                    self.unique_id = None
            
                    logger.error('ignore message from unknow inverter!')
                    return

            self.unique_id = serial_no
            
            ha = Config.get('ha')
            self.entitiy_prfx = ha['entity_prefix'] + '/'
            self.discovery_prfx = ha['discovery_prefix'] + '/'
            
            

    
    async def loop(self) -> None:
        
        while True:
            try:
                await self.__async_read()     
                
                if self.id_str:
                    self.set_serial_no(self.id_str.decode("utf-8"))
            
                if self.unique_id: 
                    await self.__async_write()     
                    await self.__async_forward()
                    await self.async_publ_mqtt()
                
      
            except (ConnectionResetError,
                    ConnectionAbortedError,
                    RuntimeError) as error:
                logger.error(f'In loop for {self.addr}: {error}')
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

        if self.remoteStream:   # if we have knowledge about a remote stream, we del the references between the two streams
            self.remoteStream.remoteStream = None
            self.remoteStream = None

    
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
        logger.debug ("AsyncStream __del__")     
        super().__del__()  


