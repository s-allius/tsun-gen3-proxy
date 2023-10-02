import logging, traceback, json
#import gc, ctypes
from config import Config
from messages import Message, hex_dump_memory
from mqtt import Mqtt

logger = logging.getLogger('conn')

#def ref_count(address):
#    return ctypes.c_long.from_address(address).value

class AsyncStream(Message):

    def __init__(self, proxy, reader, writer, addr, weak_stream=None, server_side=True):
        logger.debug (f"AsyncStream __init__ {self}")       

        super().__init__()
        self.proxy  = proxy
        self.reader = reader
        self.writer = writer
        self.__WkRemoteStream = weak_stream
        self.addr = addr
        self.server_side = server_side
        self.mqtt = Mqtt()
        self.unique_id = 0
        self.node_id = ''
        
    '''
    Our puplic methods
    '''
    def set_serial_no(self, serial_no : str):
        logger.debug(f'SerialNo: {serial_no}')
       
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
            
            
    async def register_home_assistant(self):        
            
            if self.server_side:
                try:
                    for data_json, component, id in self.db.ha_confs(self.entitiy_prfx + self.node_id, self.unique_id, self.sug_area):
                            logger.debug(f'Register MQTT: {data_json}')                                
                            await self.mqtt.publish(f"{self.discovery_prfx}{component}/{self.node_id}{id}/config", data_json)
    
                except Exception:
                    logging.error(
                        f"Proxy: Exception:\n"
                        f"{traceback.format_exc()}")

    
    async def loop(self) -> None:
        
        while True:
            try:
                await self.__async_read()     
                
                if self.id_str:
                    self.set_serial_no(self.id_str.decode("utf-8"))
            
                if self.unique_id: 
                    await self.__async_write()     
                    await self.__async_forward()
                    await self.__async_publ_mqtt()
                
      
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
            
        
    def close(self) -> None:
        logger.debug(f'in AsyncStream.close() {self.addr}')
        super().close()
        self.writer.close()
        del self.proxy
        
        #logger.info (f'refcount: {ref_count(id (self))}') 
        #logger.info (f'AsyncStream refs: {gc.get_referrers(self)}')

    
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
            if not self.__WkRemoteStream:
                tsun = Config.get('tsun')
                self.__WkRemoteStream = await self.proxy.CreateClientStream (tsun['host'], tsun['port'])
                
            if self.__WkRemoteStream:
                remoteStream = self.__WkRemoteStream()
                if remoteStream:
                    hex_dump_memory(logging.DEBUG, f'Forward to {remoteStream.addr}:', self._forward_buffer, len(self._forward_buffer))
                    remoteStream.writer.write (self._forward_buffer)
                    await remoteStream.writer.drain()                    
                    self._forward_buffer = bytearray(0)

    async def __async_publ_mqtt(self) -> None:
        if self.server_side:
            db = self.db.db

            # check if new inverter or collector infos are available or when the home assistant has changed the status back to online
            if (self.new_data.keys() & {'inverter', 'collector'}) or self.mqtt.home_assistant_restarted:
                await self.register_home_assistant()
                self.mqtt.home_assistant_restarted = False # clear flag

            for key in self.new_data:
                if self.new_data[key] and key in db:
                    data_json = json.dumps(db[key])
                    #logger.info(f'MQTT publish {key}: {data_json}')
                    await self.mqtt.publish(f"{self.entitiy_prfx}{self.node_id}{key}", data_json)
                    self.new_data[key] = False

    def __del__ (self):
        logger.debug ("AsyncStream __del__")       
        super().__del__()    

