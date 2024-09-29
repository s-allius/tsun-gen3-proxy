import asyncio
import logging
import traceback
import json
from aiomqtt import MqttCodeError

if __name__ == "app.src.inverter_base":
    from app.src.inverter import Inverter
    from app.src.async_stream import AsyncStreamClient
    from app.src.config import Config
    from app.src.infos import Infos
else:  # pragma: no cover
    from inverter import Inverter
    from async_stream import AsyncStreamClient
    from config import Config
    from infos import Infos

logger_mqtt = logging.getLogger('mqtt')


class InverterBase(Inverter):
    def __init__(self):
        self.__ha_restarts = -1

    async def async_create_remote(self, inv_prot: str, conn_class) -> None:
        '''Establish a client connection to the TSUN cloud'''
        tsun = Config.get(inv_prot)
        host = tsun['host']
        port = tsun['port']
        addr = (host, port)
        stream = self.local.stream

        try:
            logging.info(f'[{stream.node_id}] Connect to {addr}')
            connect = asyncio.open_connection(host, port)
            reader, writer = await connect
            ifc = AsyncStreamClient(reader, writer,
                                    self.remote)

            if hasattr(stream, 'id_str'):
                self.remote.stream = conn_class(
                    addr, ifc, False, stream.id_str)
            else:
                self.remote.stream = conn_class(
                    addr, ifc, False)

            logging.info(f'[{self.remote.stream.node_id}:'
                         f'{self.remote.stream.conn_no}] '
                         f'Connected to {addr}')
            asyncio.create_task(self.remote.ifc.client_loop(addr))

        except (ConnectionRefusedError, TimeoutError) as error:
            logging.info(f'{error}')
        except Exception:
            Infos.inc_counter('SW_Exception')
            logging.error(
                f"Inverter: Exception for {addr}:\n"
                f"{traceback.format_exc()}")

    async def async_publ_mqtt(self) -> None:
        '''publish data to MQTT broker'''
        stream = self.local.stream
        if not stream.unique_id:
            return
        # check if new inverter or collector infos are available or when the
        #  home assistant has changed the status back to online
        try:
            if (('inverter' in stream.new_data and stream.new_data['inverter'])
                    or ('collector' in stream.new_data and
                        stream.new_data['collector'])
                    or self.mqtt.ha_restarts != self.__ha_restarts):
                await self._register_proxy_stat_home_assistant()
                await self.__register_home_assistant(stream)
                self.__ha_restarts = self.mqtt.ha_restarts

            for key in stream.new_data:
                await self.__async_publ_mqtt_packet(stream, key)
            for key in Infos.new_stat_data:
                await Inverter._async_publ_mqtt_proxy_stat(key)

        except MqttCodeError as error:
            logging.error(f'Mqtt except: {error}')
        except Exception:
            Infos.inc_counter('SW_Exception')
            logging.error(
                f"Inverter: Exception:\n"
                f"{traceback.format_exc()}")

    async def __async_publ_mqtt_packet(self, stream, key):
        db = stream.db.db
        if key in db and stream.new_data[key]:
            data_json = json.dumps(db[key])
            node_id = stream.node_id
            logger_mqtt.debug(f'{key}: {data_json}')
            await self.mqtt.publish(f'{self.entity_prfx}{node_id}{key}', data_json)  # noqa: E501
            stream.new_data[key] = False

    async def __register_home_assistant(self, stream) -> None:
        '''register all our topics at home assistant'''
        for data_json, component, node_id, id in stream.db.ha_confs(
                self.entity_prfx, stream.node_id, stream.unique_id,
                stream.sug_area):
            logger_mqtt.debug(f"MQTT Register: cmp:'{component}'"
                              f" node_id:'{node_id}' {data_json}")
            await self.mqtt.publish(f"{self.discovery_prfx}{component}"
                                    f"/{node_id}{id}/config", data_json)

        stream.db.reg_clr_at_midnight(f'{self.entity_prfx}{stream.node_id}')
