import os
from unittest.mock import patch
from app.config import GEMINI_API_KEY, REQUEST_TIMEOUT, get_config


def test_default_config():
    assert REQUEST_TIMEOUT == 5
    assert isinstance(GEMINI_API_KEY, str)


def test_config_env_override():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key_123", "REQUEST_TIMEOUT": "10"}):
        cfg = get_config()
        assert cfg["GEMINI_API_KEY"] == "test_key_123"
        assert cfg["REQUEST_TIMEOUT"] == 10
