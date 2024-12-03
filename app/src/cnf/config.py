'''Config module handles the proxy configuration in the config.toml file'''

import tomllib
import logging
from abc import ABC, abstractmethod
from schema import Schema, And, Or, Use, Optional


class ConfigIfc(ABC):
    @abstractmethod
    def get_config(cls) -> dict:  # pragma: no cover
        pass


class Config():
    '''Static class Config is reads and sanitize the config.

    Read config.toml file and sanitize it with read().
    Get named parts of the config with get()'''
    act_config = {}
    def_config = {}

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
            'user': And(Use(str), Use(lambda s: s if len(s) > 0 else None)),
            'passwd': And(Use(str), Use(lambda s: s if len(s) > 0 else None))
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
    def init(cls, ifc: ConfigIfc, path='') -> None | str:
        cls.ifc = ifc
        cls.act_config = {}
        cls.def_config = {}
        return cls.read(path)

    @classmethod
    def read(cls, path) -> None | str:
        '''Read config file, merge it with the default config
        and sanitize the result'''
        err = None
        config = {}
        logger = logging.getLogger('data')

        try:
            # read example config file as default configuration
            cls.def_config = {}
            with open(f"{path}default_config.toml", "rb") as f:
                def_config = tomllib.load(f)
                cls.def_config = cls.conf_schema.validate(def_config)

            # overwrite the default values, with values from
            # the config.toml file
            usr_config = cls.ifc.get_config()

            # merge the default and the user config
            config = def_config.copy()
            for key in ['tsun', 'solarman', 'mqtt', 'ha', 'inverters',
                        'gen3plus']:
                if key in usr_config:
                    config[key] |= usr_config[key]

            try:
                cls.act_config = cls.conf_schema.validate(config)
            except Exception as error:
                err = f'Config.read: {error}'
                logging.error(err)

            # logging.debug(f'Readed config: "{cls.act_config}" ')

        except Exception as error:
            err = f'Config.read: {error}'
            logger.error(err)
            cls.act_config = {}

        return err

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
