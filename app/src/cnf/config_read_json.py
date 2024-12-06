'''Config module handles the proxy configuration in the config.toml file'''

import json
from cnf.config import ConfigIfc

# Dieses file übernimmt die Add-On Konfiguration und schreibt sie in die
# Konfigurationsdatei des tsun-proxy
# Die Addon Konfiguration wird in der Datei /data/options.json bereitgestellt
# Die Konfiguration wird in der Datei /home/proxy/config/config.toml
# gespeichert

# Übernehme die Umgebungsvariablen
# alternativ kann auch auf die homeassistant supervisor API zugegriffen werden


class ConfigReadJson(ConfigIfc):
    def __init__(self, cnf_file='/data/options.json'):
        self.cnf_file = cnf_file

    def convert_inv(self, conf, inv):
        if 'serial' in inv:
            snr = inv['serial']
            del inv['serial']
            conf[snr] = {}

            for key, val in inv.items():
                self._extend_key(conf[snr], key, val)

    def convert_inv_arr(self, conf, key, val: list):
        if key not in conf:
            conf[key] = {}
        for elm in val:
            self.convert_inv(conf[key], elm)

    def convert_to_obj(self, data):
        conf = {}
        for key, val in data.items():
            if key == 'inverters' and isinstance(val, list):
                self.convert_inv_arr(conf, key, val)
            else:
                self._extend_key(conf, key, val)
        return conf

    def add_config(self) -> dict:
        try:
            with open(self.cnf_file) as f:
                data = json.load(f)
                return self.convert_to_obj(data)

        except FileNotFoundError:
            pass

        return {}
