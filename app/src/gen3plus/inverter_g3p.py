import logging
from config import Config
from gen3plus.async_stream import AsyncStreamV2

# import gc

# logger = logging.getLogger('conn')
logger_mqtt = logging.getLogger('mqtt')


class InverterG3P(AsyncStreamV2):
    '''class Inverter is a derivation of an Async_Stream

    The class has some class method for managing common resources like a
    connection to the MQTT broker or proxy error counter which are common
    for all inverter connection

    Instances of the class are connections to an inverter and can have an
    optional link to an remote connection to the TSUN cloud. A remote
    connection dies with the inverter connection.

    class methods:
        class_init():  initialize the common resources of the proxy (MQTT
                       broker, Proxy DB, etc). Must be called before the
                       first inverter instance can be created
        class_close(): release the common resources of the proxy. Should not
                       be called before any instances of the class are
                       destroyed

    methods:
        server_loop(addr): Async loop method for receiving messages from the
                           inverter (server-side)
        client_loop(addr): Async loop method for receiving messages from the
                           TSUN cloud (client-side)
        async_create_remote(): Establish a client connection to the TSUN cloud
        async_publ_mqtt(): Publish data to MQTT broker
        close(): Release method which must be called before a instance can be
                 destroyed
    '''
    @classmethod
    def class_init(cls) -> None:
        logging.debug('InverterG3P.class_init')
        # initialize the proxy statistics
        # Infos.static_init()
        # cls.db_stat = Infos()

        ha = Config.get('ha')
        cls.entity_prfx = ha['entity_prefix'] + '/'
        cls.discovery_prfx = ha['discovery_prefix'] + '/'
        cls.proxy_node_id = ha['proxy_node_id'] + '/'
        cls.proxy_unique_id = ha['proxy_unique_id']

    @classmethod
    def class_close(cls, loop) -> None:
        logging.debug('InverterG3P.class_close')
        logging.info('Close MQTT Task')

    def __init__(self, reader, writer, addr):
        super().__init__(reader, writer, addr, None, True)
        pass

    async def server_loop(self, addr):
        '''Loop for receiving messages from the inverter (server-side)'''
        logging.info(f'Accept connection V2 from  {addr}')
        # self.inc_counter('Inverter_Cnt')
        await self.loop()
        # self.dec_counter('Inverter_Cnt')
        logging.info(f'Server loop stopped for r{self.r_addr}')

    def close(self) -> None:
        logging.debug(f'InverterG3P.close() l{self.l_addr} | r{self.r_addr}')
        super().close()         # call close handler in the parent class
#        logger.debug (f'Inverter refs: {gc.get_referrers(self)}')

    def __del__(self):
        logging.debug("InverterG3P.__del__")
        super().__del__()
