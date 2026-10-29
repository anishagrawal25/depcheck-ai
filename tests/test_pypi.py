from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from app.checks.pypi import get_package_signals


@patch("requests.get")
def test_package_exists(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "info": {"name": "requests"},
        "releases": {"1.0.0": []},
    }
    mock_get.return_value = mock_response

    signals = get_package_signals("requests")
    assert signals.name == "requests"
    assert signals.exists is True


@patch("requests.get")
def test_package_does_not_exist(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    signals = get_package_signals("nonexistent-pkg-999")
    assert signals.name == "nonexistent-pkg-999"
    assert signals.exists is False


@patch("requests.get")
def test_package_age_and_release_count(mock_get):
    now = datetime.now(timezone.utc)
    upload_1 = (now - timedelta(days=120)).isoformat()
    upload_2 = (now - timedelta(days=30)).isoformat()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "info": {"name": "my-pkg"},
        "releases": {
            "0.1.0": [{"upload_time_iso_8601": upload_1}],
            "0.2.0": [{"upload_time_iso_8601": upload_2}],
        },
    }
    mock_get.return_value = mock_response

    signals = get_package_signals("my-pkg")
    assert signals.release_count == 2
    assert signals.age_days is not None
    assert 119 <= signals.age_days <= 121


@patch("requests.get")
def test_package_has_repo_github(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "info": {
            "name": "my-pkg",
            "home_page": "https://github.com/my-org/my-pkg",
            "project_urls": None,
        },
        "releases": {},
    }
    mock_get.return_value = mock_response

    signals = get_package_signals("my-pkg")
    assert signals.has_repo is True


@patch("requests.get")
def test_package_has_repo_gitlab_project_urls(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "info": {
            "name": "my-pkg",
            "home_page": "https://mypkg.org",
            "project_urls": {"Repository": "https://gitlab.com/group/repo"},
        },
        "releases": {},
    }
    mock_get.return_value = mock_response

    signals = get_package_signals("my-pkg")
    assert signals.has_repo is True


@patch("requests.get")
def test_package_no_repo(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "info": {
            "name": "my-pkg",
            "home_page": "https://example.com",
            "project_urls": {"Docs": "https://docs.example.com"},
        },
        "releases": {},
    }
    mock_get.return_value = mock_response

    signals = get_package_signals("my-pkg")
    assert signals.has_repo is False
