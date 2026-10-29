import pytest
from app.checks.pypi import get_package_signals, clear_cache


@pytest.fixture(autouse=True)
def run_before_each_test():
    clear_cache()
    yield
    clear_cache()


@pytest.mark.network
def test_live_package_exists():
    signals = get_package_signals("requests")
    assert signals.name == "requests"
    assert signals.exists is True
    assert signals.age_days is not None and signals.age_days > 365
    assert signals.release_count is not None and signals.release_count > 10
    assert signals.has_repo is True


@pytest.mark.network
def test_live_package_does_not_exist():
    signals = get_package_signals("this-package-definitely-does-not-exist-9876543210-xyz")
    assert signals.exists is False
