import asyncio
import logging
import aiomqtt
import traceback

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

        ha = Config.get('ha')
        self.ha_status_topic = f"{ha['auto_conf_prefix']}/status"
        self.mb_rated_topic = f"{ha['entity_prefix']}/+/rated_load"
        self.mb_out_coeff_topic = f"{ha['entity_prefix']}/+/out_coeff"
        self.mb_reads_topic = f"{ha['entity_prefix']}/+/modbus_read_regs"
        self.mb_inputs_topic = f"{ha['entity_prefix']}/+/modbus_read_inputs"
        self.mb_at_cmd_topic = f"{ha['entity_prefix']}/+/at_cmd"

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
                    self.ctime = datetime.now()
                    self.published = 0
                    self.received = 0

                    if self.__cb_mqtt_is_up:
                        await self.__cb_mqtt_is_up()

                    await self.__client.subscribe(self.ha_status_topic)
                    await self.__client.subscribe(self.mb_rated_topic)
                    await self.__client.subscribe(self.mb_out_coeff_topic)
                    await self.__client.subscribe(self.mb_reads_topic)
                    await self.__client.subscribe(self.mb_inputs_topic)
                    await self.__client.subscribe(self.mb_at_cmd_topic)

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

    async def dispatch_msg(self, message):
        self.received += 1

        if message.topic.matches(self.ha_status_topic):
            status = message.payload.decode("UTF-8")
            logger_mqtt.info('Home-Assistant Status:'
                             f' {status}')
            if status == 'online':
                self.ha_restarts += 1
                await self.__cb_mqtt_is_up()

        if message.topic.matches(self.mb_rated_topic):
            await self.modbus_cmd(message,
                                  Modbus.WRITE_SINGLE_REG,
                                  1, 0x2008)

        if message.topic.matches(self.mb_out_coeff_topic):
            payload = message.payload.decode("UTF-8")
            try:
                val = round(float(payload) * 1024/100)
                if val < 0 or val > 1024:
                    logger_mqtt.error('out_coeff: value must be in'
                                      'the range 0..100,'
                                      f' got: {payload}')
                else:
                    await self.modbus_cmd(message,
                                          Modbus.WRITE_SINGLE_REG,
                                          0, 0x202c, val)
            except Exception:
                pass

        if message.topic.matches(self.mb_reads_topic):
            await self.modbus_cmd(message,
                                  Modbus.READ_REGS, 2)

        if message.topic.matches(self.mb_inputs_topic):
            await self.modbus_cmd(message,
                                  Modbus.READ_INPUTS, 2)

        if message.topic.matches(self.mb_at_cmd_topic):
            await self.at_cmd(message)

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

    async def modbus_cmd(self, message, func, params=0, addr=0, val=0):
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

    async def at_cmd(self, message):
        payload = message.payload.decode("UTF-8")
        for fnc in self.each_inverter(message, "send_at_cmd"):
            await fnc(payload)
