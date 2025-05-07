# test_with_pytest.py
import pytest
import logging
import os
from mock import patch
from server import app, Server, ProxyState

pytest_plugins = ('pytest_asyncio',)


class TestServerClass:
    class FakeServer(Server):
        def __init__(self):
            pass  # don't call the suoer(.__init__ for unit tests

    def test_get_log_level(self):
        s = self.FakeServer()

        with patch.dict(os.environ, {}):
            log_lvl = s.get_log_level()
            assert log_lvl == None

        with patch.dict(os.environ, {'LOG_LVL': 'DEBUG'}):
            log_lvl = s.get_log_level()
            assert log_lvl == logging.DEBUG

        with patch.dict(os.environ, {'LOG_LVL': 'INFO'}):
            log_lvl = s.get_log_level()
            assert log_lvl == logging.INFO

        with patch.dict(os.environ, {'LOG_LVL': 'WARN'}):
            log_lvl = s.get_log_level()
            assert log_lvl == logging.WARNING

        with patch.dict(os.environ, {'LOG_LVL': 'ERROR'}):
            log_lvl = s.get_log_level()
            assert log_lvl == logging.ERROR

        with patch.dict(os.environ, {'LOG_LVL': 'UNKNOWN'}):
            log_lvl = s.get_log_level()
            assert log_lvl == None

    def test_default_args(self):
        s = self.FakeServer()
        assert s.config_path == './config/'
        assert s.json_config == ''
        assert s.toml_config == ''
        assert s.trans_path == '../translations/'
        assert s.rel_urls == False
        assert s.log_path == './log/'
        assert s.log_backups == 0

    def test_parse_args_empty(self):
        s = self.FakeServer()
        s.parse_args([])
        assert s.config_path == './config/'
        assert s.json_config == None
        assert s.toml_config == None
        assert s.trans_path == '../translations/'
        assert s.rel_urls == False
        assert s.log_path == './log/'
        assert s.log_backups == 0

    def test_parse_args_short(self):
        s = self.FakeServer()
        s.parse_args(['-r', '-c', '/tmp/my-config', '-j', 'cnf.jsn', '-t', 'cnf.tml', '-tr', '/my/trans/', '-l', '/my_logs/', '-b', '3'])
        assert s.config_path == '/tmp/my-config'
        assert s.json_config == 'cnf.jsn'
        assert s.toml_config == 'cnf.tml'
        assert s.trans_path == '/my/trans/'
        assert s.rel_urls == True
        assert s.log_path == '/my_logs/'
        assert s.log_backups == 3

    def test_parse_args_long(self):
        s = self.FakeServer()
        s.parse_args(['--rel_urls', '--config_path', '/tmp/my-config', '--json_config', 'cnf.jsn',
                      '--toml_config', 'cnf.tml', '--trans_path', '/my/trans/', '--log_path', '/my_logs/',
                      '--log_backups', '3'])
        assert s.config_path == '/tmp/my-config'
        assert s.json_config == 'cnf.jsn'
        assert s.toml_config == 'cnf.tml'
        assert s.trans_path == '/my/trans/'
        assert s.rel_urls == True
        assert s.log_path == '/my_logs/'
        assert s.log_backups == 3

    def test_parse_args_invalid(self):
        s = self.FakeServer()
        with pytest.raises(SystemExit) as exc_info: 
            s.parse_args(['--inalid', '/tmp/my-config'])
        assert exc_info.value.code == 2


class TestApp:
    @pytest.mark.asyncio
    async def test_ready(self):
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
    async def test_healthy(self):
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

