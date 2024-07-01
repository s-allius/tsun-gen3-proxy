import logging
import json
from mqtt import Mqtt
from aiocron import crontab
from infos import ClrAtMidnight

logger_mqtt = logging.getLogger('mqtt')


class Schedule:
    mqtt = None
    count = 0

    @classmethod
    def start(cls) -> None:
        '''Start the scheduler and schedule the tasks (cron jobs)'''
        logging.debug("Scheduler init")
        cls.mqtt = Mqtt(None)

        crontab('0 0 * * *', func=cls.atmidnight, start=True)

    @classmethod
    async def atmidnight(cls) -> None:
        '''Clear daily counters at midnight'''
        logging.info("Clear daily counters at midnight")

        for key, data in ClrAtMidnight.elm():
            logger_mqtt.debug(f'{key}: {data}')
            data_json = json.dumps(data)
            await cls.mqtt.publish(f"{key}", data_json)
