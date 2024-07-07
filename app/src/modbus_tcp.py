import logging
import traceback
import asyncio
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

    def __init__(self, loop, host, port, snr: int) -> None:
        loop.create_task(self.modbus_loop(host, port, snr))

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
                logging.info(f'{error}')

            except Exception:
                logging.error(
                    f"ModbusTcpCreate: Exception for {(host,port)}:\n"
                    f"{traceback.format_exc()}")

            await asyncio.sleep(10)
