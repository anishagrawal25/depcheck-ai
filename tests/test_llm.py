from unittest.mock import MagicMock, patch
import pytest
import requests
from app.llm import GeminiClient, explain_finding, generate
from app.schemas import Finding, LLMExplanation


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


def test_explain_finding_valid_json():
    finding = Finding(
        package="totallyfake",
        verdict="hallucinated",
        risk_score=0.95,
        confidence=0.95,
        reasons=["Package does not exist on PyPI"],
    )
    code = "import totallyfake"

    valid_response = '{"explanation": "The package totallyfake does not exist on PyPI and is likely hallucinated.", "suggested_fix": "Remove import or install a real package."}'

    with patch("app.llm.generate", return_value=valid_response) as mock_gen:
        result = explain_finding(finding, code)
        assert isinstance(result, LLMExplanation)
        assert "totallyfake does not exist" in result.explanation
        assert result.suggested_fix == "Remove import or install a real package."
        assert mock_gen.call_count == 1


def test_explain_finding_retry_on_invalid_json():
    finding = Finding(
        package="reqeusts",
        verdict="suspicious",
        risk_score=0.6,
        confidence=0.85,
        reasons=["Name is very similar to requests"],
    )
    code = "import reqeusts"

    invalid_response = "I think reqeusts is a typo for requests"
    valid_retry_response = '```json\n{"explanation": "reqeusts is a typo for requests.", "suggested_fix": "import requests"}\n```'

    with patch("app.llm.generate", side_effect=[invalid_response, valid_retry_response]) as mock_gen:
        result = explain_finding(finding, code)
        assert isinstance(result, LLMExplanation)
        assert result.explanation == "reqeusts is a typo for requests."
        assert result.suggested_fix == "import requests"
        assert mock_gen.call_count == 2


def test_explain_finding_retry_fails():
    finding = Finding(
        package="reqeusts",
        verdict="suspicious",
        risk_score=0.6,
        confidence=0.85,
        reasons=["Name is very similar to requests"],
    )
    code = "import reqeusts"

    with patch("app.llm.generate", return_value="Still not JSON"):
        with pytest.raises(ValueError, match="Failed to produce valid LLMExplanation"):
            explain_finding(finding, code)
