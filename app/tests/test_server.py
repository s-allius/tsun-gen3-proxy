# test_with_pytest.py
import pytest
import logging
import os
from mock import patch
from server import get_log_level, app, ProxyState

pytest_plugins = ('pytest_asyncio',)

def test_get_log_level():

    with patch.dict(os.environ, {}):
        log_lvl = get_log_level()
        assert log_lvl == None

    with patch.dict(os.environ, {'LOG_LVL': 'DEBUG'}):
        log_lvl = get_log_level()
        assert log_lvl == logging.DEBUG

    with patch.dict(os.environ, {'LOG_LVL': 'INFO'}):
        log_lvl = get_log_level()
        assert log_lvl == logging.INFO

    with patch.dict(os.environ, {'LOG_LVL': 'WARN'}):
        log_lvl = get_log_level()
        assert log_lvl == logging.WARNING

    with patch.dict(os.environ, {'LOG_LVL': 'ERROR'}):
        log_lvl = get_log_level()
        assert log_lvl == logging.ERROR

    with patch.dict(os.environ, {'LOG_LVL': 'UNKNOWN'}):
        log_lvl = get_log_level()
        assert log_lvl == None


@pytest.mark.asyncio
async def test_home():
    """Test the home route."""
    client = app.test_client()
    response = await client.get('/')
    assert response.status_code == 200
    result = await response.get_data()
    assert result == b"Hello, world"

@pytest.mark.asyncio
async def test_ready():
    """Test the ready route."""

    ProxyState.set_up(False)
    client = app.test_client()
    response = await client.get('/-/ready')
    assert response.status_code == 503
    result = await response.get_data()
    assert result == b"Not ready"

    ProxyState.set_up(True)
    response = await client.get('/-/ready')
    assert response.status_code == 200
    result = await response.get_data()
    assert result == b"Is ready"

@pytest.mark.asyncio
async def test_healthy():
    """Test the healthy route."""

    ProxyState.set_up(False)
    client = app.test_client()
    response = await client.get('/-/healthy')
    assert response.status_code == 200
    result = await response.get_data()
    assert result == b"I'm fine"

    ProxyState.set_up(True)
    response = await client.get('/-/healthy')
    assert response.status_code == 200
    result = await response.get_data()
    assert result == b"I'm fine"
