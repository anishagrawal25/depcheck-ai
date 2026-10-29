from app.checks.typosquat import find_similar


def test_find_similar_reqeusts():
    similar = find_similar("reqeusts")
    assert "requests" in similar


def test_find_similar_numpyy():
    similar = find_similar("numpyy")
    assert "numpy" in similar


def test_find_similar_identical_requests():
    # Identical package name should not be returned as similar
    similar = find_similar("requests")
    assert "requests" not in similar
    assert similar == []
