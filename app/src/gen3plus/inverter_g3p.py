import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3plus.inverter_g3p":
    from app.src.inverter import Inverter
    from app.src.gen3plus.connection_g3p import ConnectionG3PServer
    from app.src.gen3plus.connection_g3p import ConnectionG3PClient
else:  # pragma: no cover
    from inverter import Inverter
    from gen3plus.connection_g3p import ConnectionG3PServer
    from gen3plus.connection_g3p import ConnectionG3PClient


logger_mqtt = logging.getLogger('mqtt')


class InverterG3P(Inverter, ConnectionG3PServer):
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

    def __init__(self, reader: StreamReader, writer: StreamWriter, addr,
                 client_mode: bool = False):
        Inverter.__init__(self)
        ConnectionG3PServer.__init__(
            self, reader, writer, addr, None, client_mode=client_mode)
        self.addr = addr

    async def async_create_remote(self) -> None:
        await Inverter.async_create_remote(
            self, 'solarman', ConnectionG3PClient)

    def close(self) -> None:
        logging.debug(f'InverterG3P.close() {self.addr}')
        ConnectionG3PServer.close(self)
#        logger.debug (f'Inverter refs: {gc.get_referrers(self)}')
