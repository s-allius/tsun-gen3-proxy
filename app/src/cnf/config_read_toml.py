'''Config module handles the proxy configuration in the config.toml file'''

import tomllib
from cnf.config import ConfigIfc


class ConfigReadToml(ConfigIfc):
    def __init__(self, cnf_file="config/config.toml"):
        self.cnf_file = cnf_file
        super().__init__()

    def add_config(self) -> dict:
        with open(self.cnf_file, "rb") as f:
            return tomllib.load(f)
