import logging
import logging.handlers
from logging import config  # noqa F401
import asyncio
from asyncio import StreamReader, StreamWriter
import os
import argparse
from quart import Quart, Response

from cnf.config import Config
from cnf.config_read_env import ConfigReadEnv
from cnf.config_read_toml import ConfigReadToml
from cnf.config_read_json import ConfigReadJson
from web import Web
from web.wrapper import url_for
from proxy import Proxy
from inverter_ifc import InverterIfc
from gen3.inverter_g3 import InverterG3
from gen3plus.inverter_g3p import InverterG3P
from scheduler import Schedule

from modbus_tcp import ModbusTcp


class Server():
    serv_name = ''
    version = ''
    src_dir = ''

    ####
    # The following default values are used for the unit tests only, since
    # `Server.parse_args()' will not be called during test setup.
    # Ofcorse, we can call `Server.parse_args()' in a test case explicitly
    # to overwrite this values
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
            var = {'version': self.version,
                   'slug': os.getenv("SLUG"),
                   'hostname': os.getenv("HOSTNAME"),
                   }
            if var['slug']:
                var['hassio'] = True
                slug_len = len(var['slug'])
                var['addonname'] = var['slug'] + '_' + \
                    var['hostname'][slug_len+1:]
            return var

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

    def init_logging_system(self):
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
                    log_path=self.log_path,
                    cnf_path=self.config_path)
        ConfigReadEnv()
        ConfigReadJson(self.config_path + "config.json")
        ConfigReadToml(self.config_path + "config.toml")
        ConfigReadJson(self.json_config)
        ConfigReadToml(self.toml_config)
        config_err = Config.get_error()

        if config_err is not None:
            logging.info(f'config_err: {config_err}')
            return

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


class ProxyState:
    _is_up = False

    @staticmethod
    def is_up() -> bool:
        return ProxyState._is_up

    @staticmethod
    def set_up(value: bool):
        ProxyState._is_up = value


class HypercornLogHndl:
    access_hndl = []
    error_hndl = []
    must_fix = False
    HYPERC_ERR = 'hypercorn.error'
    HYPERC_ACC = 'hypercorn.access'

    @classmethod
    def save(cls):
        cls.access_hndl = logging.getLogger(
            cls.HYPERC_ACC).handlers
        cls.error_hndl = logging.getLogger(
            cls.HYPERC_ERR).handlers
        cls.must_fix = True

    @classmethod
    def restore(cls):
        if not cls.must_fix:
            return
        cls.must_fix = False
        access_hndl = logging.getLogger(
            cls.HYPERC_ACC).handlers
        if access_hndl != cls.access_hndl:
            print(' * Fix hypercorn.access setting')
            logging.getLogger(
                cls.HYPERC_ACC).handlers = cls.access_hndl

        error_hndl = logging.getLogger(
            cls.HYPERC_ERR).handlers
        if error_hndl != cls.error_hndl:
            print(' * Fix hypercorn.error setting')
            logging.getLogger(
                cls.HYPERC_ERR).handlers = cls.error_hndl


app = Quart(__name__,
            template_folder='web/templates',
            static_folder='web/static')
app.secret_key = 'JKLdks.dajlKKKdladkflKwolafallsdfl'
app.jinja_env.globals.update(url_for=url_for)
app.background_tasks = set()
server = Server(app, __name__ == "__main__")
Web(app, server.trans_path, server.rel_urls)


@app.route('/-/ready')
async def ready():
    if ProxyState.is_up():
        status = 200
        text = 'Is ready'
    else:
        status = 503
        text = 'Not ready'
    return Response(status=status, response=text)


@app.route('/-/healthy')
async def healthy():

    if ProxyState.is_up():
        # logging.info('web reqeust healthy()')
        for inverter in InverterIfc:
            try:
                res = inverter.healthy()
                if not res:
                    return Response(status=503, response="I have a problem")
            except Exception as err:
                logging.info(f'Exception:{err}')

    return Response(status=200, response="I'm fine")


async def handle_client(reader: StreamReader,
                        writer: StreamWriter,
                        inv_class):    # pragma: no cover
    '''Handles a new incoming connection and starts an async loop'''

    with inv_class(reader, writer) as inv:
        await inv.local.ifc.server_loop()


@app.before_serving
async def startup_app():    # pragma: no cover
    HypercornLogHndl.save()
    loop = asyncio.get_event_loop()
    Proxy.class_init()
    Schedule.start()
    ModbusTcp(loop)

    for inv_class, port in [(InverterG3, 5005), (InverterG3P, 10000)]:
        logging.info(f'listen on port: {port} for inverters')
        task = loop.create_task(
            asyncio.start_server(lambda r, w, i=inv_class:
                                 handle_client(r, w, i),
                                 '0.0.0.0', port))
        app.background_tasks.add(task)
        task.add_done_callback(app.background_tasks.discard)

    ProxyState.set_up(True)


@app.before_request
async def startup_request():
    HypercornLogHndl.restore()


@app.after_serving
async def handle_shutdown():   # pragma: no cover
    '''Close all TCP connections and stop the event loop'''

    logging.info('Shutdown due to SIGTERM')
    loop = asyncio.get_event_loop()
    ProxyState.set_up(False)

    #
    # first, disc all open TCP connections gracefully
    #
    for inverter in InverterIfc:
        await inverter.disc(True)

    logging.info('Proxy disconnecting done')
    app.background_tasks.clear()

    await Proxy.class_close(loop)


if __name__ == "__main__":  # pragma: no cover

    try:
        logging.info("Start Quart")
        app.run(host='0.0.0.0', port=8127, use_reloader=False,
                debug=server.log_level == logging.DEBUG)
        logging.info("Quart stopped")

    except KeyboardInterrupt:
        pass
    except asyncio.exceptions.CancelledError:
        logging.info("Quart cancelled")

    finally:
        logging.info(f'Finally, exit Server "{server.serv_name}"')
