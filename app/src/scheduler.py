import logging
import json
from mqtt import Mqtt
from aiocron import crontab
from infos import ClrAtMidnight
from modbus import Modbus
from messages import Message

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

        # every minute
        crontab('* * * * *', func=cls.regular_modbus_cmds, start=True)

    @classmethod
    async def atmidnight(cls) -> None:
        '''Clear daily counters at midnight'''
        logging.info("Clear daily counters at midnight")

        for key, data in ClrAtMidnight.elm():
            logger_mqtt.debug(f'{key}: {data}')
            data_json = json.dumps(data)
            await cls.mqtt.publish(f"{key}", data_json)

    @classmethod
    async def regular_modbus_cmds(cls):
        # logging.info("Regular Modbus requests")
        if 0 == (cls.count % 30):
            # logging.info("Regular Modbus Status request")
            addr, len = 0x2007, 2
        else:
            addr, len = 0x3008, 20
        cls.count += 1

        for m in Message:
            if m.server_side:
                fnc = getattr(m, "send_modbus_cmd", None)
                if callable(fnc):
                    await fnc(Modbus.READ_REGS, addr, len)
