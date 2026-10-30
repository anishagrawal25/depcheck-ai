import time
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import LLMExplanation, PackageSignals

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scan_endpoint_sequential():
    code_snippet = """
import requests
import totallyfakepkg
"""
    def mock_signals(name: str):
        if name == "requests":
            return PackageSignals(
                name="requests",
                exists=True,
                age_days=1000,
                release_count=50,
                has_repo=True,
            )
        return PackageSignals(name=name, exists=False)

    with patch("app.main.get_package_signals", side_effect=mock_signals):
        response = client.post("/scan", json={"code": code_snippet})
        assert response.status_code == 200
        data = response.json()
        assert data["scanned_imports"] == 2
        findings = data["findings"]
        assert len(findings) == 2

        req_finding = next(f for f in findings if f["package"] == "requests")
        assert req_finding["verdict"] == "ok"

        fake_finding = next(f for f in findings if f["package"] == "totallyfakepkg")
        assert fake_finding["verdict"] == "hallucinated"


def test_scan_concurrent_order_is_stable():
    code_snippet = """
import pkg_a
import pkg_b
import pkg_c
import pkg_d
"""
    delays = {
        "pkg_a": 0.06,
        "pkg_b": 0.03,
        "pkg_c": 0.01,
        "pkg_d": 0.00,
    }

    def mock_signals(name: str):
        delay = delays.get(name, 0.0)
        time.sleep(delay)
        return PackageSignals(
            name=name,
            exists=True,
            age_days=100,
            release_count=10,
            has_repo=True,
        )

    with patch("app.main.get_package_signals", side_effect=mock_signals):
        response = client.post("/scan", json={"code": code_snippet})
        assert response.status_code == 200
        data = response.json()
        assert data["scanned_imports"] == 4
        result_pkgs = [f["package"] for f in data["findings"]]
        assert result_pkgs == ["pkg_a", "pkg_b", "pkg_c", "pkg_d"]


def test_scan_invalid_python_returns_400():
    response = client.post("/scan", json={"code": "def invalid syntax :"})
    assert response.status_code == 400
    assert "Syntax error" in response.json()["detail"]


def test_scan_empty_body_returns_422():
    response = client.post("/scan", json={})
    assert response.status_code == 422


def test_scan_requests_and_fake_fastjsonparserx():
    code_snippet = """
import requests
import fastjsonparserx
"""
    def mock_signals(name: str):
        if name == "requests":
            return PackageSignals(
                name="requests",
                exists=True,
                age_days=1000,
                release_count=50,
                has_repo=True,
            )
        elif name == "fastjsonparserx":
            return PackageSignals(name="fastjsonparserx", exists=False)
        return PackageSignals(name=name, exists=False)

    with patch("app.main.get_package_signals", side_effect=mock_signals):
        response = client.post("/scan", json={"code": code_snippet})
        assert response.status_code == 200
        data = response.json()
        assert data["scanned_imports"] == 2
        findings = {f["package"]: f for f in data["findings"]}
        assert findings["requests"]["verdict"] == "ok"
        assert findings["fastjsonparserx"]["verdict"] == "hallucinated"
        assert findings["fastjsonparserx"]["risk_score"] == 0.95


def test_scan_use_llm_false_does_not_call_llm():
    code_snippet = "import fastjsonparserx"
    with patch("app.main.get_package_signals", return_value=PackageSignals(name="fastjsonparserx", exists=False)):
        with patch("app.main.explain_finding") as mock_explain:
            response = client.post("/scan", params={"use_llm": False}, json={"code": code_snippet})
            assert response.status_code == 200
            assert mock_explain.call_count == 0


def test_scan_use_llm_true_calls_llm_only_for_non_ok():
    code_snippet = """
import requests
import fastjsonparserx
"""
    def mock_signals(name: str):
        if name == "requests":
            return PackageSignals(name="requests", exists=True, age_days=1000, release_count=50, has_repo=True)
        return PackageSignals(name=name, exists=False)

    with patch("app.main.get_package_signals", side_effect=mock_signals):
        with patch(
            "app.main.explain_finding",
            return_value=LLMExplanation(explanation="LLM explanation for fake pkg", suggested_fix="Remove it"),
        ) as mock_explain:
            response = client.post("/scan", params={"use_llm": True}, json={"code": code_snippet})
            assert response.status_code == 200
            # explain_finding must be called only for fastjsonparserx (non-ok), NOT for requests (ok)
            assert mock_explain.call_count == 1
            call_finding = mock_explain.call_args[0][0]
            assert call_finding.package == "fastjsonparserx"

            data = response.json()
            findings = {f["package"]: f for f in data["findings"]}
            assert findings["fastjsonparserx"]["reasons"] == ["LLM explanation for fake pkg"]
            assert findings["fastjsonparserx"]["suggested_fix"] == "Remove it"


def test_scan_mode_agent_triggers_investigate_package():
    code_snippet = """
import requests
import fastjsonparserx
"""
    def mock_signals(name: str):
        if name == "requests":
            return PackageSignals(name="requests", exists=True, age_days=1000, release_count=50, has_repo=True)
        return PackageSignals(name=name, exists=False)

    from app.schemas import Finding
    investigated = Finding(
        package="fastjsonparserx",
        verdict="hallucinated",
        risk_score=0.95,
        confidence=0.95,
        reasons=["Agent verified hallucinated package"],
        suggested_fix="Do not import fastjsonparserx",
    )

    with patch("app.main.get_package_signals", side_effect=mock_signals):
        with patch("app.main.investigate_package", return_value=investigated) as mock_inv:
            response = client.post("/scan", params={"mode": "agent"}, json={"code": code_snippet})
            assert response.status_code == 200
            assert mock_inv.call_count == 1
            call_finding = mock_inv.call_args[0][0]
            assert call_finding.package == "fastjsonparserx"

            data = response.json()
            findings = {f["package"]: f for f in data["findings"]}
            assert findings["fastjsonparserx"]["reasons"] == ["Agent verified hallucinated package"]
            assert findings["fastjsonparserx"]["suggested_fix"] == "Do not import fastjsonparserx"


def test_scan_mode_rule_does_not_trigger_agent():
    code_snippet = "import fastjsonparserx"
    with patch("app.main.get_package_signals", return_value=PackageSignals(name="fastjsonparserx", exists=False)):
        with patch("app.main.investigate_package") as mock_inv:
            response = client.post("/scan", params={"mode": "rule"}, json={"code": code_snippet})
            assert response.status_code == 200
            assert mock_inv.call_count == 0

