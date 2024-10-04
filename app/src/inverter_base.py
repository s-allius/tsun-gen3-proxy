from abc import abstractmethod
import weakref
import asyncio
import logging
import traceback
import json
from aiomqtt import MqttCodeError
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.inverter_base":
    from app.src.iter_registry import AbstractIterMeta
    from app.src.proxy import Proxy
    from app.src.async_stream import StreamPtr
    from app.src.async_stream import AsyncStreamClient
    from app.src.async_stream import AsyncStreamServer
    from app.src.config import Config
    from app.src.infos import Infos
else:  # pragma: no cover
    from iter_registry import AbstractIterMeta
    from proxy import Proxy
    from async_stream import StreamPtr
    from async_stream import AsyncStreamClient
    from async_stream import AsyncStreamServer
    from config import Config
    from infos import Infos

logger_mqtt = logging.getLogger('mqtt')


class InverterIfc(metaclass=AbstractIterMeta):
    _registry = []

    @abstractmethod
    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 config_id: str, prot_class,
                 client_mode: bool):
        pass  # pragma: no cover

    @abstractmethod
    def __enter__(self):
        pass  # pragma: no cover

    @abstractmethod
    def __exit__(self, exc_type, exc, tb):
        pass  # pragma: no cover

    @abstractmethod
    def healthy(self) -> bool:
        pass  # pragma: no cover

    @abstractmethod
    async def disc(self, shutdown_started=False) -> None:
        pass  # pragma: no cover

    @abstractmethod
    async def create_remote(self) -> None:
        pass  # pragma: no cover


class InverterBase(InverterIfc, Proxy):

    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 config_id: str, prot_class,
                 client_mode: bool = False):
        Proxy.__init__(self)
        self._registry.append(weakref.ref(self))
        self.addr = writer.get_extra_info('peername')
        self.config_id = config_id
        self.prot_class = prot_class
        self.__ha_restarts = -1
        self.remote = StreamPtr(None)
        ifc = AsyncStreamServer(reader, writer,
                                self.async_publ_mqtt,
                                self.create_remote,
                                self.remote)

        self.local = StreamPtr(
            self.prot_class(self.addr, ifc, True, client_mode), ifc
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        logging.debug(f'InverterBase.__exit__() {self.addr}')
        self.__del_remote()

        self.local.stream.close()
        self.local.stream = None
        self.local.ifc.close()
        self.local.ifc = None

    def __del__(self) -> None:
        logging.debug(f'InverterBase.__del__() {self.addr}')

    def __del_remote(self):
        if self.remote.stream:
            self.remote.stream.close()
            self.remote.stream = None

        if self.remote.ifc:
            self.remote.ifc.close()
            self.remote.ifc = None

    async def disc(self, shutdown_started=False) -> None:
        if self.remote.stream:
            self.remote.stream.shutdown_started = shutdown_started
        if self.remote.ifc:
            await self.remote.ifc.disc()
        if self.local.stream:
            self.local.stream.shutdown_started = shutdown_started
        if self.local.ifc:
            await self.local.ifc.disc()

    def healthy(self) -> bool:
        logging.debug('InverterBase healthy()')

        if self.local.ifc and not self.local.ifc.healthy():
            return False
        if self.remote.ifc and not self.remote.ifc.healthy():
            return False
        return True

    async def create_remote(self) -> None:
        '''Establish a client connection to the TSUN cloud'''

        tsun = Config.get(self.config_id)
        host = tsun['host']
        port = tsun['port']
        addr = (host, port)
        stream = self.local.stream

        try:
            logging.info(f'[{stream.node_id}] Connect to {addr}')
            connect = asyncio.open_connection(host, port)
            reader, writer = await connect
            ifc = AsyncStreamClient(
                reader, writer, self.local, self.__del_remote)

            self.remote.ifc = ifc
            if hasattr(stream, 'id_str'):
                self.remote.stream = self.prot_class(
                    addr, ifc, server_side=False,
                    client_mode=False, id_str=stream.id_str)
            else:
                self.remote.stream = self.prot_class(
                    addr, ifc, server_side=False,
                    client_mode=False)

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
        if not stream or not stream.unique_id:
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
                await Proxy._async_publ_mqtt_proxy_stat(key)

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
