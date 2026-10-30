from unittest.mock import MagicMock, patch
import pytest
import requests
from app.checks.osv import check_vulnerabilities, clear_cache


@pytest.fixture(autouse=True)
def setup_teardown():
    clear_cache()
    yield
    clear_cache()


def test_check_vulnerabilities_found():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "vulns": [
            {"id": "GHSA-1"},
            {"id": "GHSA-2"},
            {"id": "GHSA-3"},
            {"id": "GHSA-4"},
            {"id": "GHSA-5"},
        ]
    }

    with patch("requests.post", return_value=mock_resp) as mock_post:
        count, vuln_ids = check_vulnerabilities("vulnerable-pkg")
        assert count == 5
        assert vuln_ids == ["GHSA-1", "GHSA-2", "GHSA-3"]
        assert mock_post.called
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["package"]["name"] == "vulnerable-pkg"
        assert kwargs["json"]["package"]["ecosystem"] == "PyPI"


def test_check_vulnerabilities_none():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"vulns": []}

    with patch("requests.post", return_value=mock_resp):
        count, vuln_ids = check_vulnerabilities("clean-pkg")
        assert count == 0
        assert vuln_ids == []


def test_check_vulnerabilities_timeout():
    with patch("requests.post", side_effect=requests.Timeout("Connection timeout")) as mock_post:
        count, vuln_ids = check_vulnerabilities("timeout-pkg", timeout=3)
        assert count == 0
        assert vuln_ids == []
        assert mock_post.called
        args, kwargs = mock_post.call_args
        assert kwargs["timeout"] == 3


def test_check_vulnerabilities_network_error():
    with patch("requests.post", side_effect=requests.ConnectionError("Network error")):
        count, vuln_ids = check_vulnerabilities("err-pkg")
        assert count == 0
        assert vuln_ids == []


def test_check_vulnerabilities_caching():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"vulns": [{"id": "GHSA-99"}]}

    with patch("requests.post", return_value=mock_resp) as mock_post:
        res1 = check_vulnerabilities("cache-pkg")
        res2 = check_vulnerabilities("cache-pkg")
        assert res1 == res2
        assert mock_post.call_count == 1
