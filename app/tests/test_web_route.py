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
async def test_favicon():
    """Test the favicon.ico route."""
    client = app.test_client()
    response = await client.get('/favicon.ico')
    assert response.status_code == 200
    assert response.mimetype == 'image/x-icon'
