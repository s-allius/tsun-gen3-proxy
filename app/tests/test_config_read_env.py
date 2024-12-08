# test_with_pytest.py
import pytest
import os
from mock import patch
from cnf.config import Config
from cnf.config_read_toml import ConfigReadToml
from cnf.config_read_env import ConfigReadEnv

def patch_getenv():
    def new_getenv(key: str, defval=None):
        """Get an environment variable, return None if it doesn't exist.
The optional second argument can specify an alternate default. key,
default and the result are str."""
        if key == 'MQTT_PASSWORD':
            return 'passwd'
        elif key == 'MQTT_PORT':
            return 1234
        elif key == 'MQTT_HOST':
            return ""
        return defval

    with patch.object(os, 'getenv', new_getenv) as conn:
        yield conn

def test_extend_key():
    cnf_rd = ConfigReadEnv()

    conf = {}
    cnf_rd._extend_key(conf, "mqtt.user", "testuser")
    assert conf == {
        'mqtt': {
            'user': 'testuser',
        },
    }

    conf = {}
    cnf_rd._extend_key(conf, "mqtt", "testuser")
    assert conf == {
        'mqtt': 'testuser',
    }

    conf = {}
    cnf_rd._extend_key(conf, "", "testuser")
    assert conf == {'': 'testuser'}

def test_read_env_config():
    Config.init(ConfigReadToml("app/config/default_config.toml"))
    assert Config.get('mqtt') == {'host': 'mqtt', 'port': 1883, 'user': None, 'passwd': None}
    for _ in patch_getenv():

        ConfigReadEnv()
    assert Config.get_error() == None
    assert Config.get('mqtt') == {'host': 'mqtt', 'port': 1234, 'user': None, 'passwd': 'passwd'}
