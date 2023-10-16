'''Config module handles the proxy configuration in the config.toml file'''

import shutil, tomllib, logging
from schema import Schema, And, Use, Optional

class Config():
    '''Static class Config is reads and sanitize the config. 
    
    Read config.toml file and sanitize it with read(). 
    Get named parts of the config with get()'''

    config = {}
    conf_schema = Schema({  'tsun': {
                                    'enabled': Use(bool),
                                    'host':    Use(str), 
                                    'port':    And(Use(int), lambda n: 1024 <= n <= 65535)}, 

                            'mqtt': {
                                    'host':    Use(str), 
                                    'port':    And(Use(int), lambda n: 1024 <= n <= 65535), 
                                    'user':    And(Use(str), Use(lambda s: s if len(s) >0 else None)), 
                                    'passwd':  And(Use(str), Use(lambda s: s if len(s) >0 else None))},

                            
                            'ha': {
                                    'auto_conf_prefix': Use(str),
                                    'discovery_prefix': Use(str),
                                    'entity_prefix':    Use(str),
                                    'proxy_node_id':    Use(str),
                                    'proxy_unique_id':  Use(str)},
                         
                            'inverters': {
                                    'allow_all' : Use(bool),
                                    And(Use(str), lambda s: len(s) == 16 ): { 
                                           Optional('node_id',         default=""): And(Use(str),Use(lambda s: s +'/' if len(s)> 0 and s[-1] != '/' else s)), 
                                           Optional('suggested_area',  default=""): Use(str)
                                           }}
                            }, ignore_extra_keys=True)

    @classmethod
    def read(cls) -> None:
        '''Read config file, merge it with the default config and sanitize the result'''

        config = {}
        logger = logging.getLogger('data')

        try:
            # make the default config transparaent by copying it in the config.example file
            shutil.copy2("default_config.toml", "config/config.example.toml")

            # read example config file as default configuration
            with open("default_config.toml", "rb") as f:
                def_config = tomllib.load(f)

            # overwrite the default values, with values from the config.toml file
            with open("config/config.toml", "rb") as f:
                usr_config = tomllib.load(f)
 
            config['tsun']      = def_config['tsun']      | usr_config['tsun']
            config['mqtt']      = def_config['mqtt']      | usr_config['mqtt']
            config['ha']        = def_config['ha']        | usr_config['ha']
            config['inverters'] = def_config['inverters'] | usr_config['inverters']

            cls.config = cls.conf_schema.validate(config)
            #logging.debug(f'Readed config: "{cls.config}" ')
 
        except Exception as error:
            logger.error(f'Config.read: {error}')
            cls.config = {}

    @classmethod
    def get(cls, member:str = None):
        '''Get a named attribute from the proxy config. If member == None it returns the complete config dict'''

        if member:
            return cls.config.get(member, {})
        else:
            return cls.config