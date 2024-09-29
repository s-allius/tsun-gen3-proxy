import asyncio
import logging
import traceback
import json
from aiomqtt import MqttCodeError

if __name__ == "app.src.inverter":
    from app.src.config import Config
    from app.src.mqtt import Mqtt
    from app.src.infos import Infos
else:  # pragma: no cover
    from config import Config
    from mqtt import Mqtt
    from infos import Infos

logger_mqtt = logging.getLogger('mqtt')


class Inverter():
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
        cls.mqtt = Mqtt(cls._cb_mqtt_is_up)

        # register all counters which should be reset at midnight.
        # This is needed if the proxy is restated before midnight
        # and the inverters are offline, cause the normal refgistering
        # needs an update on the counters.
        # Without this registration here the counters would not be
        # reset at midnight when you restart the proxy just before
        # midnight!
        inverters = Config.get('inverters')
        # logger.debug(f'Inverters: {inverters}')
        for inv in inverters.values():
            if (type(inv) is dict):
                node_id = inv['node_id']
                cls.db_stat.reg_clr_at_midnight(f'{cls.entity_prfx}{node_id}',
                                                check_dependencies=False)

    @classmethod
    async def _cb_mqtt_is_up(cls) -> None:
        logging.info('Initialize proxy device on home assistant')
        # register proxy status counters at home assistant
        await cls._register_proxy_stat_home_assistant()

        # send values of the proxy status counters
        await asyncio.sleep(0.5)            # wait a bit, before sending data
        Infos.new_stat_data['proxy'] = True   # force sending data to sync ha
        await cls._async_publ_mqtt_proxy_stat('proxy')

    @classmethod
    async def _register_proxy_stat_home_assistant(cls) -> None:
        '''register all our topics at home assistant'''
        for data_json, component, node_id, id in cls.db_stat.ha_proxy_confs(
                 cls.entity_prfx, cls.proxy_node_id, cls.proxy_unique_id):
            logger_mqtt.debug(f"MQTT Register: cmp:'{component}' node_id:'{node_id}' {data_json}")      # noqa: E501
            await cls.mqtt.publish(f'{cls.discovery_prfx}{component}/{node_id}{id}/config', data_json)  # noqa: E501

    @classmethod
    async def _async_publ_mqtt_proxy_stat(cls, key) -> None:
        stat = Infos.stat
        if key in stat and Infos.new_stat_data[key]:
            data_json = json.dumps(stat[key])
            node_id = cls.proxy_node_id
            logger_mqtt.debug(f'{key}: {data_json}')
            await cls.mqtt.publish(f"{cls.entity_prfx}{node_id}{key}",
                                   data_json)
            Infos.new_stat_data[key] = False

    @classmethod
    def class_close(cls, loop) -> None:   # pragma: no cover
        logging.debug('Inverter.class_close')
        logging.info('Close MQTT Task')
        loop.run_until_complete(cls.mqtt.close())
        cls.mqtt = None

    def __init__(self):
        self.__ha_restarts = -1

    async def async_create_remote(self, inv_prot: str, conn_class) -> None:
        '''Establish a client connection to the TSUN cloud'''
        tsun = Config.get(inv_prot)
        host = tsun['host']
        port = tsun['port']
        addr = (host, port)

        try:
            logging.info(f'[{self.node_id}] Connect to {addr}')
            connect = asyncio.open_connection(host, port)
            reader, writer = await connect
            if hasattr(self, 'id_str'):
                self.remote.stream = conn_class(
                    reader, writer, addr, self, self.id_str)
            else:
                self.remote.stream = conn_class(
                    reader, writer, addr, self)

            logging.info(f'[{self.remote.stream.node_id}:'
                         f'{self.remote.stream.conn_no}] '
                         f'Connected to {addr}')
            asyncio.create_task(self.remote.ifc.client_loop(addr))

        except (ConnectionRefusedError, TimeoutError) as error:
            logging.info(f'{error}')
        except Exception:
            self.inc_counter('SW_Exception')
            logging.error(
                f"Inverter: Exception for {addr}:\n"
                f"{traceback.format_exc()}")

    async def async_publ_mqtt(self) -> None:
        '''publish data to MQTT broker'''
        if not self.unique_id:
            return
        # check if new inverter or collector infos are available or when the
        #  home assistant has changed the status back to online
        try:
            if (('inverter' in self.new_data and self.new_data['inverter'])
                    or ('collector' in self.new_data and
                        self.new_data['collector'])
                    or self.mqtt.ha_restarts != self.__ha_restarts):
                await self._register_proxy_stat_home_assistant()
                await self.__register_home_assistant()
                self.__ha_restarts = self.mqtt.ha_restarts

            for key in self.new_data:
                await self.__async_publ_mqtt_packet(key)
            for key in Infos.new_stat_data:
                await Inverter._async_publ_mqtt_proxy_stat(key)

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
                self.sug_area):
            logger_mqtt.debug(f"MQTT Register: cmp:'{component}'"
                              f" node_id:'{node_id}' {data_json}")
            await self.mqtt.publish(f"{self.discovery_prfx}{component}"
                                    f"/{node_id}{id}/config", data_json)

        self.db.reg_clr_at_midnight(f'{self.entity_prfx}{self.node_id}')
