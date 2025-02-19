'''Config module handles the proxy configuration'''

import shutil
import logging
from abc import ABC, abstractmethod
from schema import Schema, And, Or, Use, Optional


class ConfigIfc(ABC):
    '''Abstract basis class for config readers'''
    def __init__(self):
        Config.add(self)

    @abstractmethod
    def get_config(self) -> dict:    # pragma: no cover
        '''get the unverified config from the reader'''
        pass

    @abstractmethod
    def descr(self) -> str:          # pragma: no cover
        '''return a descriction of the source, e.g. the file name'''
        pass

    def _extend_key(self, conf, key, val):
        '''split a dotted dict key into a hierarchical dict tree '''
        lst = key.split('.')
        d = conf
        for i, idx in enumerate(lst, 1):  # pragma: no branch
            if i == len(lst):
                d[idx] = val
                break
            if idx not in d:
                d[idx] = {}
            d = d[idx]


class Config():
    '''Static class Config build and sanitize the internal config dictenary.

 Using config readers, a partial configuration is added to config.
 Config readers are a derivation of the abstract ConfigIfc reader.
 When a config reader is instantiated, theits `get_config` method is
 called automatically and afterwards the config will be merged.
    '''

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
            'allow_all': Use(bool),
            And(Use(str), lambda s: len(s) == 16): {
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
                Optional('sensor_list', default=0): Use(int),
                Or(Optional('pv1'),
                   Optional('pv2'),
                   Optional('pv3'),
                   Optional('pv4'),
                   Optional('pv5'),
                   Optional('pv6')): {
                    Optional('type'): Use(str),
                    Optional('manufacturer'): Use(str),
                }
            }
        },
        'batteries': {
            And(Use(str), lambda s: len(s) == 16): {
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
                Optional('sensor_list', default=0): Use(int),
                Or(Optional('pv1'),
                   Optional('pv2')): {
                    Optional('type'): Use(str),
                    Optional('manufacturer'): Use(str),
                }
            }
        }
    }, ignore_extra_keys=True
    )

    @classmethod
    def init(cls, def_reader: ConfigIfc) -> None | str:
        '''Initialise the Proxy-Config

Copy the internal default config file into the config directory
and initialise the Config with the default configuration '''
        cls.err = None
        cls.def_config = {}
        try:
            # make the default config transparaent by copying it
            # in the config.example file
            logging.debug('Copy Default Config to config.example.toml')

            shutil.copy2("default_config.toml",
                         "config/config.example.toml")
        except Exception:
            pass

        # read example config file as default configuration
        try:
            def_config = def_reader.get_config()
            cls.def_config = cls.conf_schema.validate(def_config)
            logging.info(f'Read from {def_reader.descr()} => ok')
        except Exception as error:
            cls.err = f'Config.read: {error}'
            logging.error(
                f"Can't read from {def_reader.descr()} => error\n  {error}")

        cls.act_config = cls.def_config.copy()

    @classmethod
    def add(cls, reader: ConfigIfc):
        '''Merge the config from the Config Reader into the config

Checks if a default config exists. If no default configuration exists,
the Config.init  method has not yet been called.This is normal for the very
first Config Reader which creates the default config and must be ignored
here. The default config reader is handled in the Config.init method'''
        if hasattr(cls, 'def_config'):
            cls.__parse(reader)

    @classmethod
    def get_error(cls) -> None | str:
        '''return the last error as a string or None if there is no error'''
        return cls.err

    @classmethod
    def __parse(cls, reader) -> None | str:
        '''Read config from the reader, merge it with the default config
        and sanitize the result'''
        res = 'ok'
        try:
            rd_config = reader.get_config()
            config = cls.act_config.copy()
            for key in ['tsun', 'solarman', 'mqtt', 'ha', 'inverters',
                        'gen3plus', 'batteries']:
                if key in rd_config:
                    config[key] = config[key] | rd_config[key]

            cls.act_config = cls.conf_schema.validate(config)
        except FileNotFoundError:
            res = 'n/a'
        except Exception as error:
            cls.err = f'error: {error}'
            logging.error(
                f"Can't read from {reader.descr()} => error\n  {error}")
            return cls.err

        logging.info(f'Read from {reader.descr()} => {res}')
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
