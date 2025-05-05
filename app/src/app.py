import logging
import asyncio
import logging.handlers
from asyncio import StreamReader, StreamWriter
from quart import Quart, Response
from logging import config  # noqa F401
from proxy import Proxy
from inverter_ifc import InverterIfc
from gen3.inverter_g3 import InverterG3
from gen3plus.inverter_g3p import InverterG3P
from scheduler import Schedule
from server import Server
from web import Web
from web.wrapper import url_for

from modbus_tcp import ModbusTcp


class ProxyState:
    _is_up = False

    @staticmethod
    def is_up() -> bool:
        return ProxyState._is_up

    @staticmethod
    def set_up(value: bool):
        ProxyState._is_up = value


class HypercornLogHndl:
    access_hndl = []
    error_hndl = []
    must_fix = False
    HYPERC_ERR = 'hypercorn.error'
    HYPERC_ACC = 'hypercorn.access'

    @classmethod
    def save(cls):
        cls.access_hndl = logging.getLogger(
            cls.HYPERC_ACC).handlers
        cls.error_hndl = logging.getLogger(
            cls.HYPERC_ERR).handlers
        cls.must_fix = True

    @classmethod
    def restore(cls):
        if not cls.must_fix:
            return
        cls.must_fix = False
        access_hndl = logging.getLogger(
            cls.HYPERC_ACC).handlers
        if access_hndl != cls.access_hndl:
            print(' * Fix hypercorn.access setting')
            logging.getLogger(
                cls.HYPERC_ACC).handlers = cls.access_hndl

        error_hndl = logging.getLogger(
            cls.HYPERC_ERR).handlers
        if error_hndl != cls.error_hndl:
            print(' * Fix hypercorn.error setting')
            logging.getLogger(
                cls.HYPERC_ERR).handlers = cls.error_hndl


app = Quart(__name__,
            template_folder='web/templates',
            static_folder='web/static')
app.secret_key = 'JKLdks.dajlKKKdladkflKwolafallsdfl'
app.jinja_env.globals.update(url_for=url_for)


@app.route('/-/ready')
async def ready():
    if ProxyState.is_up():
        status = 200
        text = 'Is ready'
    else:
        status = 503
        text = 'Not ready'
    return Response(status=status, response=text)


@app.route('/-/healthy')
async def healthy():

    if ProxyState.is_up():
        # logging.info('web reqeust healthy()')
        for inverter in InverterIfc:
            try:
                res = inverter.healthy()
                if not res:
                    return Response(status=503, response="I have a problem")
            except Exception as err:
                logging.info(f'Exception:{err}')

    return Response(status=200, response="I'm fine")


async def handle_client(reader: StreamReader, writer: StreamWriter, inv_class):
    '''Handles a new incoming connection and starts an async loop'''

    with inv_class(reader, writer) as inv:
        await inv.local.ifc.server_loop()


@app.before_serving
async def startup_app():
    HypercornLogHndl.save()
    loop = asyncio.get_event_loop()
    Proxy.class_init()
    Schedule.start()
    ModbusTcp(loop)

    for inv_class, port in [(InverterG3, 5005), (InverterG3P, 10000)]:
        logging.info(f'listen on port: {port} for inverters')
        loop.create_task(asyncio.start_server(lambda r, w, i=inv_class:
                                              handle_client(r, w, i),
                                              '0.0.0.0', port))
    ProxyState.set_up(True)


@app.before_request
async def startup_request():
    HypercornLogHndl.restore()


@app.after_serving
async def handle_shutdown():   # pragma: no cover
    '''Close all TCP connections and stop the event loop'''

    logging.info('Shutdown due to SIGTERM')
    loop = asyncio.get_event_loop()
    ProxyState.set_up(False)

    #
    # first, disc all open TCP connections gracefully
    #
    for inverter in InverterIfc:
        await inverter.disc(True)

    logging.info('Proxy disconnecting done')

    await Proxy.class_close(loop)


server = Server(app, __name__ == "__main__")
Web(app, server.trans_path, server.rel_urls)

if __name__ == "__main__":  # pragma: no cover

    try:
        logging.info("Start Quart")
        app.run(host='0.0.0.0', port=8127, use_reloader=False,
                debug=Server.log_level == logging.DEBUG)
        logging.info("Quart stopped")

    except KeyboardInterrupt:
        pass
    except asyncio.exceptions.CancelledError:
        logging.info("Quart cancelled")

    finally:
        logging.info(f'Finally, exit Server "{Server.serv_name}"')
