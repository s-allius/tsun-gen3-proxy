import asyncio
import logging
import traceback
import json
from config import Config
from inverter import Inverter
from gen3plus.async_stream_g3p import AsyncStreamG3P
from aiomqtt import MqttCodeError
from infos import Infos

# import gc

# logger = logging.getLogger('conn')
logger_mqtt = logging.getLogger('mqtt')


class InverterG3P(Inverter, AsyncStreamG3P):
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
                       first inverter instance can be created
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

    def __init__(self, reader, writer, addr):
        super().__init__(reader, writer, addr, None, True)
        self.ha_restarts = -1

    async def async_create_remote(self) -> None:
        '''Establish a client connection to the TSUN cloud'''
        tsun = Config.get('solarman')
        host = tsun['host']
        port = tsun['port']
        addr = (host, port)

        try:
            logging.info(f'Connected to {addr}')
            connect = asyncio.open_connection(host, port)
            reader, writer = await connect
            self.remoteStream = AsyncStreamG3P(reader, writer, addr, self,
                                               False)
            asyncio.create_task(self.client_loop(addr))

        except (ConnectionRefusedError, TimeoutError) as error:
            logging.info(f'{error}')
        except Exception:
            self.inc_counter('SW_Exception')
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
                await self._register_proxy_stat_home_assistant()
                await self.__register_home_assistant()
                self.ha_restarts = self.mqtt.ha_restarts

            for key in self.new_data:
                await self.__async_publ_mqtt_packet(key)
            for key in Infos.new_stat_data:
                await self._async_publ_mqtt_proxy_stat(key)

        except MqttCodeError as error:
            logging.error(f'Mqtt except: {error}')
        except Exception:
            self.inc_counter('SW_Exception')
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
        logging.debug(f'InverterG3P.close() l{self.l_addr} | r{self.r_addr}')
        super().close()         # call close handler in the parent class
#        logger.debug (f'Inverter refs: {gc.get_referrers(self)}')

    def __del__(self):
        logging.debug("InverterG3P.__del__")
        super().__del__()
