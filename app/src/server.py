import logging
import logging.handlers
import os
import argparse
from cnf.config import Config
from cnf.config_read_env import ConfigReadEnv
from cnf.config_read_toml import ConfigReadToml
from cnf.config_read_json import ConfigReadJson


class Server():
    serv_name = ''
    version = ''
    src_dir = ''
    config_path = './config/'
    json_config = ''
    toml_config = ''
    trans_path = '../translations/'
    rel_urls = False
    log_path = './log/'
    log_backups = 0
    log_level = None

    def __init__(self, app, parse_args: bool):
        ''' Applikation Setup

    1. Read cli arguments
    2. Init the logging system by the ini file
    3. Log the config parms
    4. Set the log-levels
    5. Read the build the config for the app
    '''
        self.serv_name = os.getenv('SERVICE_NAME', 'proxy')
        self.version = os.getenv('VERSION', 'unknown')
        self.src_dir = os.path.dirname(__file__) + '/'
        if parse_args:   # pragma: no cover
            self.parse_args(None)
        self.init_logging_system()
        self.build_config()

        @app.context_processor
        def utility_processor():
            return dict(version=self.version)

    def parse_args(self, arg_list: list[str] | None):
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--config_path', type=str,
                            default='./config/',
                            help='set path for the configuration files')
        parser.add_argument('-j', '--json_config', type=str,
                            help='read user config from json-file')
        parser.add_argument('-t', '--toml_config', type=str,
                            help='read user config from toml-file')
        parser.add_argument('-l', '--log_path', type=str,
                            default='./log/',
                            help='set path for the logging files')
        parser.add_argument('-b', '--log_backups', type=int,
                            default=0,
                            help='set max number of daily log-files')
        parser.add_argument('-tr', '--trans_path', type=str,
                            default='../translations/',
                            help='set path for the translations files')
        parser.add_argument('-r', '--rel_urls', action="store_true",
                            help='use relative dashboard urls')
        args = parser.parse_args(arg_list)

        self.config_path = args.config_path
        self.json_config = args.json_config
        self.toml_config = args.toml_config
        self.trans_path = args.trans_path
        self.rel_urls = args.rel_urls
        self.log_path = args.log_path
        self.log_backups = args.log_backups

    def init_logging_system(self):   # pragma: no cover

        setattr(logging.handlers, "log_path", self.log_path)
        setattr(logging.handlers, "log_backups", self.log_backups)
        os.makedirs(self.log_path, exist_ok=True)

        logging.config.fileConfig(self.src_dir + 'logging.ini')

        logging.info(
            f'Server "{self.serv_name} - {self.version}" will be started')
        logging.info(f'current dir: {os.getcwd()}')
        logging.info(f"config_path: {self.config_path}")
        logging.info(f"json_config: {self.json_config}")
        logging.info(f"toml_config: {self.toml_config}")
        logging.info(f"trans_path:  {self.trans_path}")
        logging.info(f"rel_urls:    {self.rel_urls}")
        logging.info(f"log_path:    {self.log_path}")
        if self.log_backups == 0:
            logging.info("log_backups: unlimited")
        else:
            logging.info(f"log_backups: {self.log_backups} days")
        self.log_level = self.get_log_level()
        logging.info('******')
        if self.log_level:
            # set lowest-severity for 'root', 'msg', 'conn' and 'data' logger
            logging.getLogger().setLevel(self.log_level)
            logging.getLogger('msg').setLevel(self.log_level)
            logging.getLogger('conn').setLevel(self.log_level)
            logging.getLogger('data').setLevel(self.log_level)
            logging.getLogger('tracer').setLevel(self.log_level)
            logging.getLogger('asyncio').setLevel(self.log_level)
            # logging.getLogger('mqtt').setLevel(self.log_level)

    def build_config(self):
        # read config file
        Config.init(ConfigReadToml(self.src_dir + "cnf/default_config.toml"),
                    log_path=self.log_path)
        ConfigReadEnv()
        ConfigReadJson(self.config_path + "config.json")
        ConfigReadToml(self.config_path + "config.toml")
        ConfigReadJson(self.json_config)
        ConfigReadToml(self.toml_config)
        config_err = Config.get_error()

        if config_err is not None:
            logging.info(f'config_err: {config_err}')
            return  # fixme raise an exception

        logging.info('******')

    def get_log_level(self) -> int | None:
        '''checks if LOG_LVL is set in the environment and returns the
        corresponding logging.LOG_LEVEL'''
        switch = {
            'DEBUG': logging.DEBUG,
            'WARN': logging.WARNING,
            'INFO': logging.INFO,
            'ERROR': logging.ERROR,
        }
        log_lvl = os.getenv('LOG_LVL', None)
        logging.info(f"LOG_LVL    : {log_lvl}")

        return switch.get(log_lvl, None)
