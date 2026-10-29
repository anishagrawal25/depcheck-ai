import pytest
from pydantic import ValidationError
from app.schemas import PackageSignals


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
        PackageSignals(name=123, exists="not_a_bool")  # invalid types
