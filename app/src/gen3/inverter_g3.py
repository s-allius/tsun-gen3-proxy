import logging
from asyncio import StreamReader, StreamWriter

if __name__ == "app.src.gen3.inverter_g3":
    from app.src.inverter import Inverter
    from app.src.gen3.connection_g3 import ConnectionG3Server
    from app.src.gen3.connection_g3 import ConnectionG3Client
else:  # pragma: no cover
    from inverter import Inverter
    from gen3.connection_g3 import ConnectionG3Server
    from gen3.connection_g3 import ConnectionG3Client


logger_mqtt = logging.getLogger('mqtt')


class InverterG3(Inverter, ConnectionG3Server):
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

    def __init__(self, reader: StreamReader, writer: StreamWriter, addr):
        Inverter.__init__(self)
        ConnectionG3Server.__init__(self, reader, writer, addr, None)
        self.addr = addr

    async def async_create_remote(self) -> None:
        await Inverter.async_create_remote(
            self, 'tsun', ConnectionG3Client)

    def close(self) -> None:
        logging.debug(f'InverterG3.close() {self.addr}')
        ConnectionG3Server.close(self)
#         logging.info(f'Inverter refs: {gc.get_referrers(self)}')
