from datetime import datetime, timezone
from typing import Optional
import requests
from app.schemas import PackageSignals


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
    """Fetch package signals from PyPI JSON API, including age_days, release_count, and has_repo."""
    url = f"https://pypi.org/pypi/{name}/json"
    response = requests.get(url)

    if response.status_code == 404:
        return PackageSignals(name=name, exists=False)

    if response.status_code == 200:
        data = response.json()
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

        return PackageSignals(
            name=name,
            exists=True,
            age_days=age_days,
            release_count=release_count,
            has_repo=has_repo,
        )

    return PackageSignals(name=name, exists=False)
