# test_with_pytest.py
import pytest
from server import app
from web import Web, web
from async_stream import AsyncStreamClient
from gen3plus.inverter_g3p import InverterG3P
from test_inverter_g3p import FakeReader, FakeWriter, config_conn

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
    """Test the empty page route."""
    response = await client.get('/page')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'

@pytest.mark.asyncio
async def test_rel_page(client):
    """Test the empty page route."""
    web.build_relative_urls = True
    response = await client.get('/page')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    web.build_relative_urls = False

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
    """Test the healthy route."""
    _ = create_inverter
    client = app.test_client()
    response = await client.get('/data-fetch')
    assert response.status_code == 200

    response = await client.get('/data-fetch')
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_data_fetch1(create_inverter_server):
    """Test the healthy route."""
    _ = create_inverter_server
    client = app.test_client()
    response = await client.get('/data-fetch')
    assert response.status_code == 200

    response = await client.get('/data-fetch')
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_data_fetch2(create_inverter_client):
    """Test the healthy route."""
    _ = create_inverter_client
    client = app.test_client()
    response = await client.get('/data-fetch')
    assert response.status_code == 200

    response = await client.get('/data-fetch')
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_language_en(client):
    """Test the language/en route."""
    response = await client.get('/language/en')
    assert response.status_code == 302
    assert response.mimetype == 'text/html'

    client.set_cookie('test', key='language', value='de')
    response = await client.get('/page')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'

@pytest.mark.asyncio
async def test_language_de(client):
    """Test the language/en route."""
    response = await client.get('/language/de')
    assert response.status_code == 302
    assert response.mimetype == 'text/html'

@pytest.mark.asyncio
async def test_language_unknown(client):
    """Test the language/en route."""
    response = await client.get('/language/unknonw')
    assert response.status_code == 404
    assert response.mimetype == 'text/html'
