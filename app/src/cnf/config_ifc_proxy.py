'''Config module handles the proxy configuration in the config.toml file'''

import shutil
import tomllib
import logging
from cnf.config import ConfigIfc


class ConfigIfcProxy(ConfigIfc):
    def __init__(self):
        try:
            # make the default config transparaent by copying it
            # in the config.example file
            logging.info('Copy Default Config to config.example.toml')

            shutil.copy2("default_config.toml",
                         "config/config.example.toml")
        except Exception:
            pass

    def get_config(self, cnf_file="config/config.toml") -> dict:
        usr_config = {}

        try:
            with open(cnf_file, "rb") as f:
                usr_config = tomllib.load(f)
        except Exception as error:
            err = f'Config.read: {error}'
            logging.error(err)
            logging.info(
                '\n  To create the missing config.toml file, '
                'you can rename the template config.example.toml\n'
                '  and customize it for your scenario.\n')
        return usr_config
