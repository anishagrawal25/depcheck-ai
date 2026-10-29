import difflib
import os
from typing import List, Optional

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "top_packages.txt")

_POPULAR_PACKAGES: Optional[List[str]] = None


def get_popular_packages() -> List[str]:
    """Load popular package names from data/top_packages.txt with fallback."""
    global _POPULAR_PACKAGES
    if _POPULAR_PACKAGES is not None:
        return _POPULAR_PACKAGES

    packages = []
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    name = line.strip()
                    if name:
                        packages.append(name)
        except OSError:
            pass

    if not packages:
        # Fallback list of very common packages
        packages = [
            "requests", "numpy", "pandas", "boto3", "urllib3", "pydantic",
            "fastapi", "flask", "django", "pytest", "scipy", "torch",
        ]

    _POPULAR_PACKAGES = packages
    return _POPULAR_PACKAGES


def find_similar(name: str, threshold: float = 0.85) -> List[str]:
    """
    Find popular packages with similarity above threshold that are not identical.
    """
    target = name.strip().lower()
    popular_pkgs = get_popular_packages()
    matches: List[str] = []

    for pkg in popular_pkgs:
        pkg_lower = pkg.lower()
        if pkg_lower == target:
            # Skip identical packages
            continue

        similarity = difflib.SequenceMatcher(None, target, pkg_lower).ratio()
        if similarity >= threshold:
            matches.append(pkg)

    return matches
