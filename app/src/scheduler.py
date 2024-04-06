import logging
import json
from mqtt import Mqtt
from aiocron import crontab
from infos import ClrAtMidnight

logger_mqtt = logging.getLogger('mqtt')


class Schedule:
    mqtt = None

    @classmethod
    def start(cls):
        logging.info("Scheduler init")
        cls.mqtt = Mqtt(None)

        crontab('0 0 * * *', func=cls.atmidnight, start=True)
        # crontab('*/5 * * * *', func=cls.atmidnight, start=True)

    @classmethod
    async def atmidnight(cls):
        logging.info("Clear daily counters at midnight")

        for key, data in ClrAtMidnight.elm():
            logger_mqtt.debug(f'{key}: {data}')
            data_json = json.dumps(data)
            await cls.mqtt.publish(f"{key}", data_json)
