from app.scoring import WEIGHTS, score_package
from app.schemas import PackageSignals


def test_scoring_weights_config():
    assert "age" in WEIGHTS
    assert "releases" in WEIGHTS
    assert "repo" in WEIGHTS
    assert "typosquat" in WEIGHTS
    assert sum(WEIGHTS.values()) <= 1.05


def test_score_package_hallucinated():
    signals = PackageSignals(name="totally-fake-pkg-123", exists=False)
    finding = score_package(signals, similar=[])

    assert finding.package == "totally-fake-pkg-123"
    assert finding.verdict == "hallucinated"
    assert finding.risk_score == 0.95
    assert finding.confidence >= 0.9
    assert "Package does not exist on PyPI" in finding.reasons


def test_score_package_age_under_30_days():
    signals = PackageSignals(
        name="fresh-pkg",
        exists=True,
        age_days=10,
        release_count=5,
        has_repo=True,
    )
    finding = score_package(signals, similar=[])

    assert finding.verdict == "ok"  # 0.2 < 0.5
    assert finding.risk_score == 0.2
    assert any("newly created" in r for r in finding.reasons)


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
