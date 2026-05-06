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
    """
    Main Server class responsible for application initialization, configuration loading,
    and logging setup.
    """
    serv_name = ''
    version = ''
    src_dir = ''

    # Default values for unit tests or fallback
    config_path = './config/'
    json_config = ''
    toml_config = ''
    trans_path = '../translations/'
    rel_urls = False
    log_path = './log/'
    log_backups = 0
    log_level = None

    def __init__(self, app: Quart, parse_args: bool):
        """
        Initializes the Server instance.

        1. Sets up service metadata from environment variables.
        2. Parses command line arguments (if enabled).
        3. Initializes the logging system.
        4. Builds the application configuration.
        5. Registers context processors for the Quart web app.

        Args:
            app (Quart): The Quart application instance.
            parse_args (bool): Whether to parse CLI arguments or use defaults.
        """
        self.serv_name = os.getenv('SERVICE_NAME', 'proxy')
        self.version = os.getenv('VERSION', 'unknown')
        self.src_dir = os.path.dirname(__file__) + '/'

        if parse_args:   # pragma: no cover
            self.parse_args(None)

        self.init_logging_system()
        self.build_config()

        @app.context_processor
        def utility_processor():
            """Injects global variables into Jinja2 templates."""
            var = {
                'version': self.version,
                'slug': os.getenv("SLUG"),
                'hostname': os.getenv("HOSTNAME"),
            }
            if var['slug']:
                var['hassio'] = True
                slug_len = len(var['slug'])
                var['addonname'] = f"{var['slug']}_{var['hostname'][slug_len+1:]}"
            return var

    def parse_args(self, arg_list: list[str] | None):
        """
        Parses command line arguments to configure paths and logging.

        Args:
            arg_list (list[str] | None): List of arguments to parse. 
                                         If None, sys.argv is used.
        """
        parser = argparse.ArgumentParser(description='Proxy Server Configuration')
        parser.add_argument('-c', '--config_path', type=str, default='./config/',
                            help='Path for the configuration files')
        parser.add_argument('-j', '--json_config', type=str,
                            help='Read user config from specific JSON file')
        parser.add_argument('-t', '--toml_config', type=str,
                            help='Read user config from specific TOML file')
        parser.add_argument('-l', '--log_path', type=str, default='./log/',
                            help='Path for the logging files')
        parser.add_argument('-b', '--log_backups', type=int, default=0,
                            help='Max number of daily log-file backups')
        parser.add_argument('-tr', '--trans_path', type=str, default='../translations/',
                            help='Path for translation files')
        parser.add_argument('-r', '--rel_urls', action="store_true",
                            help='Use relative dashboard URLs')
        
        args = parser.parse_args(arg_list)

        self.config_path = args.config_path
        self.json_config = args.json_config
        self.toml_config = args.toml_config
        self.trans_path = args.trans_path
        self.rel_urls = args.rel_urls
        self.log_path = args.log_path
        self.log_backups = args.log_backups

    def init_logging_system(self):
        """
        Configures the logging system based on the provided log path and level.
        Initializes the root and specific loggers (msg, conn, data, etc.).
        """
        setattr(logging.handlers, "log_path", self.log_path)
        setattr(logging.handlers, "log_backups", self.log_backups)
        os.makedirs(self.log_path, exist_ok=True)

        logging.config.fileConfig(self.src_dir + 'logging.ini')

        logging.info(f'Server "{self.serv_name} - {self.version}" starting...')
        logging.info(f'Current working directory: {os.getcwd()}')
        
        # Log active configuration parameters
        params = {
            "config_path": self.config_path, "json_config": self.json_config,
            "toml_config": self.toml_config, "trans_path": self.trans_path,
            "rel_urls": self.rel_urls, "log_path": self.log_path
        }
        for key, val in params.items():
            logging.info(f"{key:12}: {val}")

        logging.info(f"log_backups : {self.log_backups if self.log_backups > 0 else 'unlimited'}")
        
        self.log_level = self.get_log_level()
        logging.info('******')
        
        if self.log_level:
            loggers = ['', 'msg', 'conn', 'data', 'tracer', 'asyncio', 'test']
            for logger_name in loggers:
                logging.getLogger(logger_name).setLevel(self.log_level)

    def build_config(self):
        """
        Loads configuration from multiple sources in priority order:
        1. Default TOML
        2. Environment variables
        3. Config folder files (config.json/toml)
        4. CLI specified files
        """
        Config.init(ConfigReadToml(self.src_dir + "cnf/default_config.toml"),
                    log_path=self.log_path,
                    cnf_path=self.config_path)
        
        ConfigReadEnv()
        ConfigReadJson(self.config_path + "config.json")
        ConfigReadToml(self.config_path + "config.toml")
        
        if self.json_config:
            ConfigReadJson(self.json_config)
        if self.toml_config:
            ConfigReadToml(self.toml_config)
            
        config_err = Config.get_error()
        if config_err:
            logging.error(f'Configuration error: {config_err}')
            return

        logging.info('Configuration successfully loaded.')
        logging.info('******')

    def get_log_level(self) -> int | None:
        """
        Maps the LOG_LVL environment variable to logging module constants.

        Returns:
            int | None: The logging level (e.g., logging.DEBUG) or None if not set.
        """
        levels = {
            'DEBUG': logging.DEBUG,
            'WARN': logging.WARNING,
            'INFO': logging.INFO,
            'ERROR': logging.ERROR,
        }
        log_lvl_str = os.getenv('LOG_LVL', None)
        logging.info(f"LOG_LVL environment: {log_lvl_str}")

        return levels.get(log_lvl_str)


class ProxyState:
    """
    Thread-safe or global state tracker for the Proxy's readiness.
    """
    _is_up = False

    @staticmethod
    def is_up() -> bool:
        """Returns True if the proxy service is fully initialized."""
        return ProxyState._is_up

    @staticmethod
    def set_up(value: bool):
        """Sets the readiness state of the proxy."""
        ProxyState._is_up = value


class HypercornLogHndl:
    """
    Utility class to manage Hypercorn's logging handlers.
    Used to prevent Hypercorn from overriding custom logging configurations.
    """
    access_hndl = []
    error_hndl = []
    must_fix = False
    HYPERC_ERR = 'hypercorn.error'
    HYPERC_ACC = 'hypercorn.access'

    @classmethod
    def save(cls):
        """Saves current Hypercorn logger handlers."""
        cls.access_hndl = logging.getLogger(cls.HYPERC_ACC).handlers
        cls.error_hndl = logging.getLogger(cls.HYPERC_ERR).handlers
        cls.must_fix = True

    @classmethod
    def restore(cls):
        """Restores saved handlers to Hypercorn loggers if they were overwritten."""
        if not cls.must_fix:
            return
        cls.must_fix = False
        
        acc_logger = logging.getLogger(cls.HYPERC_ACC)
        if acc_logger.handlers != cls.access_hndl:
            print(' * Fixing hypercorn.access handlers')
            acc_logger.handlers = cls.access_hndl

        err_logger = logging.getLogger(cls.HYPERC_ERR)
        if err_logger.handlers != cls.error_hndl:
            print(' * Fixing hypercorn.error handlers')
            err_logger.handlers = cls.error_hndl


# Quart Application Setup
app = Quart(__name__,
            template_folder='web/templates',
            static_folder='web/static')

app.secret_key = 'JKLdks.dajlKKKdladkflKwolafallsdfl'
app.jinja_env.globals.update(url_for=url_for)
app.background_tasks = set()

# Initialize Server and Web UI
server = Server(app, __name__ == "__main__")
Web(app, server.trans_path, server.rel_urls)


@app.route('/-/ready')
async def ready():
    """
    Health check endpoint for Kubernetes/Docker.
    Returns 200 if the ProxyState is 'up', otherwise 503.
    """
    if ProxyState.is_up():
        return 'Is ready', 200
    return 'Not ready', 503

@app.route('/-/healthy')
async def healthy():
    """
    Detailed health check endpoint.
    
    Verifies not only if the proxy is up, but also checks the health status 
    of every connected inverter instance.
    
    Returns:
        Response: 200 OK if all systems and inverters are healthy, 
                  503 Service Unavailable otherwise.
    """
    if ProxyState.is_up():
        for inverter in InverterIfc:
            try:
                res = inverter.healthy()
                if not res:
                    return Response(status=503, response="I have a problem")
            except Exception as err:
                logging.info(f'Exception during health check: {err}')
                # Note: You might want to decide if an exception should also return 503

    return Response(status=200, response="I'm fine")


async def handle_client(reader: StreamReader,
                        writer: StreamWriter,
                        inv_class):    # pragma: no cover
    """
    Handles a new incoming TCP connection from an inverter.

    Args:
        reader (StreamReader): Asyncio stream reader for incoming data.
        writer (StreamWriter): Asyncio stream writer for outgoing data.
        inv_class (class): The specific inverter class (G3/G3P) to instantiate.
    """
    with inv_class(reader, writer) as inv:
        await inv.local.ifc.server_loop()


@app.before_serving
async def startup_app():    # pragma: no cover
    """
    Lifecycle hook: Executed before the Quart server starts serving requests.
    
    Initializes core components:
    - Saves logger states.
    - Initializes the Proxy and Scheduler.
    - Starts the Modbus TCP handler.
    - Starts TCP servers (listeners) for different inverter types based on configuration.
    """
    HypercornLogHndl.save()
    loop = asyncio.get_event_loop()
    Proxy.class_init()
    Schedule.start()
    ModbusTcp(loop)

    # Define supported inverter generations and their respective ports
    inverter_configs = [
        (InverterG3, 'tsun', 5005),
        (InverterG3P, 'solarman', 10000)
    ]

    for inv_class, config_id, port in inverter_configs:
        config_arr = Config.get(config_id)
        
        if not config_arr.get('listener'):
            logging.info(f'{config_id}.listener not enabled, skipping port {port}')
            continue
            
        logging.info(f'Listening on port: {port} for {config_id} inverters')
        
        # Start a TCP server for the specific inverter type
        task = loop.create_task(
            asyncio.start_server(
                lambda r, w, i=inv_class: handle_client(r, w, i),
                '0.0.0.0', port
            )
        )
        app.background_tasks.add(task)
        task.add_done_callback(app.background_tasks.discard)

    ProxyState.set_up(True)


@app.before_request
async def startup_request():
    """Ensures logging handlers are correctly set before each request."""
    HypercornLogHndl.restore()


@app.after_serving
async def handle_shutdown():   # pragma: no cover
    """
    Lifecycle hook: Executed during server shutdown (e.g., on SIGTERM).
    
    Performs a graceful shutdown:
    - Updates ProxyState.
    - Gracefully disconnects all active inverter TCP connections.
    - Cleans up background tasks and closes proxy resources.
    """
    logging.info('Shutdown due to SIGTERM')
    loop = asyncio.get_event_loop()
    ProxyState.set_up(False)

    # Disconnect all open TCP connections gracefully
    for inverter in InverterIfc:
        await inverter.disc(True)

    logging.info('Proxy disconnecting done')
    app.background_tasks.clear()

    await Proxy.class_close(loop)


if __name__ == "__main__":  # pragma: no cover
    """
    Entry point: Starts the Quart web server.
    """
    try:
        logging.info("Start Quart")
        # Run app on port 8127 - Debug mode enabled if log level is DEBUG
        app.run(
            host='0.0.0.0', 
            port=8127, 
            use_reloader=False,
            debug=server.log_level == logging.DEBUG
        )
        logging.info("Quart stopped")

    except KeyboardInterrupt:
        # Standard exit on Ctrl+C
        pass
    except asyncio.exceptions.CancelledError:
        logging.info("Quart cancelled")
    finally:
        logging.info(f'Finally, exit Server "{server.serv_name}"')
