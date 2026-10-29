import requests
from app.schemas import PackageSignals


def get_package_signals(name: str) -> PackageSignals:
    """Fetch package signals from PyPI JSON API."""
    url = f"https://pypi.org/pypi/{name}/json"
    response = requests.get(url)

    if response.status_code == 404:
        return PackageSignals(name=name, exists=False)

    if response.status_code == 200:
        return PackageSignals(name=name, exists=True)

    return PackageSignals(name=name, exists=False)
