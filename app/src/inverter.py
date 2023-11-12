import asyncio
import logging
import traceback
import json
from config import Config
from async_stream import AsyncStream
from mqtt import Mqtt
from aiomqtt import MqttCodeError
from infos import Infos

# import gc

# logger = logging.getLogger('conn')
logger_mqtt = logging.getLogger('mqtt')


class Inverter(AsyncStream):
    '''class Inverter is a derivation of an Async_Stream

    The class has some class method for managing common resources like a
    connection to the MQTT broker or proxy error counter which are common
    for all inverter connection

    Instances of the class are connections to an inverter and can have an
    optional link to an remote connection to the TSUN cloud. A remote
    connection dies with the inverter connection.

    class methods:
        class_init():  initialize the common resources of the proxy (MQTT
                       broker, Proxy DB, etc). Must be called before the
                       first Ib´verter instance can be created
        class_close(): release the common resources of the proxy. Should not
                       be called before any instances of the class are
                       destroyed

    methods:
        server_loop(addr): Async loop method for receiving messages from the
                           inverter (server-side)
        client_loop(addr): Async loop method for receiving messages from the
                           TSUN cloud (client-side)
        async_create_remote(): Establish a client connection to the TSUN cloud
        async_publ_mqtt(): Publish data to MQTT broker
        close(): Release method which must be called before a instance can be
                 destroyed
    '''
    @classmethod
    def class_init(cls) -> None:
        logging.debug('Inverter.class_init')
        # initialize the proxy statistics
        Infos.static_init()
        cls.db_stat = Infos()

        ha = Config.get('ha')
        cls.entity_prfx = ha['entity_prefix'] + '/'
        cls.discovery_prfx = ha['discovery_prefix'] + '/'
        cls.proxy_node_id = ha['proxy_node_id'] + '/'
        cls.proxy_unique_id = ha['proxy_unique_id']

        # call Mqtt singleton to establisch the connection to the mqtt broker
        cls.mqtt = Mqtt(cls.__cb_mqtt_is_up)

    @classmethod
    async def __cb_mqtt_is_up(cls) -> None:
        logging.info('Initialize proxy device on home assistant')
        # register proxy status counters at home assistant
        await cls.__register_proxy_stat_home_assistant()

        # send values of the proxy status counters
        await asyncio.sleep(0.5)            # wait a bit, before sending data
        cls.new_stat_data['proxy'] = True   # force sending data to sync ha
        await cls.__async_publ_mqtt_proxy_stat('proxy')

    @classmethod
    async def __register_proxy_stat_home_assistant(cls) -> None:
        '''register all our topics at home assistant'''
        for data_json, component, node_id, id in cls.db_stat.ha_confs(
                 cls.entity_prfx, cls.proxy_node_id,
                 cls.proxy_unique_id, True):
            logger_mqtt.debug(f"MQTT Register: cmp:'{component}' node_id:'{node_id}' {data_json}")      # noqa: E501
            await cls.mqtt.publish(f'{cls.discovery_prfx}{component}/{node_id}{id}/config', data_json)  # noqa: E501

    @classmethod
    async def __async_publ_mqtt_proxy_stat(cls, key) -> None:
        stat = Infos.stat
        if key in stat and cls.new_stat_data[key]:
            data_json = json.dumps(stat[key])
            node_id = cls.proxy_node_id
            logger_mqtt.debug(f'{key}: {data_json}')
            await cls.mqtt.publish(f"{cls.entity_prfx}{node_id}{key}",
                                   data_json)
            cls.new_stat_data[key] = False

    @classmethod
    def class_close(cls, loop) -> None:
        logging.debug('Inverter.class_close')
        logging.info('Close MQTT Task')
        loop.run_until_complete(cls.mqtt.close())
        cls.mqtt = None

    def __init__(self, reader, writer, addr):
        super().__init__(reader, writer, addr, None, True)
        self.ha_restarts = -1

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
            await self.__async_publ_mqtt_proxy_stat('proxy')
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
            self.remoteStream = AsyncStream(reader, writer, addr, self,
                                            False, self.id_str)
            asyncio.create_task(self.client_loop(addr))

        except ConnectionRefusedError as error:
            logging.info(f'{error}')
        except Exception:
            logging.error(
                f"Inverter: Exception for {addr}:\n"
                f"{traceback.format_exc()}")

    async def async_publ_mqtt(self) -> None:
        '''publish data to MQTT broker'''
        # check if new inverter or collector infos are available or when the
        #  home assistant has changed the status back to online
        try:
            if (('inverter' in self.new_data and self.new_data['inverter'])
                    or ('collector' in self.new_data and
                        self.new_data['collector'])
                    or self.mqtt.ha_restarts != self.ha_restarts):
                await self.__register_proxy_stat_home_assistant()
                await self.__register_home_assistant()
                self.ha_restarts = self.mqtt.ha_restarts

            for key in self.new_data:
                await self.__async_publ_mqtt_packet(key)
            for key in self.new_stat_data:
                await self.__async_publ_mqtt_proxy_stat(key)

        except MqttCodeError as error:
            logging.error(f'Mqtt except: {error}')
        except Exception:
            logging.error(
                f"Inverter: Exception:\n"
                f"{traceback.format_exc()}")

    async def __async_publ_mqtt_packet(self, key):
        db = self.db.db
        if key in db and self.new_data[key]:
            data_json = json.dumps(db[key])
            node_id = self.node_id
            logger_mqtt.debug(f'{key}: {data_json}')
            await self.mqtt.publish(f'{self.entity_prfx}{node_id}{key}', data_json)  # noqa: E501
            self.new_data[key] = False

    async def __register_home_assistant(self) -> None:
        '''register all our topics at home assistant'''
        for data_json, component, node_id, id in self.db.ha_confs(
                self.entity_prfx, self.node_id, self.unique_id,
                False, self.sug_area):
            logger_mqtt.debug(f"MQTT Register: cmp:'{component}'"
                              f" node_id:'{node_id}' {data_json}")
            await self.mqtt.publish(f"{self.discovery_prfx}{component}"
                                    f"/{node_id}{id}/config", data_json)

    def close(self) -> None:
        logging.debug(f'Inverter.close() l{self.l_addr} | r{self.r_addr}')
        super().close()         # call close handler in the parent class
#        logger.debug (f'Inverter refs: {gc.get_referrers(self)}')

    def __del__(self):
        logging.debug("Inverter.__del__")
        super().__del__()
