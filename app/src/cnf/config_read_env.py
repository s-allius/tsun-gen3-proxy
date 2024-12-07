'''Config module handles the proxy configuration in the config.toml file'''

import os
from cnf.config import ConfigIfc

# Dieses file übernimmt die Add-On Konfiguration und schreibt sie in die
# Konfigurationsdatei des tsun-proxy
# Die Addon Konfiguration wird in der Datei /data/options.json bereitgestellt
# Die Konfiguration wird in der Datei /home/proxy/config/config.toml
# gespeichert

# Übernehme die Umgebungsvariablen
# alternativ kann auch auf die homeassistant supervisor API zugegriffen werden


class ConfigReadEnv(ConfigIfc):

    def add_config(self) -> dict:
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
        return "Read environment"
