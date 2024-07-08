import logging
import traceback
import asyncio
from config import Config

# import gc
from gen3plus.inverter_g3p import InverterG3P

logger = logging.getLogger('conn')


class ModbusConn():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.addr = (host, port)
        self.stream = None

    async def __aenter__(self) -> 'InverterG3P':
        '''Establish a client connection to the TSUN cloud'''
        connection = asyncio.open_connection(self.host, self.port)
        reader, writer = await connection
        self.stream = InverterG3P(reader, writer, self.addr)
        logging.info(f'[{self.stream.node_id}:{self.stream.conn_no}] '
                     f'Connected to {self.addr}')
        self.stream.inc_counter('Inverter_Cnt')
        return self.stream

    async def __aexit__(self, exc_type, exc, tb):
        self.stream.dec_counter('Inverter_Cnt')


class ModbusTcp():

    def __init__(self, loop) -> None:
        inverters = Config.get('inverters')
        # logging.info(f'Inverters: {inverters}')

        for inv in inverters.values():
            if (type(inv) is dict
               and 'monitor_sn' in inv
               and 'client_mode' in inv):
                client = inv['client_mode']
                # logging.info(f"SerialNo:{inv['monitor_sn']} host:{client['host']} port:{client['port']}")  # noqa: E501
                loop.create_task(self.modbus_loop(client['host'],
                                                  client['port'],
                                                  inv['monitor_sn']))

    async def modbus_loop(self, host, port, snr: int) -> None:
        '''Loop for receiving messages from the TSUN cloud (client-side)'''
        while True:
            try:
                async with ModbusConn(host, port) as stream:
                    await stream.send_start_cmd(snr)
                    await stream.loop()
                    logger.info(f'[{stream.node_id}:{stream.conn_no}] '
                                f'Connection closed - Shutdown: '
                                f'{stream.shutdown_started}')
                    if stream.shutdown_started:
                        return

            except (ConnectionRefusedError, TimeoutError) as error:
                logging.debug(f'Inv-conn:{error}')

            except OSError as error:
                logging.info(f'os-error: {error}')

            except Exception:
                logging.error(
                    f"ModbusTcpCreate: Exception for {(host,port)}:\n"
                    f"{traceback.format_exc()}")

            await asyncio.sleep(10)
