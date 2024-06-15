import logging
import asyncio
import signal
import os
from asyncio import StreamReader, StreamWriter
from aiohttp import web
from logging import config  # noqa F401
from messages import Message
from inverter import Inverter
from gen3.inverter_g3 import InverterG3
from gen3plus.inverter_g3p import InverterG3P
from scheduler import Schedule
from config import Config

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
        for stream in Message:
            try:
                res = stream.healthy()
                if not res:
                    return web.Response(status=503, text="I have a problem")
            except Exception as err:
                logging.info(f'Exception:{err}')

    return web.Response(status=200, text="I'm fine")


async def webserver(runner, addr, port):
    await runner.setup()
    site = web.TCPSite(runner, addr, port)
    await site.start()
    logging.info(f'HTTP server listen on port: {port}')

    while True:
        await asyncio.sleep(3600)  # sleep forever


async def handle_client(reader: StreamReader, writer: StreamWriter):
    '''Handles a new incoming connection and starts an async loop'''

    addr = writer.get_extra_info('peername')
    await InverterG3(reader, writer, addr).server_loop(addr)


async def handle_client_v2(reader: StreamReader, writer: StreamWriter):
    '''Handles a new incoming connection and starts an async loop'''

    addr = writer.get_extra_info('peername')
    await InverterG3P(reader, writer, addr).server_loop(addr)


async def handle_shutdown(loop, runner):
    '''Close all TCP connections and stop the event loop'''

    logging.info('Shutdown due to SIGTERM')
    await runner.cleanup()
    logging.info('HTTP server stopped')

    #
    # first, disc all open TCP connections gracefully
    #
    for stream in Message:
        try:
            await asyncio.wait_for(stream.disc(), 2)
        except Exception:
            pass
    logging.info('Disconnecting done')

    #
    # second, close all open TCP connections
    #
    for stream in Message:
        stream.close()

    #
    # at last, we stop the loop
    #
    loop.stop()

    logging.info('Shutdown complete')


def get_log_level() -> int:
    '''checks if LOG_LVL is set in the environment and returns the
    corresponding logging.LOG_LEVEL'''
    log_level = os.getenv('LOG_LVL', 'INFO')
    if log_level == 'DEBUG':
        log_level = logging.DEBUG
    elif log_level == 'WARN':
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    return log_level


if __name__ == "__main__":
    #
    # Setup our daily, rotating logger
    #
    serv_name = os.getenv('SERVICE_NAME', 'proxy')
    version = os.getenv('VERSION', 'unknown')

    logging.config.fileConfig('logging.ini')
    logging.info(f'Server "{serv_name} - {version}" will be started')

    # set lowest-severity for 'root', 'msg', 'conn' and 'data' logger
    log_level = get_log_level()
    logging.getLogger().setLevel(log_level)
    logging.getLogger('msg').setLevel(log_level)
    logging.getLogger('conn').setLevel(log_level)
    logging.getLogger('data').setLevel(log_level)
    logging.getLogger('tracer').setLevel(log_level)
    # logging.getLogger('mqtt').setLevel(log_level)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # read config file
    ConfigErr = Config.class_init()
    logging.info(f'ConfigErr: {ConfigErr}')
    Inverter.class_init()
    Schedule.start()

    #
    # Setup webserver application and runner
    #
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)

    #
    # Register some UNIX Signal handler for a gracefully server shutdown
    # on Docker restart and stop
    #
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame),
                                lambda loop=loop: asyncio.create_task(
                                    handle_shutdown(loop, runner)))

    #
    # Create tasks for our listening servers. These must be tasks! If we call
    # start_server directly out of our main task, the eventloop will be blocked
    # and we can't receive and handle the UNIX signals!
    #
    loop.create_task(asyncio.start_server(handle_client, '0.0.0.0', 5005))
    loop.create_task(asyncio.start_server(handle_client_v2, '0.0.0.0', 10000))
    loop.create_task(webserver(runner, '0.0.0.0', 8127))

    try:
        if ConfigErr is None:
            proxy_is_up = True
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        proxy_is_up = False
        Inverter.class_close(loop)
        logging.info('Close event loop')
        loop.close()
        logging.info(f'Finally, exit Server "{serv_name}"')
