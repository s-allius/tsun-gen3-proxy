import asyncio
import logging
import aiomqtt
from config import Config

logger_mqtt = logging.getLogger('mqtt')


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        logger_mqtt.debug('singleton: __call__')
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton,
                                        cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Mqtt(metaclass=Singleton):
    __client = None
    __cb_MqttIsUp = None

    def __init__(self, cb_MqttIsUp):
        logger_mqtt.debug('MQTT: __init__')
        if cb_MqttIsUp:
            self.cb_MqttIsUp = cb_MqttIsUp
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
        while True:
            try:
                async with self.__client:
                    logger_mqtt.info('MQTT broker connection established')

                    if self.cb_MqttIsUp:
                        await self.cb_MqttIsUp()

                    async with self.__client.messages() as messages:
                        await self.__client.subscribe(
                            f"{ha['auto_conf_prefix']}"
                            "/status")
                        async for message in messages:
                            status = message.payload.decode("UTF-8")
                            logger_mqtt.info('Home-Assistant Status:'
                                             f' {status}')
                            if status == 'online':
                                self.ha_restarts += 1
                                await self.cb_MqttIsUp()

            except aiomqtt.MqttError:
                logger_mqtt.info(f"Connection lost; Reconnecting in {interval}"
                                 " seconds ...")
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger_mqtt.debug("MQTT task cancelled")
                self.__client = None
                return
