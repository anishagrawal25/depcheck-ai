from app.scoring import WEIGHTS


def test_scoring_weights_config():
    assert "age" in WEIGHTS
    assert "releases" in WEIGHTS
    assert "repo" in WEIGHTS
    assert "typosquat" in WEIGHTS
    assert sum(WEIGHTS.values()) <= 1.05
