import asyncio
import logging
import json
from itertools import chain

from cnf.config import Config
from mqtt import Mqtt
from infos import Infos

logger_mqtt = logging.getLogger('mqtt')


class Proxy():
    '''class Proxy is a baseclass

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
        create_remote(): Establish a client connection to the TSUN cloud
        async_publ_mqtt(): Publish data to MQTT broker
    '''
    @classmethod
    def class_init(cls) -> None:
        logging.debug('Proxy.class_init')
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
        batteries = Config.get('batteries')
        # logger.debug(f'Proxys: {inverters}')
        for _, inv in chain(inverters.items(), batteries.items()):
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
    async def class_close(cls, loop) -> None:   # pragma: no cover
        logging.debug('Proxy.class_close')
        logging.info('Close MQTT Task')
        await cls.mqtt.close()
        cls.mqtt = None
