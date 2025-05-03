# test_with_pytest.py
import pytest
from server import app
from web import Web, web
from async_stream import AsyncStreamClient
from gen3plus.inverter_g3p import InverterG3P
from test_inverter_g3p import FakeReader, FakeWriter, config_conn
from cnf.config import Config
from mock import patch
from proxy import Proxy
import os, errno

pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def client():
    app.secret_key = 'super secret key'
    Web(app, '../transfer', False)
    return app.test_client()

@pytest.fixture
def create_inverter(config_conn):
    _ = config_conn
    inv = InverterG3P(FakeReader(), FakeWriter(), client_mode=False)

    return inv

@pytest.fixture
def create_inverter_server(config_conn):
    _ = config_conn
    inv = InverterG3P(FakeReader(), FakeWriter(), client_mode=False)
    ifc = AsyncStreamClient(FakeReader(), FakeWriter(), inv.local,
                            None, inv.use_emulation)
    inv.remote.ifc = ifc

    return inv

@pytest.fixture
def create_inverter_client(config_conn):
    _ = config_conn
    inv = InverterG3P(FakeReader(), FakeWriter(), client_mode=True)
    ifc = AsyncStreamClient(FakeReader(), FakeWriter(), inv.local,
                            None, inv.use_emulation)
    inv.remote.ifc = ifc

    return inv

@pytest.mark.asyncio
async def test_home(client):
    """Test the home route."""
    response = await client.get('/')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'

@pytest.mark.asyncio
async def test_page(client):
    """Test the mqtt page route."""
    response = await client.get('/mqtt')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'

@pytest.mark.asyncio
async def test_rel_page(client):
    """Test the mqtt route."""
    web.build_relative_urls = True
    response = await client.get('/mqtt')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    web.build_relative_urls = False

@pytest.mark.asyncio
async def test_logging(client):
    """Test the logging page route."""
    response = await client.get('/logging')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'

@pytest.mark.asyncio
async def test_favicon96(client):
    """Test the favicon-96x96.png route."""
    response = await client.get('/favicon-96x96.png')
    assert response.status_code == 200
    assert response.mimetype == 'image/png'

@pytest.mark.asyncio
async def test_favicon(client):
    """Test the favicon.ico route."""
    response = await client.get('/favicon.ico')
    assert response.status_code == 200
    assert response.mimetype == 'image/x-icon'

@pytest.mark.asyncio
async def test_favicon_svg(client):
    """Test the favicon.svg route."""
    response = await client.get('/favicon.svg')
    assert response.status_code == 200
    assert response.mimetype == 'image/svg+xml'

@pytest.mark.asyncio
async def test_apple_touch_icon(client):
    """Test the apple-touch-icon.png route."""
    response = await client.get('/apple-touch-icon.png')
    assert response.status_code == 200
    assert response.mimetype == 'image/png'

@pytest.mark.asyncio
async def test_manifest(client):
    """Test the site.webmanifest route."""
    response = await client.get('/site.webmanifest')
    assert response.status_code == 200
    assert response.mimetype == 'application/manifest+json'

@pytest.mark.asyncio
async def test_data_fetch(create_inverter):
    """Test the data-fetch route."""
    _ = create_inverter
    client = app.test_client()
    response = await client.get('/data-fetch')
    assert response.status_code == 200

    response = await client.get('/data-fetch')
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_data_fetch1(create_inverter_server):
    """Test the data-fetch route with server connection."""
    _ = create_inverter_server
    client = app.test_client()
    response = await client.get('/data-fetch')
    assert response.status_code == 200

    response = await client.get('/data-fetch')
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_data_fetch2(create_inverter_client):
    """Test the data-fetch route with client connection."""
    _ = create_inverter_client
    client = app.test_client()
    response = await client.get('/data-fetch')
    assert response.status_code == 200

    response = await client.get('/data-fetch')
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_language_en(client):
    """Test the language/en route and cookie."""
    response = await client.get('/language/en', headers={'referer': '/index'})
    assert response.status_code == 302
    assert response.content_language.pop() == 'en'
    assert response.location == '/index'
    assert response.mimetype == 'text/html'

    client.set_cookie('test', key='language', value='de')
    response = await client.get('/mqtt')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'

@pytest.mark.asyncio
async def test_language_de(client):
    """Test the language/de route."""
    response = await client.get('/language/de', headers={'referer': '/'})
    assert response.status_code == 302
    assert response.content_language.pop() == 'de'
    assert response.location == '/'
    assert response.mimetype == 'text/html'


@pytest.mark.asyncio
async def test_language_unknown(client):
    """Test the language/unknown route."""
    response = await client.get('/language/unknown')
    assert response.status_code == 404
    assert response.mimetype == 'text/html'


@pytest.mark.asyncio
async def test_mqtt_fetch(client, create_inverter):
    """Test the mqtt-fetch route."""
    _ = create_inverter
    Proxy.class_init()

    response = await client.get('/mqtt-fetch')
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_file_fetch(client, config_conn):
    """Test the data-fetch route."""
    _ = config_conn
    assert Config.log_path == 'app/tests/log/'
    response = await client.get('/file-fetch')
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_send_file(client, config_conn):
    """Test the send-file route."""
    _ = config_conn
    assert Config.log_path == 'app/tests/log/'
    response = await client.get('/send-file/test.txt')
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_missing_send_file(client, config_conn):
    """Test the send-file route (file not found)."""
    _ = config_conn
    assert Config.log_path == 'app/tests/log/'
    response = await client.get('/send-file/no_file.log')
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_send_file(client, config_conn):
    """Test the send-file route (invalid filename)."""
    _ = config_conn
    assert Config.log_path == 'app/tests/log/'
    response = await client.get('/send-file/../test_web_route.py')
    assert response.status_code == 404

@pytest.fixture
def patch_os_remove_err():
    def new_remove(file_path: str):
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)


    with patch.object(os, 'remove', new_remove) as wrapped_os:
        yield wrapped_os

@pytest.fixture
def patch_os_remove_ok():
    def new_remove(file_path: str):
        return

    with patch.object(os, 'remove', new_remove) as wrapped_os:
        yield wrapped_os

@pytest.mark.asyncio
async def test_del_file_ok(client, config_conn, patch_os_remove_ok):
    """Test the del-file route with no error."""
    _ = config_conn
    _ = patch_os_remove_ok
    assert Config.log_path == 'app/tests/log/'
    response = await client.delete ('/del-file/test.txt')
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_del_file_err(client, config_conn, patch_os_remove_err):
    """Test the send-file route with OSError."""
    _ = config_conn
    _ = patch_os_remove_err
    assert Config.log_path == 'app/tests/log/'
    response = await client.delete ('/del-file/test.txt')
    assert response.status_code == 404
