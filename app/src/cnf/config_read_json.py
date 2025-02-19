'''Config Reader module which handles *.json config files'''

import json
from cnf.config import ConfigIfc


class ConfigReadJson(ConfigIfc):
    '''Reader for json config files'''
    def __init__(self, cnf_file='/data/options.json'):
        '''Read a json file and add the settings to the config'''
        if not isinstance(cnf_file, str):
            return
        self.cnf_file = cnf_file
        super().__init__()

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
            if (key == 'inverters' or key == 'batteries') and \
               isinstance(val, list):
                self.convert_inv_arr(conf, key, val)
            else:
                self._extend_key(conf, key, val)
        return conf

    def get_config(self) -> dict:
        with open(self.cnf_file) as f:
            data = json.load(f)
            return self.convert_to_obj(data)

    def descr(self):
        return self.cnf_file
