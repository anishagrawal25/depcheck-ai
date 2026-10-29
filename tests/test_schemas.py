import json
import pytest
from pydantic import ValidationError
from app.schemas import PackageSignals, Finding, ScanReport


def test_package_signals_valid():
    signals = PackageSignals(
        name="requests",
        exists=True,
        age_days=3000,
        release_count=45,
        has_repo=True,
        downloads=10000000,
    )
    assert signals.name == "requests"
    assert signals.exists is True
    assert signals.age_days == 3000
    assert signals.release_count == 45
    assert signals.has_repo is True
    assert signals.downloads == 10000000


def test_package_signals_nonexistent():
    signals = PackageSignals(name="fake-package-xyz", exists=False)
    assert signals.name == "fake-package-xyz"
    assert signals.exists is False
    assert signals.age_days is None


def test_package_signals_validation_error():
    with pytest.raises(ValidationError):
        PackageSignals(name=123, exists="not_a_bool")


def test_finding_valid():
    finding = Finding(
        package="reqeusts",
        verdict="suspicious",
        risk_score=0.85,
        confidence=0.9,
        reasons=["Similar to popular package requests"],
        suggested_fix="Use 'requests' instead.",
    )
    assert finding.package == "reqeusts"
    assert finding.verdict == "suspicious"
    assert finding.risk_score == 0.85
    assert finding.confidence == 0.9
    assert finding.suggested_fix == "Use 'requests' instead."


def test_finding_verdict_validation():
    with pytest.raises(ValidationError):
        Finding(
            package="foo",
            verdict="invalid_verdict",
            risk_score=0.5,
            confidence=0.5,
        )


def test_finding_risk_score_range():
    with pytest.raises(ValidationError):
        Finding(
            package="foo",
            verdict="ok",
            risk_score=1.5,
            confidence=0.5,
        )

    with pytest.raises(ValidationError):
        Finding(
            package="foo",
            verdict="ok",
            risk_score=-0.1,
            confidence=0.5,
        )


def test_finding_confidence_range():
    with pytest.raises(ValidationError):
        Finding(
            package="foo",
            verdict="ok",
            risk_score=0.2,
            confidence=2.0,
        )


def test_scan_report_serialization():
    finding = Finding(
        package="fake-lib",
        verdict="hallucinated",
        risk_score=0.95,
        confidence=0.9,
        reasons=["Package does not exist on PyPI"],
    )
    report = ScanReport(findings=[finding], scanned_imports=1)
    json_str = report.model_dump_json()
    parsed = json.loads(json_str)

    assert parsed["scanned_imports"] == 1
    assert len(parsed["findings"]) == 1
    assert parsed["findings"][0]["package"] == "fake-lib"
    assert parsed["findings"][0]["verdict"] == "hallucinated"
    assert parsed["findings"][0]["risk_score"] == 0.95

    # Round-trip deserialization
    reconstructed = ScanReport.model_validate_json(json_str)
    assert reconstructed.scanned_imports == 1
    assert reconstructed.findings[0].package == "fake-lib"
