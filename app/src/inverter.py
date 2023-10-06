import asyncio, logging, traceback, json
from config import Config
from async_stream import AsyncStream
from mqtt import Mqtt
#import gc

logger = logging.getLogger('conn')



class Inverter(AsyncStream):

    def __init__ (self, reader, writer, addr):
        super().__init__(reader, writer, addr, None, True)
        self.mqtt = Mqtt()
        self.ha_restarts = 0
        ha = Config.get('ha')
        self.entitiy_prfx = ha['entity_prefix'] + '/'
        self.discovery_prfx = ha['discovery_prefix'] + '/'


    async def server_loop(self, addr):
        '''Loop for receiving messages from the inverter (server-side)'''
        logger.info(f'Accept connection from  {addr}')        
        await self.loop()
        logging.info(f'Server loop stopped for {addr}')
        
        # if the server connection closes, we also have to disconnect the connection to te TSUN cloud
        if self.remoteStream:
            logging.debug ("disconnect client connection")
            self.remoteStream.disc()
        
    async def client_loop(self, addr):
        '''Loop for receiving messages from the TSUN cloud (client-side)'''
        await self.remoteStream.loop()    
        logging.info(f'Client loop stopped for {addr}')

        # if the client connection closes, we don't touch the server connection. Instead we erase the client
        # connection stream, thus on the next received packet from the inverter, we can establish a new connection 
        # to the TSUN cloud
        self.remoteStream.remoteStream = None    # erase backlink to inverter instance
        self.remoteStream = None                 # than erase client connection 
        
    async def async_create_remote(self) -> None:
        '''Establish a client connection to the TSUN cloud'''
        tsun = Config.get('tsun')
        host = tsun['host']
        port = tsun['port']     
        addr = (host, port)
            
        try:
            logging.info(f'Connected to {addr}')
            connect = asyncio.open_connection(host, port)
            reader, writer = await connect    
            self.remoteStream = AsyncStream(reader, writer, addr, self, False)
            asyncio.create_task(self.client_loop(addr))
            
        except ConnectionRefusedError as error:
            logging.info(f'{error}')
        except Exception:
            logging.error(
                f"Inverter: Exception for {addr}:\n"
                f"{traceback.format_exc()}")
        
    

    async def async_publ_mqtt(self) -> None:
        '''puplish data to MQTT broker'''
        db = self.db.db
        # check if new inverter or collector infos are available or when the home assistant has changed the status back to online
        if (('inverter' in self.new_data and self.new_data['inverter']) or 
             ('collector' in self.new_data and self.new_data['collector']) or
               self.mqtt.ha_restarts != self.ha_restarts):
            await self.__register_home_assistant()
            self.ha_restarts = self.mqtt.ha_restarts

        for key in self.new_data:
            if self.new_data[key] and key in db:
                data_json = json.dumps(db[key])
                logger.info(f'{key}: {data_json}')
                await self.mqtt.publish(f"{self.entitiy_prfx}{self.node_id}{key}", data_json)
                self.new_data[key] = False

    async def __register_home_assistant(self) -> None:
        '''register all our topics at home assistant'''
        try:
            for data_json, component, id in self.db.ha_confs(self.entitiy_prfx + self.node_id, self.unique_id, self.sug_area):
                    #logger.debug(f'MQTT Register: {data_json}')                                
                    await self.mqtt.publish(f"{self.discovery_prfx}{component}/{self.node_id}{id}/config", data_json)
        except Exception:
            logging.error(
                f"Inverter: Exception:\n"
                f"{traceback.format_exc()}")
            
    def close(self) -> None:
        logging.debug(f'Inverter.close() {self.addr}')
        super().close()         # call close handler in the parent class
#        logger.debug (f'Inverter refs: {gc.get_referrers(self)}')


    def __del__ (self):
        logging.debug ("Inverter.__del__")
        super().__del__()  
