import logging
from mqtt import Mqtt
from aiocron import crontab


class Schedule:
    mqtt = None

    @classmethod
    def start(cls):
        logging.info("Scheduler init")
        cls.mqtt = Mqtt(None)
        # json.dumps(i.db['total']) == json.dumps({'Daily_Generation': 0.0})
        # json.dumps(i.db['input']) == json.dumps({"pv1": {"Daily_Generation": 0.0}, "pv2": {"Daily_Generation": 0.0}, "pv3": {"Daily_Generation": 0.0}, "pv4": {"Daily_Generation": 0.0}})  # noqa: E501

        crontab('0 0 * * *', func=cls.atmidnight, start=True)

    async def atmidnight():
        logging.info("Scheduler is working")
        # db = self.db.db
        # if key in db and self.new_data[key]:
        # data_json = json.dumps(db[key])
        # node_id = self.node_id
        # logger_mqtt.debug(f'{key}: {data_json}')
        # await cls.mqtt.publish(f'{self.entity_prfx}{node_id}{key}', data_json)  # noqa: E501
