import asyncio
import logging
import aiomqtt
import traceback
import struct
import inspect

from modbus import Modbus
from messages import Message
from cnf.config import Config
from singleton import Singleton
from datetime import datetime


logger_mqtt = logging.getLogger('mqtt')


class Mqtt(metaclass=Singleton):
    __client: aiomqtt.Client = None
    __cb_mqtt_is_up = None
    ctime = None
    published: int = 0
    received: int = 0

    def __init__(self, cb_mqtt_is_up):
        logger_mqtt.debug('MQTT: __init__')
        if cb_mqtt_is_up:
            self.__cb_mqtt_is_up = cb_mqtt_is_up
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self.__loop())
        self.ha_restarts = 0
        self.topic_defs = [
            {'prefix': 'auto_conf_prefix', 'topic': '/status',
             'fnc': self._ha_status, 'args': []},
            {'prefix': 'entity_prefix', 'topic': '/+/rated_load',
             'fnc': self._modbus_cmd,
             'args': [Modbus.WRITE_SINGLE_REG, 1, 0x2008]},
            {'prefix': 'entity_prefix', 'topic': '/+/out_coeff',
             'fnc': self._out_coeff, 'args': []},
            {'prefix': 'entity_prefix', 'topic': '/+/dcu_power',
             'fnc': self._dcu_cmd, 'args': []},
            {'prefix': 'entity_prefix', 'topic': '/+/modbus_read_regs',
             'fnc': self._modbus_cmd, 'args': [Modbus.READ_REGS, 2]},
            {'prefix': 'entity_prefix', 'topic': '/+/modbus_read_inputs',
             'fnc': self._modbus_cmd, 'args': [Modbus.READ_INPUTS, 2]},
            {'prefix': 'entity_prefix', 'topic': '/+/at_cmd',
             'fnc': self._at_cmd, 'args': []},
        ]

        ha = Config.get('ha')
        for entry in self.topic_defs:
            entry['full_topic'] = f"{ha[entry['prefix']]}{entry['topic']}"

    @property
    def ha_restarts(self):
        return self._ha_restarts

    @ha_restarts.setter
    def ha_restarts(self, value):
        self._ha_restarts = value

    async def close(self) -> None:
        logger_mqtt.debug('MQTT: close')
        self.task.cancel()
        try:
            await self.task

        except (asyncio.CancelledError, Exception) as e:
            logging.debug(f"Mqtt.close: exception: {e} ...")

    async def publish(self, topic: str, payload: str | bytes | bytearray
                      | int | float | None = None) -> None:
        if self.__client:
            await self.__client.publish(topic, payload)
            self.published += 1

    async def __loop(self) -> None:
        mqtt = Config.get('mqtt')
        logger_mqtt.info(f'start MQTT: host:{mqtt["host"]}  port:'
                         f'{mqtt["port"]}  '
                         f'user:{mqtt["user"]}')
        self.__client = aiomqtt.Client(hostname=mqtt['host'],
                                       port=mqtt['port'],
                                       username=mqtt['user'],
                                       password=mqtt['passwd'])

        interval = 5  # Seconds

        while True:
            try:
                async with self.__client:
                    logger_mqtt.info('MQTT broker connection established')
                    await self._init_new_conn()

                    async for message in self.__client.messages:
                        await self.dispatch_msg(message)

            except aiomqtt.MqttError:
                self.ctime = None

                if Config.is_default('mqtt'):
                    logger_mqtt.info(
                        "MQTT is unconfigured; Check your config.toml!")
                    interval = 30
                else:
                    interval = 5  # Seconds
                    logger_mqtt.info(
                        f"Connection lost; Reconnecting in {interval}"
                        " seconds ...")

                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger_mqtt.debug("MQTT task cancelled")
                self.__client = None
                return
            except Exception:
                # self.inc_counter('SW_Exception')   # fixme
                self.ctime = None
                logger_mqtt.error(
                    f"Exception:\n"
                    f"{traceback.format_exc()}")

    async def _init_new_conn(self):
        self.ctime = datetime.now()
        self.published = 0
        self.received = 0
        if self.__cb_mqtt_is_up:
            await self.__cb_mqtt_is_up()
        for entry in self.topic_defs:
            await self.__client.subscribe(entry['full_topic'])

    async def dispatch_msg(self, message):
        self.received += 1

        for entry in self.topic_defs:
            if message.topic.matches(entry['full_topic']) \
               and 'fnc' in entry:
                fnc = entry['fnc']

                if inspect.iscoroutinefunction(fnc):
                    await entry['fnc'](message, *entry['args'])
                elif callable(fnc):
                    entry['fnc'](message, *entry['args'])

    async def _ha_status(self, message):
        status = message.payload.decode("UTF-8")
        logger_mqtt.info('Home-Assistant Status:'
                         f' {status}')
        if status == 'online':
            self.ha_restarts += 1
            await self.__cb_mqtt_is_up()

    async def _out_coeff(self, message):
        payload = message.payload.decode("UTF-8")
        try:
            val = round(float(payload) * 1024/100)
            if val < 0 or val > 1024:
                logger_mqtt.error('out_coeff: value must be in'
                                  'the range 0..100,'
                                  f' got: {payload}')
            else:
                await self._modbus_cmd(message,
                                       Modbus.WRITE_SINGLE_REG,
                                       0, 0x202c, val)
        except Exception:
            pass

    def each_inverter(self, message, func_name: str):
        topic = str(message.topic)
        node_id = topic.split('/')[1] + '/'
        for m in Message:
            if m.server_side and (m.node_id == node_id):
                logger_mqtt.debug(f'Found: {node_id}')
                fnc = getattr(m, func_name, None)
                if callable(fnc):
                    yield fnc
                else:
                    logger_mqtt.warning(f'Cmd not supported by: {node_id}')
                break

        else:
            logger_mqtt.warning(f'Node_id: {node_id} not found')

    async def _modbus_cmd(self, message, func, params=0, addr=0, val=0):
        payload = message.payload.decode("UTF-8")
        for fnc in self.each_inverter(message, "send_modbus_cmd"):
            res = payload.split(',')
            if params > 0 and params != len(res):
                logger_mqtt.error(f'Parameter expected: {params}, '
                                  f'got: {len(res)}')
                return
            if params == 1:
                val = int(payload)
            elif params == 2:
                addr = int(res[0], base=16)
                val = int(res[1])  # lenght
            await fnc(func, addr, val, logging.INFO)

    async def _at_cmd(self, message):
        payload = message.payload.decode("UTF-8")
        for fnc in self.each_inverter(message, "send_at_cmd"):
            await fnc(payload)

    def _dcu_cmd(self, message):
        payload = message.payload.decode("UTF-8")
        val = round(float(payload) * 10)
        if val < 1000 or val > 8000:
            logger_mqtt.error('dcu_power: value must be in'
                              'the range 100..800,'
                              f' got: {payload}')
        else:
            pdu = struct.pack('>BBBBBBH', 1, 1, 6, 1, 0, 1, val)
            for fnc in self.each_inverter(message, "send_dcu_cmd"):
                fnc(pdu)
