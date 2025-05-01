import logging
import asyncio
import logging.handlers
import os
import argparse
from asyncio import StreamReader, StreamWriter
from quart import Quart, Response
from logging import config  # noqa F401
from proxy import Proxy
from inverter_ifc import InverterIfc
from gen3.inverter_g3 import InverterG3
from gen3plus.inverter_g3p import InverterG3P
from scheduler import Schedule
from cnf.config import Config
from cnf.config_read_env import ConfigReadEnv
from cnf.config_read_toml import ConfigReadToml
from cnf.config_read_json import ConfigReadJson
from web import Web
from web.wrapper import url_for

from modbus_tcp import ModbusTcp


class ProxyState:
    _is_up = False

    @staticmethod
    def is_up() -> bool:
        return ProxyState._is_up

    @staticmethod
    def set_up(value: bool):
        ProxyState._is_up = value


app = Quart(__name__,
            template_folder='web/templates',
            static_folder='web/static')
app.secret_key = 'JKLdks.dajlKKKdladkflKwolafallsdfl'
app.jinja_env.globals.update(url_for=url_for)


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


async def handle_client(reader: StreamReader, writer: StreamWriter, inv_class):
    '''Handles a new incoming connection and starts an async loop'''

    with inv_class(reader, writer) as inv:
        await inv.local.ifc.server_loop()


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

    #
    # now cancel all remaining (pending) tasks
    #
    for task in asyncio.all_tasks():
        if task == asyncio.current_task():
            continue
        task.cancel()
    logging.info('Proxy cancelling done')

    await Proxy.class_close(loop)


def get_log_level() -> int | None:
    '''checks if LOG_LVL is set in the environment and returns the
    corresponding logging.LOG_LEVEL'''
    switch = {
        'DEBUG': logging.DEBUG,
        'WARN': logging.WARNING,
        'INFO': logging.INFO,
        'ERROR': logging.ERROR,
    }
    log_level = os.getenv('LOG_LVL', None)
    logging.info(f"LOG_LVL    : {log_level}")

    return switch.get(log_level, None)


def main():   # pragma: no cover
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
    parser.add_argument('-r', '--rel_urls', type=bool,
                        default=False,
                        help='use relative dashboard urls')
    args = parser.parse_args()
    #
    # Setup our daily, rotating logger
    #
    serv_name = os.getenv('SERVICE_NAME', 'proxy')
    version = os.getenv('VERSION', 'unknown')

    setattr(logging.handlers, "log_path", args.log_path)
    setattr(logging.handlers, "log_backups", args.log_backups)
    os.makedirs(args.log_path, exist_ok=True)

    src_dir = os.path.dirname(__file__) + '/'
    logging.config.fileConfig(src_dir + 'logging.ini')
    logging.info(f'Server "{serv_name} - {version}" will be started')
    logging.info(f'current dir: {os.getcwd()}')
    logging.info(f"config_path: {args.config_path}")
    logging.info(f"json_config: {args.json_config}")
    logging.info(f"toml_config: {args.toml_config}")
    logging.info(f"trans_path:  {args.trans_path}")
    logging.info(f"rel_urls:    {args.rel_urls}")
    logging.info(f"log_path:    {args.log_path}")
    if args.log_backups == 0:
        logging.info("log_backups: unlimited")
    else:
        logging.info(f"log_backups: {args.log_backups} days")
    log_level = get_log_level()
    logging.info('******')
    if log_level:
        # set lowest-severity for 'root', 'msg', 'conn' and 'data' logger
        logging.getLogger().setLevel(log_level)
        logging.getLogger('msg').setLevel(log_level)
        logging.getLogger('conn').setLevel(log_level)
        logging.getLogger('data').setLevel(log_level)
        logging.getLogger('tracer').setLevel(log_level)
        logging.getLogger('asyncio').setLevel(log_level)
        # logging.getLogger('mqtt').setLevel(log_level)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # read config file
    Config.init(ConfigReadToml(src_dir + "cnf/default_config.toml"),
                log_path=args.log_path)
    ConfigReadEnv()
    ConfigReadJson(args.config_path + "config.json")
    ConfigReadToml(args.config_path + "config.toml")
    ConfigReadJson(args.json_config)
    ConfigReadToml(args.toml_config)
    config_err = Config.get_error()

    if config_err is not None:
        logging.info(f'config_err: {config_err}')
        return

    logging.info('******')

    Proxy.class_init()
    Schedule.start()
    ModbusTcp(loop)
    Web(app, args.trans_path, args.rel_urls)

    #
    # Create tasks for our listening servers. These must be tasks! If we call
    # start_server directly out of our main task, the eventloop will be blocked
    # and we can't receive and handle the UNIX signals!
    #
    for inv_class, port in [(InverterG3, 5005), (InverterG3P, 10000)]:
        logging.info(f'listen on port: {port} for inverters')
        loop.create_task(asyncio.start_server(lambda r, w, i=inv_class:
                                              handle_client(r, w, i),
                                              '0.0.0.0', port))

    loop.set_debug(log_level == logging.DEBUG)
    try:
        ProxyState.set_up(True)
        logging.info("Start Quart")
        app.run(host='0.0.0.0', port=8127, use_reloader=False, loop=loop,
                debug=True,)
        logging.info("Quart stopped")

    except KeyboardInterrupt:
        pass
    except asyncio.exceptions.CancelledError:
        logging.info("Quart cancelled")

    finally:
        logging.debug('Close event loop')
        loop.close()
        logging.info(f'Finally, exit Server "{serv_name}"')


if __name__ == "__main__":  # pragma: no cover
    main()
