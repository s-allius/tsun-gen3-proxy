'''Config Reader module which handles config values from the environment'''

import os
from cnf.config import ConfigIfc


class ConfigReadEnv(ConfigIfc):
    '''Reader for environment values of the configuration'''

    def get_config(self) -> dict:
        conf = {}
        data = [
            ('mqtt.host', 'MQTT_HOST'),
            ('mqtt.port', 'MQTT_PORT'),
            ('mqtt.user', 'MQTT_USER'),
            ('mqtt.passwd', 'MQTT_PASSWORD'),
        ]
        for key, env_var in data:
            val = os.getenv(env_var)
            if val:
                self._extend_key(conf, key, val)
        return conf

    def descr(self):
        return "environment"
