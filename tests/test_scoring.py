from app.scoring import WEIGHTS, score_package
from app.schemas import PackageSignals


def test_scoring_weights_config():
    assert "age" in WEIGHTS
    assert "releases" in WEIGHTS
    assert "repo" in WEIGHTS
    assert "typosquat" in WEIGHTS
    assert "vulnerabilities" in WEIGHTS
    assert sum(WEIGHTS.values()) <= 1.05


def test_score_package_hallucinated():
    signals = PackageSignals(name="totally-fake-pkg-123", exists=False)
    finding = score_package(signals, similar=[])

    assert finding.package == "totally-fake-pkg-123"
    assert finding.verdict == "hallucinated"
    assert finding.risk_score == 0.95
    assert finding.confidence >= 0.9
    assert finding.reasons == ["Package 'totally-fake-pkg-123' does not exist on the PyPI registry."]


def test_score_package_age_under_30_days():
    signals = PackageSignals(
        name="fresh-pkg",
        exists=True,
        age_days=10,
        release_count=5,
        has_repo=True,
    )
    finding = score_package(signals, similar=[])

    assert finding.verdict == "ok"
    assert finding.risk_score == 0.2
    assert "newly published (10 days old, under 30-day threshold)" in finding.reasons[0]


def test_score_package_older_package_clean():
    signals = PackageSignals(
        name="mature-pkg",
        exists=True,
        age_days=300,
        release_count=10,
        has_repo=True,
    )
    finding = score_package(signals, similar=[])

    assert finding.verdict == "ok"
    assert finding.risk_score == 0.0
    assert len(finding.reasons) == 0


def test_score_package_suspicious_typosquat_and_no_repo():
    signals = PackageSignals(
        name="reqeusts",
        exists=True,
        age_days=100,
        release_count=5,
        has_repo=False,
    )
    finding = score_package(signals, similar=["requests"])

    assert finding.verdict == "suspicious"
    assert finding.risk_score == 0.6
    assert finding.suggested_fix == "Did you mean 'requests'?"
    assert any("highly similar to popular package(s): requests" in r for r in finding.reasons)
    assert any("No public source repository" in r for r in finding.reasons)


def test_score_package_human_readable_reasons_all():
    signals = PackageSignals(
        name="bad-package",
        exists=True,
        age_days=5,
        release_count=1,
        has_repo=False,
    )
    finding = score_package(signals, similar=["requests"])

    # Check each readable sentence
    assert any("newly published (5 days old" in r for r in finding.reasons)
    assert any("low release count (1 release(s)" in r for r in finding.reasons)
    assert any("No public source repository" in r for r in finding.reasons)
    assert any("highly similar to popular package(s): requests" in r for r in finding.reasons)


def test_score_package_with_vulnerabilities():
    signals = PackageSignals(
        name="vulnerable-pkg",
        exists=True,
        age_days=200,
        release_count=10,
        has_repo=True,
    )
    vulns = (2, ["GHSA-1234", "GHSA-5678"])
    finding = score_package(signals, similar=[], vulnerabilities=vulns)

    assert finding.risk_score == 0.05
    assert any("2 known vulnerability/vulnerabilities" in r for r in finding.reasons)
    assert any("GHSA-1234" in r for r in finding.reasons)
