import logging
import asyncio
import signal
import functools
import os
# from logging import config
from async_stream import AsyncStream
from inverter import Inverter
from config import Config


async def handle_client(reader, writer):
    '''Handles a new incoming connection and starts an async loop'''

    addr = writer.get_extra_info('peername')
    await Inverter(reader, writer, addr).server_loop(addr)


def handle_SIGTERM(loop):
    '''Close all TCP connections and stop the event loop'''

    logging.info('Shutdown due to SIGTERM')

    #
    # first, close all open TCP connections
    #
    for stream in AsyncStream:
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

    # read config file
    Config.read()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    Inverter.class_init()
    #
    # Register some UNIX Signal handler for a gracefully server shutdown
    # on Docker restart and stop
    #
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame),
                                functools.partial(handle_SIGTERM, loop))

    #
    # Create a task for our listening server. This must be a task! If we call
    # start_server directly out of our main task, the eventloop will be blocked
    # and we can't receive and handle the UNIX signals!
    #
    loop.create_task(asyncio.start_server(handle_client, '0.0.0.0', 5005))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        Inverter.class_close(loop)
        logging.info('Close event loop')
        loop.close()
        logging.info(f'Finally, exit Server "{serv_name}"')
