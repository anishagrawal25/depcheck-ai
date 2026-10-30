from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import PackageSignals

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
