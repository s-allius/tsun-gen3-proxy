import asyncio
import logging
import aiomqtt
import traceback
from modbus import Modbus
from messages import Message
from config import Config
from singleton import Singleton

logger_mqtt = logging.getLogger('mqtt')


class Mqtt(metaclass=Singleton):
    __client = None
    __cb_MqttIsUp = None

    def __init__(self, cb_MqttIsUp):
        logger_mqtt.debug('MQTT: __init__')
        if cb_MqttIsUp:
            self.__cb_MqttIsUp = cb_MqttIsUp
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self.__loop())
        self.ha_restarts = 0

    @property
    def ha_restarts(self):
        return self._ha_restarts

    @ha_restarts.setter
    def ha_restarts(self, value):
        self._ha_restarts = value

    def __del__(self):
        logger_mqtt.debug('MQTT: __del__')

    async def close(self) -> None:
        logger_mqtt.debug('MQTT: close')
        self.task.cancel()
        try:
            await self.task
        except Exception as e:
            logging.debug(f"Mqtt.close: exception: {e} ...")

    async def publish(self, topic: str, payload: str | bytes | bytearray
                      | int | float | None = None) -> None:
        if self.__client:
            await self.__client.publish(topic, payload)

    async def __loop(self) -> None:
        mqtt = Config.get('mqtt')
        ha = Config.get('ha')
        logger_mqtt.info(f'start MQTT: host:{mqtt["host"]}  port:'
                         f'{mqtt["port"]}  '
                         f'user:{mqtt["user"]}')
        self.__client = aiomqtt.Client(hostname=mqtt['host'],
                                       port=mqtt['port'],
                                       username=mqtt['user'],
                                       password=mqtt['passwd'])

        interval = 5  # Seconds
        ha_status_topic = f"{ha['auto_conf_prefix']}/status"
        inv_cnf_topic = "tsun/+/test"

        while True:
            try:
                async with self.__client:
                    logger_mqtt.info('MQTT broker connection established')

                    if self.__cb_MqttIsUp:
                        await self.__cb_MqttIsUp()

                    # async with self.__client.messages() as messages:
                    await self.__client.subscribe(ha_status_topic)
                    await self.__client.subscribe(inv_cnf_topic)

                    async for message in self.__client.messages:
                        if message.topic.matches(ha_status_topic):
                            status = message.payload.decode("UTF-8")
                            logger_mqtt.info('Home-Assistant Status:'
                                             f' {status}')
                            if status == 'online':
                                self.ha_restarts += 1
                                await self.__cb_MqttIsUp()

                        if message.topic.matches(inv_cnf_topic):
                            topic = str(message.topic)
                            node_id = topic.split('/')[1] + '/'
                            payload = message.payload.decode("UTF-8")
                            logger_mqtt.info(f'InvCnf: {node_id}:{payload}')
                            for m in Message:
                                if m.server_side and m.node_id == node_id:
                                    logger_mqtt.info(f'Found: {node_id}')
                                    fnc = getattr(m, "send_modbus_cmd", None)
                                    if callable(fnc):
                                        # await fnc(Modbus.MB_WRITE_SINGLE_REG,
                                        #           0x2008, 2)
                                        await fnc(Modbus.MB_READ_SINGLE_REG,
                                                  0x2008, 1)

            except aiomqtt.MqttError:
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
                # self.inc_counter('SW_Exception')
                logger_mqtt.error(
                    f"Exception:\n"
                    f"{traceback.format_exc()}")
