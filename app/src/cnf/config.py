'''Config module handles the proxy configuration in the config.toml file'''

import shutil
import logging
from abc import ABC, abstractmethod
from schema import Schema, And, Or, Use, Optional


class ConfigIfc(ABC):
    @abstractmethod
    def add_config(cls) -> dict:  # pragma: no cover
        pass

    def _extend_key(self, conf, key, val):
        lst = key.split('.')
        d = conf
        for i, idx in enumerate(lst, 1):
            if i == len(lst):
                d[idx] = val
                break
            if idx not in d:
                d[idx] = {}
            d = d[idx]


class Config():
    '''Static class Config is reads and sanitize the config.

    Read config.toml file and sanitize it with read().
    Get named parts of the config with get()'''

    conf_schema = Schema({
        'tsun': {
            'enabled': Use(bool),
            'host': Use(str),
            'port': And(Use(int), lambda n: 1024 <= n <= 65535)
        },
        'solarman': {
            'enabled': Use(bool),
            'host': Use(str),
            'port': And(Use(int), lambda n: 1024 <= n <= 65535)
        },
        'mqtt': {
            'host': Use(str),
            'port': And(Use(int), lambda n: 1024 <= n <= 65535),
            'user': Or(None, And(Use(str),
                                 Use(lambda s: s if len(s) > 0 else None))),
            'passwd': Or(None, And(Use(str),
                                   Use(lambda s: s if len(s) > 0 else None)))
        },
        'ha': {
            'auto_conf_prefix': Use(str),
            'discovery_prefix': Use(str),
            'entity_prefix': Use(str),
            'proxy_node_id': Use(str),
            'proxy_unique_id': Use(str)
        },
        'gen3plus': {
            'at_acl': {
                Or('mqtt', 'tsun'): {
                    'allow': [str],
                    Optional('block', default=[]): [str]
                }
            }
        },
        'inverters': {
            'allow_all': Use(bool), And(Use(str), lambda s: len(s) == 16): {
                Optional('monitor_sn', default=0): Use(int),
                Optional('node_id', default=""): And(Use(str),
                                                     Use(lambda s: s + '/'
                                                         if len(s) > 0
                                                         and s[-1] != '/'
                                                         else s)),
                Optional('client_mode'): {
                    'host': Use(str),
                    Optional('port', default=8899):
                        And(Use(int), lambda n: 1024 <= n <= 65535),
                    Optional('forward', default=False): Use(bool),
                },
                Optional('modbus_polling', default=True): Use(bool),
                Optional('suggested_area', default=""): Use(str),
                Optional('sensor_list', default=0x2b0): Use(int),
                Optional('pv1'): {
                    Optional('type'): Use(str),
                    Optional('manufacturer'): Use(str),
                },
                Optional('pv2'): {
                    Optional('type'): Use(str),
                    Optional('manufacturer'): Use(str),
                },
                Optional('pv3'): {
                    Optional('type'): Use(str),
                    Optional('manufacturer'): Use(str),
                },
                Optional('pv4'): {
                    Optional('type'): Use(str),
                    Optional('manufacturer'): Use(str),
                },
                Optional('pv5'): {
                    Optional('type'): Use(str),
                    Optional('manufacturer'): Use(str),
                },
                Optional('pv6'): {
                    Optional('type'): Use(str),
                    Optional('manufacturer'): Use(str),
                }
            }
        }
    }, ignore_extra_keys=True
    )

    @classmethod
    def init(cls, def_reader: ConfigIfc) -> None | str:
        cls.readers = []
        cls.act_config = {}
        cls.def_config = {}
        cls.err = None
        try:
            # make the default config transparaent by copying it
            # in the config.example file
            logging.info('Copy Default Config to config.example.toml')

            shutil.copy2("default_config.toml",
                         "config/config.example.toml")
        except Exception:
            pass

        # read example config file as default configuration
        try:
            def_config = def_reader.add_config()
            cls.def_config = cls.conf_schema.validate(def_config)
        except Exception as error:
            cls.err = f'Config.read: {error}'
            logging.error(cls.err)
        cls.act_config = cls.def_config.copy()

    @classmethod
    def add(cls, reader: ConfigIfc):
        cls.readers.append(reader)

    @classmethod
    def parse(cls) -> None | str:
        '''Read config file, merge it with the default config
        and sanitize the result'''
        cls.act_config = cls.def_config.copy()
        for reader in cls.readers:
            try:
                rd_config = reader.add_config()
                config = cls.act_config.copy()

                for key in ['tsun', 'solarman', 'mqtt', 'ha', 'inverters',
                            'gen3plus']:
                    if key in rd_config:
                        config[key] = config[key] | rd_config[key]
                        # config[key] |= rd_config[key]

                cls.act_config = cls.conf_schema.validate(config)
            except FileNotFoundError:
                pass
            except Exception as error:
                cls.err = f'Config.read: {error}'
                logging.error(cls.err)
        return cls.err

    @classmethod
    def get(cls, member: str = None):
        '''Get a named attribute from the proxy config. If member ==
          None it returns the complete config dict'''

        if member:
            return cls.act_config.get(member, {})
        else:
            return cls.act_config

    @classmethod
    def is_default(cls, member: str) -> bool:
        '''Check if the member is the default value'''

        return cls.act_config.get(member) == cls.def_config.get(member)
