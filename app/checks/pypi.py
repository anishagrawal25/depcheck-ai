from datetime import datetime, timezone
from typing import Dict, Optional
import requests
from app.config import REQUEST_TIMEOUT
from app.schemas import PackageSignals

_CACHE: Dict[str, PackageSignals] = {}


def clear_cache() -> None:
    """Clear the in-memory package signals cache."""
    _CACHE.clear()


def _check_has_repo(info: dict) -> bool:
    """Check if project_urls or home_page has a GitHub or GitLab URL."""
    urls_to_check = []
    home_page = info.get("home_page")
    if home_page and isinstance(home_page, str):
        urls_to_check.append(home_page)

    project_urls = info.get("project_urls")
    if project_urls and isinstance(project_urls, dict):
        for val in project_urls.values():
            if val and isinstance(val, str):
                urls_to_check.append(val)

    for url in urls_to_check:
        url_lower = url.lower()
        if "github.com" in url_lower or "gitlab.com" in url_lower:
            return True
    return False


def get_package_signals(name: str) -> PackageSignals:
    """Fetch package signals from PyPI JSON API with timeout, caching, and error handling."""
    normalized_name = name.strip().lower()
    if normalized_name in _CACHE:
        return _CACHE[normalized_name]

    url = f"https://pypi.org/pypi/{name}/json"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException:
        # Return a clear unknown state (exists=None), not a crash
        signals = PackageSignals(name=name, exists=None)
        _CACHE[normalized_name] = signals
        return signals

    if response.status_code == 404:
        signals = PackageSignals(name=name, exists=False)
        _CACHE[normalized_name] = signals
        return signals

    if response.status_code == 200:
        try:
            data = response.json()
        except ValueError:
            signals = PackageSignals(name=name, exists=None)
            _CACHE[normalized_name] = signals
            return signals

        info = data.get("info", {})
        releases = data.get("releases", {})
        release_count = len(releases)
        has_repo = _check_has_repo(info)

        earliest_upload: Optional[datetime] = None
        for version, files in releases.items():
            for file_info in files:
                upload_str = file_info.get("upload_time_iso_8601") or file_info.get("upload_time")
                if upload_str:
                    try:
                        if upload_str.endswith("Z"):
                            upload_str = upload_str[:-1] + "+00:00"
                        dt = datetime.fromisoformat(upload_str)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        if earliest_upload is None or dt < earliest_upload:
                            earliest_upload = dt
                    except (ValueError, TypeError):
                        continue

        age_days = None
        if earliest_upload:
            now = datetime.now(timezone.utc)
            age_days = max(0, (now - earliest_upload).days)

        signals = PackageSignals(
            name=name,
            exists=True,
            age_days=age_days,
            release_count=release_count,
            has_repo=has_repo,
        )
        _CACHE[normalized_name] = signals
        return signals

    signals = PackageSignals(name=name, exists=None)
    _CACHE[normalized_name] = signals
    return signals
