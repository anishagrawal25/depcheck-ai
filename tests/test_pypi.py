from unittest.mock import patch, MagicMock
from app.checks.pypi import get_package_signals


@patch("requests.get")
def test_package_exists(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"info": {"name": "requests"}}
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
