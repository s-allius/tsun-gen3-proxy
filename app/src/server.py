import logging
import asyncio
import logging.handlers
import signal
import os
import argparse
from asyncio import StreamReader, StreamWriter
from aiohttp import web
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
from modbus_tcp import ModbusTcp

routes = web.RouteTableDef()
proxy_is_up = False


@routes.get('/')
async def hello(request):
    return web.Response(text="Hello, world")


@routes.get('/-/ready')
async def ready(request):
    if proxy_is_up:
        status = 200
        text = 'Is ready'
    else:
        status = 503
        text = 'Not ready'
    return web.Response(status=status, text=text)


@routes.get('/-/healthy')
async def healthy(request):

    if proxy_is_up:
        # logging.info('web reqeust healthy()')
        for inverter in InverterIfc:
            try:
                res = inverter.healthy()
                if not res:
                    return web.Response(status=503, text="I have a problem")
            except Exception as err:
                logging.info(f'Exception:{err}')

    return web.Response(status=200, text="I'm fine")


async def webserver(addr, port):
    '''coro running our webserver'''
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)

    await runner.setup()
    site = web.TCPSite(runner, addr, port)
    await site.start()
    logging.info(f'HTTP server listen on port: {port}')

    try:
        # Normal interaction with aiohttp
        while True:
            await asyncio.sleep(3600)  # sleep forever
    except asyncio.CancelledError:
        logging.info('HTTP server cancelled')
        await runner.cleanup()
        logging.debug('HTTP cleanup done')


async def handle_client(reader: StreamReader, writer: StreamWriter, inv_class):
    '''Handles a new incoming connection and starts an async loop'''

    with inv_class(reader, writer) as inv:
        await inv.local.ifc.server_loop()


async def handle_shutdown(web_task):
    '''Close all TCP connections and stop the event loop'''

    logging.info('Shutdown due to SIGTERM')
    global proxy_is_up
    proxy_is_up = False

    #
    # first, disc all open TCP connections gracefully
    #
    for inverter in InverterIfc:
        await inverter.disc(True)

    logging.info('Proxy disconnecting done')

    #
    # second, cancel the web server
    #
    web_task.cancel()
    await web_task

    #
    # now cancel all remaining (pending) tasks
    #
    pending = asyncio.all_tasks()
    for task in pending:
        task.cancel()

    #
    # at last, start a coro for stopping the loop
    #
    logging.debug("Stop event loop")
    loop.stop()


def get_log_level() -> int:
    '''checks if LOG_LVL is set in the environment and returns the
    corresponding logging.LOG_LEVEL'''
    log_level = os.getenv('LOG_LVL', 'INFO')
    logging.info(f"LOG_LVL    : {log_level}")

    if log_level == 'DEBUG':
        log_level = logging.DEBUG
    elif log_level == 'WARN':
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    return log_level


if __name__ == "__main__":   # pragma: no cover
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
    args = parser.parse_args()
    #
    # Setup our daily, rotating logger
    #
    serv_name = os.getenv('SERVICE_NAME', 'proxy')
    version = os.getenv('VERSION', 'unknown')

    setattr(logging.handlers, "log_path", args.log_path)
    setattr(logging.handlers, "log_backups", args.log_backups)

    logging.config.fileConfig('logging.ini')
    logging.info(f'Server "{serv_name} - {version}" will be started')
    logging.info(f'current dir: {os.getcwd()}')
    logging.info(f"config_path: {args.config_path}")
    logging.info(f"json_config: {args.json_config}")
    logging.info(f"toml_config: {args.toml_config}")
    logging.info(f"log_path:    {args.log_path}")
    if args.log_backups == 0:
        logging.info("log_backups: unlimited")
    else:
        logging.info(f"log_backups: {args.log_backups} days")
    log_level = get_log_level()
    logging.info('******')

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
    Config.init(ConfigReadToml("default_config.toml"))
    ConfigReadEnv()
    ConfigReadJson(args.config_path + "config.json")
    ConfigReadToml(args.config_path + "config.toml")
    ConfigReadJson(args.json_config)
    ConfigReadToml(args.toml_config)
    ConfigErr = Config.get_error()

    if ConfigErr is not None:
        logging.info(f'ConfigErr: {ConfigErr}')
    logging.info('******')

    Proxy.class_init()
    Schedule.start()
    ModbusTcp(loop)

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
    web_task = loop.create_task(webserver('0.0.0.0', 8127))

    #
    # Register some UNIX Signal handler for a gracefully server shutdown
    # on Docker restart and stop
    #
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame),
                                lambda loop=loop: asyncio.create_task(
                                    handle_shutdown(web_task)))

    loop.set_debug(log_level == logging.DEBUG)
    try:
        if ConfigErr is None:
            proxy_is_up = True
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        logging.info("Event loop is stopped")
        Proxy.class_close(loop)
        logging.debug('Close event loop')
        loop.close()
        logging.info(f'Finally, exit Server "{serv_name}"')
