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
    result = await response.get_data()
    assert result == b"Hello, world"
