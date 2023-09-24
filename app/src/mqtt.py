import asyncio, logging
import aiomqtt
from config import Config

logger_mqtt = logging.getLogger('mqtt')


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        logger_mqtt.debug(f'singleton: __call__')                                
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Mqtt(metaclass=Singleton):
    client = None

    def __init__(self):
        logger_mqtt.debug(f'MQTT: __init__') 
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self.__loop())
                
        
    def __del__(self):
        logger_mqtt.debug(f'MQTT: __del__')
    

    async def close(self) -> None:
        logger_mqtt.debug(f'MQTT: close') 
        self.task.cancel()
        try:
            await self.task
        except Exception as e:
            logging.debug(f"Mqtt.close: exception: {e} ...")
        
  

    async def publish(self, topic: str, payload: str | bytes | bytearray | int | float | None = None) -> None:
        if self.client:
            await self.client.publish(topic, payload)


    async def __loop(self) -> None:
        mqtt = Config.get('mqtt')
        ha = Config.get('ha')
        logger_mqtt.info(f'start MQTT: host:{mqtt["host"]}  port:{mqtt["port"]}  user:{mqtt["user"]}')                                
        self.client = aiomqtt.Client(hostname=mqtt['host'], port=mqtt['port'], username=mqtt['user'], password=mqtt['passwd'])
     
        interval = 5  # Seconds
        while True:
            try:
                async with self.client:
                    async with self.client.messages() as messages:
                        await self.client.subscribe(f"{ha['auto_conf_prefix']}/status")
                        async for message in messages:
                            logger_mqtt.info(f'Home-Assistant Status: {message.payload.decode("UTF-8")}')
            except aiomqtt.MqttError:
                logger_mqtt.info(f"Connection lost; Reconnecting in {interval} seconds ...")
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger_mqtt.debug(f"MQTT task cancelled")
                self.client = None
                return
