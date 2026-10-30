from typing import Any, Dict, List
from langchain_core.tools import tool
from app.checks.api_verify import verify_api_call as _verify_api_call
from app.checks.osv import check_vulnerabilities as _check_osv
from app.checks.pypi import get_package_signals
from app.checks.typosquat import find_similar as _find_similar
from app.rag.search import search_docs as _search_docs


@tool
def check_registry(package: str) -> Dict[str, Any]:
    """Check PyPI registry metadata for a package, including existence, age, release count, and repository link."""
    signals = get_package_signals(package)
    return {
        "name": signals.name,
        "exists": signals.exists,
        "age_days": signals.age_days,
        "release_count": signals.release_count,
        "has_repo": signals.has_repo,
    }


@tool
def search_docs(package: str, query: str) -> List[Dict[str, Any]]:
    """Search vector documentation index for symbols and usage within a package."""
    return _search_docs(package, query, k=3)


@tool
def check_osv(package: str) -> Dict[str, Any]:
    """Check OSV database for known security vulnerabilities in a package."""
    res = _check_osv(package)
    return {
        "count": res.count,
        "vuln_ids": res.vuln_ids,
    }


@tool
def find_similar_package(package: str) -> List[str]:
    """Find popular packages that are typographically similar to the given package name."""
    return _find_similar(package)


@tool
def verify_api_call(package: str, symbol: str) -> str:
    """Verify if a specific function, class, or symbol exists in a package (returns found, not_found, or unknown)."""
    return _verify_api_call(package, symbol)


ALL_TOOLS = [
    check_registry,
    search_docs,
    check_osv,
    find_similar_package,
    verify_api_call,
]
