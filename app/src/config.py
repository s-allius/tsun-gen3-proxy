'''Config module handles the proxy configuration in the config.toml file'''

import shutil
import tomllib
import logging
from schema import Schema, And, Or, Use, Optional


class Config():
    '''Static class Config is reads and sanitize the config.

    Read config.toml file and sanitize it with read().
    Get named parts of the config with get()'''

    config = {}
    def_config = {}
    conf_schema = Schema({
        'tsun': {
            'enabled': Use(bool),
            'host':    Use(str),
            'port':    And(Use(int), lambda n: 1024 <= n <= 65535)
            },
        'solarman': {
            'enabled': Use(bool),
            'host':    Use(str),
            'port':    And(Use(int), lambda n: 1024 <= n <= 65535)
            },
        'mqtt': {
            'host':    Use(str),
            'port':    And(Use(int), lambda n: 1024 <= n <= 65535),
            'user':    And(Use(str), Use(lambda s: s if len(s) > 0 else None)),
            'passwd':  And(Use(str), Use(lambda s: s if len(s) > 0 else None))
            },
        'ha': {
            'auto_conf_prefix': Use(str),
            'discovery_prefix': Use(str),
            'entity_prefix':    Use(str),
            'proxy_node_id':    Use(str),
            'proxy_unique_id':  Use(str)
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
                                                         if len(s) > 0 and
                                                         s[-1] != '/' else s)),

                Optional('suggested_area',  default=""): Use(str),
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
                }}
            }, ignore_extra_keys=True
        )

    @classmethod
    def class_init(cls) -> None | str:  # pragma: no cover
        try:
            # make the default config transparaent by copying it
            # in the config.example file
            logging.debug('Copy Default Config to config.example.toml')

            shutil.copy2("default_config.toml",
                         "config/config.example.toml")
        except Exception:
            pass
        err_str = cls.read()
        del cls.conf_schema
        return err_str

    @classmethod
    def _read_config_file(cls) -> dict:  # pragma: no cover
        usr_config = {}

        try:
            with open("config/config.toml", "rb") as f:
                usr_config = tomllib.load(f)
        except Exception as error:
            err = f'Config.read: {error}'
            logging.error(err)
            logging.info(
                '\n  To create the missing config.toml file, '
                'you can rename the template config.example.toml\n'
                '  and customize it for your scenario.\n')
        return usr_config

    @classmethod
    def read(cls, path='') -> None | str:
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
            usr_config = cls._read_config_file()

            # merge the default and the user config
            config = def_config.copy()
            for key in ['tsun', 'solarman', 'mqtt', 'ha', 'inverters',
                        'gen3plus']:
                if key in usr_config:
                    config[key] |= usr_config[key]

            try:
                cls.config = cls.conf_schema.validate(config)
            except Exception as error:
                err = f'Config.read: {error}'
                logging.error(err)

            # logging.debug(f'Readed config: "{cls.config}" ')

        except Exception as error:
            err = f'Config.read: {error}'
            logger.error(err)
            cls.config = {}

        return err

    @classmethod
    def get(cls, member: str = None):
        '''Get a named attribute from the proxy config. If member ==
          None it returns the complete config dict'''

        if member:
            return cls.config.get(member, {})
        else:
            return cls.config

    @classmethod
    def is_default(cls, member: str) -> bool:
        '''Check if the member is the default value'''

        return cls.config.get(member) == cls.def_config.get(member)
