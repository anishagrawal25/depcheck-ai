from datetime import datetime, timezone
from typing import Optional
import requests
from app.schemas import PackageSignals


def get_package_signals(name: str) -> PackageSignals:
    """Fetch package signals from PyPI JSON API, including age_days and release_count."""
    url = f"https://pypi.org/pypi/{name}/json"
    response = requests.get(url)

    if response.status_code == 404:
        return PackageSignals(name=name, exists=False)

    if response.status_code == 200:
        data = response.json()
        releases = data.get("releases", {})
        release_count = len(releases)

        earliest_upload: Optional[datetime] = None
        for version, files in releases.items():
            for file_info in files:
                upload_str = file_info.get("upload_time_iso_8601") or file_info.get("upload_time")
                if upload_str:
                    try:
                        # Handle trailing Z or timezone offsets
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
        )

    return PackageSignals(name=name, exists=False)
