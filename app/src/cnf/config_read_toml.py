'''Config Reader module which handles *.toml config files'''

import tomllib
from cnf.config import ConfigIfc


class ConfigReadToml(ConfigIfc):
    '''Reader for toml config files'''
    def __init__(self, cnf_file):
        '''Read a toml file and add the settings to the config'''
        if not isinstance(cnf_file, str):
            return
        self.cnf_file = cnf_file
        super().__init__()

    def get_config(self) -> dict:
        with open(self.cnf_file, "rb") as f:
            return tomllib.load(f)

    def descr(self):
        return self.cnf_file
