# test_with_pytest.py
import pytest
import logging
import os, errno
import datetime
from os import DirEntry, stat_result
from quart import current_app
from mock import patch

from server import app as my_app
from server import Server
from web import Web, web
from async_stream import AsyncStreamClient
from gen3plus.inverter_g3p import InverterG3P
from web.log_handler import LogHandler
from test_inverter_g3p import FakeReader, FakeWriter, config_conn
from cnf.config import Config
from proxy import Proxy


class FakeServer(Server):
    def __init__(self):
        pass  # don't call the suoer(.__init__ for unit tests


pytest_plugins = ('pytest_asyncio',)
@pytest.fixture(scope="session")
def app():
    yield my_app

@pytest.fixture(scope="session")
def client(app):
    app.secret_key = 'super secret key'
    app.testing = True
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
    assert b"<title>TSUN Proxy - Connections</title>" in await response.data

@pytest.mark.asyncio
async def test_page(client):
    """Test the mqtt page route."""
    response = await client.get('/mqtt')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b"<title>TSUN Proxy - MQTT Status</title>" in await response.data
    assert b'fetch("/mqtt-fetch")' in await response.data

@pytest.mark.asyncio
async def test_rel_page(client):
    """Test the mqtt route with relative paths."""
    web.build_relative_urls = True
    response = await client.get('/mqtt')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b'fetch("./mqtt-fetch")' in await response.data
    web.build_relative_urls = False

@pytest.mark.asyncio
async def test_notes(client):
    """Test the notes page route."""
    response = await client.get('/notes')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b"<title>TSUN Proxy - Important Messages</title>" in await response.data

@pytest.mark.asyncio
async def test_logging(client):
    """Test the logging page route."""
    response = await client.get('/logging')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b"<title>TSUN Proxy - Log Files</title>" in await response.data

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
async def test_data_fetch(client, create_inverter):
    """Test the data-fetch route."""
    _ = create_inverter
    response = await client.get('/data-fetch')
    assert response.status_code == 200

    response = await client.get('/data-fetch')
    assert response.status_code == 200
    assert b'<h5>Connections</h5>' in await response.data

@pytest.mark.asyncio
async def test_data_fetch1(client, create_inverter_server):
    """Test the data-fetch route with server connection."""
    _ = create_inverter_server
    response = await client.get('/data-fetch')
    assert response.status_code == 200

    response = await client.get('/data-fetch')
    assert response.status_code == 200
    assert b'<h5>Connections</h5>' in await response.data

@pytest.mark.asyncio
async def test_data_fetch2(client, create_inverter_client):
    """Test the data-fetch route with client connection."""
    _ = create_inverter_client
    response = await client.get('/data-fetch')
    assert response.status_code == 200

    response = await client.get('/data-fetch')
    assert response.status_code == 200
    assert b'<h5>Connections</h5>' in await response.data

@pytest.mark.asyncio
async def test_language_en(client):
    """Test the language/en route and cookie."""
    response = await client.get('/language/en', headers={'referer': '/index'})
    assert response.status_code == 302
    assert response.content_language.pop() == 'en'
    assert response.location == '/index'
    assert response.mimetype == 'text/html'
    assert b'<html lang=en' in await response.data
    assert b'<title>Redirecting...</title>' in await response.data

    client.set_cookie('test', key='language', value='de')
    response = await client.get('/')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b'<html lang="en"' in await response.data
    assert b'<title>TSUN Proxy - Connections</title>' in await response.data

@pytest.mark.asyncio
async def test_language_de(client):
    """Test the language/de route."""
    response = await client.get('/language/de', headers={'referer': '/'})
    assert response.status_code == 302
    assert response.content_language.pop() == 'de'
    assert response.location == '/'
    assert response.mimetype == 'text/html'
    assert b'<html lang=en>' in await response.data
    assert b'<title>Redirecting...</title>' in await response.data

    client.set_cookie('test', key='language', value='en')
    response = await client.get('/')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b'<html lang="de"' in await response.data
    assert b'<title>TSUN Proxy - Verbindungen</title>' in await response.data

    """Switch back to english"""
    response = await client.get('/language/en', headers={'referer': '/index'})
    assert response.status_code == 302
    assert response.content_language.pop() == 'en'
    assert response.location == '/index'
    assert response.mimetype == 'text/html'
    assert b'<html lang=en>' in await response.data
    assert b'<title>Redirecting...</title>' in await response.data

@pytest.mark.asyncio
async def test_language_unknown(client):
    """Test the language/unknown route."""
    response = await client.get('/language/unknown')
    assert response.status_code == 404
    assert response.mimetype == 'text/html'

    client.set_cookie('test', key='language', value='en')
    response = await client.get('/')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b'<title>TSUN Proxy - Connections</title>' in await response.data


@pytest.mark.asyncio
async def test_mqtt_fetch(client, create_inverter):
    """Test the mqtt-fetch route."""
    _ = create_inverter
    Proxy.class_init()

    response = await client.get('/mqtt-fetch')
    assert response.status_code == 200
    assert b'<h5>MQTT devices</h5>' in await response.data


@pytest.mark.asyncio
async def test_notes_fetch(client, config_conn):
    """Test the notes-fetch route."""
    _ = config_conn

    s = FakeServer()
    s.src_dir = 'app/src/'
    s.init_logging_system()

    # First clear log and test Well done message
    logh = LogHandler()
    logh.clear()
    response = await client.get('/notes-fetch')
    assert response.status_code == 200
    assert b'<h2>Well done!</h2>' in await response.data

    # Check info logs which must be ignored here
    logging.info('config_info')
    logh.flush()
    response = await client.get('/notes-fetch')
    assert response.status_code == 200
    assert b'<h2>Well done!</h2>' in await response.data

    # Check warning logs which must be added to the note list
    logging.warning('config_warning')
    logh.flush()
    response = await client.get('/notes-fetch')
    assert response.status_code == 200
    assert b'WARNING' in await response.data
    assert b'config_warning' in await response.data

    # Check error logs which must be added to the note list
    logging.error('config_err')
    logh.flush()
    response = await client.get('/notes-fetch')
    assert response.status_code == 200
    assert b'ERROR' in await response.data
    assert b'config_err' in await response.data


@pytest.mark.asyncio
async def test_file_fetch(client, config_conn, monkeypatch):
    """Test the data-fetch route."""
    _ = config_conn
    assert Config.log_path == 'app/tests/log/'
    def my_stat1(*arg):
        stat = stat_result
        stat.st_size = 20
        stat.st_birthtime = datetime.datetime(2024, 1, 31, 10, 30, 15)
        stat.st_mtime = datetime.datetime(2024, 1, 1, 1, 30, 15).timestamp()
        return stat

    monkeypatch.setattr(DirEntry, "stat", my_stat1)
    response = await client.get('/file-fetch')
    assert response.status_code == 200


    def my_stat2(*arg):
        stat = stat_result
        stat.st_size = 20
        stat.st_mtime = datetime.datetime(2024, 1, 1, 1, 30, 15).timestamp()
        return stat

    monkeypatch.setattr(DirEntry, "stat", my_stat2)
    monkeypatch.delattr(stat_result, "st_birthtime")
    response = await client.get('/file-fetch')
    assert response.status_code == 200
    assert b'<h4>test.txt</h4>' in await response.data

@pytest.mark.asyncio
async def test_send_file(client, config_conn):
    """Test the send-file route."""
    _ = config_conn
    assert Config.log_path == 'app/tests/log/'
    response = await client.get('/send-file/test.txt')
    assert response.status_code == 200
    assert b'2025-04-30 00:01:23' in await response.data


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

@pytest.mark.asyncio
async def test_addon_links(client):
    """Test links to HA add-on config/log in UI"""
    with patch.dict(os.environ, {'SLUG': 'c676133d', 'HOSTNAME': 'c676133d-tsun-proxy'}):
        response = await client.get('/')
        assert response.status_code == 200
        assert response.mimetype == 'text/html'
        assert b'Add-on Config' in await response.data
        assert b'href="/hassio/addon/c676133d_tsun-proxy/logs' in await response.data
        assert b'href="/hassio/addon/c676133d_tsun-proxy/config' in await response.data

    # check that links are not available if env vars SLUG and HOSTNAME are not defined (docker version)    
    response = await client.get('/')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b'Add-on Config' not in await response.data
