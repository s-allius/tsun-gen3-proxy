import logging
import traceback
import asyncio
from itertools import chain

from cnf.config import Config
from gen3plus.inverter_g3p import InverterG3P
from infos import Infos

logger = logging.getLogger('conn')


class ModbusConn():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.addr = (host, port)
        self.inverter = None

    async def __aenter__(self) -> 'InverterG3P':
        '''Establish a client connection to the TSUN cloud'''
        connection = asyncio.open_connection(self.host, self.port)
        reader, writer = await connection
        self.inverter = InverterG3P(reader, writer,
                                    client_mode=True)
        self.inverter.__enter__()
        stream = self.inverter.local.stream
        logging.info(f'[{stream.node_id}:{stream.conn_no}] '
                     f'Connected to {self.addr}')
        Infos.inc_counter('Inverter_Cnt')
        Infos.inc_counter('ClientMode_Cnt')
        await self.inverter.local.ifc.publish_outstanding_mqtt()
        return self.inverter

    async def __aexit__(self, exc_type, exc, tb):
        Infos.dec_counter('ClientMode_Cnt')
        Infos.dec_counter('Inverter_Cnt')
        if self.inverter.local.ifc.inv_disc_cb:
            self.inverter.local.ifc.inv_disc_cb()
        await self.inverter.local.ifc.publish_outstanding_mqtt()
        self.inverter.__exit__(exc_type, exc, tb)


class ModbusTcp():

    def __init__(self, loop, tim_restart=10) -> None:
        self.tim_restart = tim_restart
        self.background_tasks = set()

        inverters = Config.get('inverters')
        batteries = Config.get('batteries')
        # logging.info(f'Inverters: {inverters}')

        for _, inv in chain(inverters.items(), batteries.items()):
            if (type(inv) is dict
               and 'monitor_sn' in inv
               and 'client_mode' in inv):
                client = inv['client_mode']
                logger.info(f"'client_mode' for Monitoring-SN: {inv['monitor_sn']} host: {client['host']}:{client['port']}, forward: {client['forward']}")  # noqa: E501
                task = loop.create_task(
                    self.modbus_loop(client['host'],
                                     client['port'],
                                     inv['monitor_sn'],
                                     client['forward']))
                self.background_tasks.add(task)
                task.add_done_callback(self.background_tasks.discard)

    async def modbus_loop(self, host, port,
                          snr: int, forward: bool) -> None:
        '''Loop for receiving messages from the TSUN cloud (client-side)'''
        while True:
            try:
                async with ModbusConn(host, port) as inverter:
                    stream = inverter.local.stream
                    stream.send_start_cmd(snr, host, forward)
                    await stream.ifc.loop()
                    logger.info(f'[{stream.node_id}:{stream.conn_no}] '
                                f'Connection closed - Shutdown: '
                                f'{stream.shutdown_started}')
                    if stream.shutdown_started:
                        return
                del inverter  # decrease ref counter after the with block

            except (ConnectionRefusedError, TimeoutError) as error:
                logging.debug(f'Inv-conn:{error}')

            except OSError as error:
                if error.errno == 113:  # pragma: no cover
                    logging.debug(f'os-error:{error}')
                else:
                    logging.info(f'os-error: {error}')

            except Exception:
                logging.error(
                    f"ModbusTcpCreate: Exception for {(host, port)}:\n"
                    f"{traceback.format_exc()}")

            await asyncio.sleep(self.tim_restart)
