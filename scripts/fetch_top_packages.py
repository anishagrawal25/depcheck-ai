#!/usr/bin/env python3
import json
import os
import requests

TOP_PACKAGES_URL = "https://hugovk.dev/top-pypi-packages/top-pypi-packages-30-days.min.json"
FALLBACK_URL = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "top_packages.txt")


def fetch_top_packages(limit: int = 500) -> list[str]:
    """Download the top PyPI packages from hugovk dataset."""
    urls = [TOP_PACKAGES_URL, FALLBACK_URL]
    for url in urls:
        try:
            response = requests.get(url, timeout=30, allow_redirects=True)
            if response.status_code == 200:
                data = response.json()
                rows = data.get("rows", [])
                packages = [row["project"] for row in rows[:limit] if "project" in row]
                if packages:
                    return packages
        except Exception as e:
            print(f"Warning: Failed to fetch from {url}: {e}")
            continue

    raise RuntimeError("Failed to fetch top packages from all sources.")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Fetching top 500 PyPI packages...")
    packages = fetch_top_packages(500)
    print(f"Writing {len(packages)} packages to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for pkg in packages:
            f.write(f"{pkg}\n")
    print(f"Successfully generated {OUTPUT_FILE} with {len(packages)} packages.")


if __name__ == "__main__":
    main()
