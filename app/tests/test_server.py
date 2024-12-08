# test_with_pytest.py
import pytest
import logging
import os
from mock import patch
from server import get_log_level

def test_get_log_level():

    with patch.dict(os.environ, {'LOG_LVL': ''}):
        log_lvl = get_log_level()
        assert log_lvl == logging.INFO

    with patch.dict(os.environ, {'LOG_LVL': 'DEBUG'}):
        log_lvl = get_log_level()
        assert log_lvl == logging.DEBUG

    with patch.dict(os.environ, {'LOG_LVL': 'WARN'}):
        log_lvl = get_log_level()
        assert log_lvl == logging.WARNING

    with patch.dict(os.environ, {'LOG_LVL': 'UNKNOWN'}):
        log_lvl = get_log_level()
        assert log_lvl == logging.INFO
