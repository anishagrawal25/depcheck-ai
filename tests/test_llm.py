from unittest.mock import MagicMock, patch
import pytest
import requests
from app.llm import GeminiClient, generate


def test_generate_success_mocked(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Dependency analysis explanation"}]
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_resp) as mock_post:
        result = generate("Test prompt", timeout=5)
        assert result == "Dependency analysis explanation"
        assert mock_post.called
        args, kwargs = mock_post.call_args
        assert kwargs["timeout"] == 5
        assert "Test prompt" in kwargs["json"]["contents"][0]["parts"][0]["text"]
        assert "key=test-api-key" in args[0]


def test_generate_timeout_mocked(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    with patch("requests.post", side_effect=requests.Timeout("Request timed out")):
        with pytest.raises(requests.Timeout):
            generate("Test timeout prompt", timeout=3)


def test_generate_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    client = GeminiClient(api_key="")
    with pytest.raises(ValueError, match="GEMINI_API_KEY is not configured"):
        client.generate("Test prompt")
