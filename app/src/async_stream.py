import logging, traceback, aiomqtt, json
from config import Config
from messages import Message, hex_dump_memory
from mqtt import Mqtt

logger = logging.getLogger('conn')
logger_mqtt = logging.getLogger('mqtt')

class AsyncStream(Message):

    def __init__(self, proxy, reader, writer, addr, stream=None, server_side=True):
        super().__init__()
        self.proxy  = proxy
        self.reader = reader
        self.writer = writer
        self.remoteStream = stream
        self.addr = addr
        self.server_side = server_side
        self.mqtt = Mqtt()
        self.unique_id = 0
        self.node_id = ''
        
    '''
    Our puplic methods
    '''
    def set_serial_no(self, serial_no : str):
        logger_mqtt.info(f'SerialNo: {serial_no}')
       
        if self.unique_id != serial_no: 
       
            inverters = Config.get('inverters')
            #logger_mqtt.debug(f'Inverters: {inverters}')
                
            if serial_no in inverters:
                logger_mqtt.debug(f'SerialNo {serial_no} allowed!')
                inv = inverters[serial_no]
                self.node_id = inv['node_id']
                self.sug_area    = inv['suggested_area']
            else:    
                logger_mqtt.debug(f'SerialNo {serial_no} not known!')
                self.node_id = ''
                self.sug_area    = ''
                if not inverters['allow_all']:
                    self.unique_id = None
            
                    logger_mqtt.error('ignore message from unknow inverter!')
                    return

            self.unique_id = serial_no
            
            ha = Config.get('ha')
            self.entitiy_prfx = ha['entity_prefix'] + '/'
            self.discovery_prfx = ha['discovery_prefix'] + '/'
            
            
    async def register_home_assistant(self):        
            
            if self.server_side:
                try:
                    for data_json, id in self.db.ha_confs(self.entitiy_prfx + self.node_id, self.unique_id, self.sug_area):
                            logger_mqtt.debug(f'Register: {data_json}')                                
                            await self.mqtt.publish(f"{self.discovery_prfx}sensor/{self.node_id}{id}/config", data_json)
    
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
        
    def close(self):
        logger.info(f'in async_stream.close() {self.addr}')
        self.writer.close()
        self.proxy = None
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
                tsun = Config.get('tsun')
                self.remoteStream = await self.proxy.CreateClientStream (self, tsun['host'], tsun['port'])
                
            if self.remoteStream:
                hex_dump_memory(logging.DEBUG, f'Forward to {self.remoteStream.addr}:', self._forward_buffer, len(self._forward_buffer))
                self.remoteStream.writer.write (self._forward_buffer)
                await self.remoteStream.writer.drain()                    
                self._forward_buffer = bytearray(0)

    async def __async_publ_mqtt(self) -> None:
        if self.server_side:
            db = self.db.db

            if self.new_data.keys() & {'inverter', 'collector'}:
                await self.register_home_assistant()

            for key in self.new_data:
                if self.new_data[key] and key in db:
                    data_json = json.dumps(db[key])
                    logger_mqtt.info(f'{key}: {data_json}')
                    await self.mqtt.publish(f"{self.entitiy_prfx}{self.node_id}{key}", data_json)
                    self.new_data[key] = False

    def __del__ (self):
        logger.debug ("AsyncStream __del__")       
            

