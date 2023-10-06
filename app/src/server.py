import logging, asyncio, signal, functools, os
from logging import config
from async_stream import AsyncStream
from inverter import Inverter
from config import Config
from mqtt import Mqtt

    
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
    

    



if __name__ == "__main__":
    #
    # Setup our daily, rotating logger
    #
    serv_name = os.getenv('SERVICE_NAME', 'proxy')
    version = os.getenv('VERSION', 'unknown')

    logging.config.fileConfig('logging.ini')
    logging.info(f'Server "{serv_name} - {version}" will be started')
    logging.getLogger().setLevel(logging.DEBUG if __debug__ else logging.INFO)
    
    # read config file
    Config.read()    

    loop = asyncio.get_event_loop()

    # call Mqtt singleton to establisch the connection to the mqtt broker
    mqtt = Mqtt()
    
    #
    # Register some UNIX Signal handler for a gracefully server shutdown on Docker restart and stop
    #  
    for signame in ('SIGINT','SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame), functools.partial(handle_SIGTERM, loop))

    #
    # Create a task for our listening server. This must be a task! If we call start_server directly out
    # of our main task, the eventloop will be blocked and we can't receive and handle the UNIX signals!
    #   
    loop.create_task(asyncio.start_server(handle_client, '0.0.0.0', 5005))
       
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        logging.info ('Close MQTT Task')        
        loop.run_until_complete(mqtt.close())
        mqtt = None   # release the last reference to the singleton
        logging.info ('Close event loop')        
        loop.close()
        logging.info (f'Finally, exit Server "{serv_name}"')
    