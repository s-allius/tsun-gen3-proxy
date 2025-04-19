# test_with_pytest.py
import pytest
from server import app

pytest_plugins = ('pytest_asyncio',)


@pytest.mark.asyncio
async def test_home():
    """Test the home route."""
    client = app.test_client()
    response = await client.get('/')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'

@pytest.mark.asyncio
async def test_page():
    """Test the empty page route."""
    client = app.test_client()
    response = await client.get('/page')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'


@pytest.mark.asyncio
async def test_favicon96():
    """Test the favicon-96x96.png route."""
    client = app.test_client()
    response = await client.get('/favicon-96x96.png')
    assert response.status_code == 200
    assert response.mimetype == 'image/png'

@pytest.mark.asyncio
async def test_favicon():
    """Test the favicon.ico route."""
    client = app.test_client()
    response = await client.get('/favicon.ico')
    assert response.status_code == 200
    assert response.mimetype == 'image/x-icon'

@pytest.mark.asyncio
async def test_favicon_svg():
    """Test the favicon.svg route."""
    client = app.test_client()
    response = await client.get('/favicon.svg')
    assert response.status_code == 200
    assert response.mimetype == 'image/svg+xml'

@pytest.mark.asyncio
async def test_apple_touch_icon():
    """Test the apple-touch-icon.png route."""
    client = app.test_client()
    response = await client.get('/apple-touch-icon.png')
    assert response.status_code == 200
    assert response.mimetype == 'image/png'

@pytest.mark.asyncio
async def test_manifest():
    """Test the site.webmanifest route."""
    client = app.test_client()
    response = await client.get('/site.webmanifest')
    assert response.status_code == 200
    assert response.mimetype == 'application/manifest+json'

@pytest.mark.asyncio
async def test_data_fetch():
    """Test the healthy route."""
    client = app.test_client()
    response = await client.get('/data-fetch')
    assert response.status_code == 200

    response = await client.get('/data-fetch')
    assert response.status_code == 200
