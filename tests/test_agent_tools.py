from unittest.mock import MagicMock, patch
from app.agent.tools import (
    ALL_TOOLS,
    check_osv,
    check_registry,
    find_similar_package,
    search_docs,
    verify_api_call,
)
from app.checks.osv import VulnerabilityResult
from app.schemas import PackageSignals


def test_tools_list_count():
    assert len(ALL_TOOLS) == 5


def test_tool_check_registry():
    mock_signals = PackageSignals(
        name="requests",
        exists=True,
        age_days=1000,
        release_count=50,
        has_repo=True,
    )
    with patch("app.agent.tools.get_package_signals", return_value=mock_signals):
        result = check_registry.invoke({"package": "requests"})
        assert result["name"] == "requests"
        assert result["exists"] is True
        assert result["age_days"] == 1000
        assert result["release_count"] == 50
        assert result["has_repo"] is True


def test_tool_search_docs():
    mock_matches = [{"id": "1", "symbol": "requests.get", "document": "doc", "metadata": {}, "distance": 0.1}]
    with patch("app.agent.tools._search_docs", return_value=mock_matches):
        result = search_docs.invoke({"package": "requests", "query": "get"})
        assert len(result) == 1
        assert result[0]["symbol"] == "requests.get"


def test_tool_check_osv():
    with patch("app.agent.tools._check_osv", return_value=VulnerabilityResult(count=1, vuln_ids=["GHSA-123"])):
        result = check_osv.invoke({"package": "vulnerable-pkg"})
        assert result["count"] == 1
        assert result["vuln_ids"] == ["GHSA-123"]


def test_tool_find_similar_package():
    with patch("app.agent.tools._find_similar", return_value=["requests"]):
        result = find_similar_package.invoke({"package": "reqeusts"})
        assert result == ["requests"]


def test_tool_verify_api_call():
    with patch("app.agent.tools._verify_api_call", return_value="found"):
        result = verify_api_call.invoke({"package": "requests", "symbol": "get"})
        assert result == "found"
