from app.agent.graph import investigate_package
from app.schemas import Finding


def test_investigate_package_ok_bypasses_graph():
    finding = Finding(
        package="requests",
        verdict="ok",
        risk_score=0.0,
        confidence=0.85,
        reasons=[],
    )
    result = investigate_package(finding, "import requests")
    assert result == finding
    assert result.confidence == 0.85


def test_investigate_package_suspicious_runs_graph():
    finding = Finding(
        package="reqeusts",
        verdict="suspicious",
        risk_score=0.6,
        confidence=0.85,
        reasons=["Name is similar to requests"],
        suggested_fix="Did you mean 'requests'?",
    )
    result = investigate_package(finding, "import reqeusts")
    assert result.package == "reqeusts"
    assert result.verdict == "suspicious"
    assert result.confidence > 0.85
    assert result.suggested_fix == "Did you mean 'requests'?"
    assert any("Agent analysis" in r for r in result.reasons)
