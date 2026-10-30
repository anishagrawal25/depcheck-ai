from typing import Dict, List, NamedTuple
import requests
from app.config import REQUEST_TIMEOUT

OSV_QUERY_URL = "https://api.osv.dev/v1/query"

_CACHE: Dict[str, "VulnerabilityResult"] = {}


class VulnerabilityResult(NamedTuple):
    count: int
    vuln_ids: List[str]


def clear_cache() -> None:
    _CACHE.clear()


def check_vulnerabilities(name: str, timeout: int = REQUEST_TIMEOUT) -> VulnerabilityResult:
    """
    Check OSV database for known PyPI vulnerabilities.
    Returns (count, top_3_vuln_ids).
    """
    normalized = name.strip().lower()
    if normalized in _CACHE:
        return _CACHE[normalized]

    payload = {
        "package": {
            "name": name,
            "ecosystem": "PyPI",
        }
    }

    try:
        response = requests.post(OSV_QUERY_URL, json=payload, timeout=timeout)
    except requests.RequestException:
        result = VulnerabilityResult(count=0, vuln_ids=[])
        _CACHE[normalized] = result
        return result

    if response.status_code != 200:
        result = VulnerabilityResult(count=0, vuln_ids=[])
        _CACHE[normalized] = result
        return result

    try:
        data = response.json()
    except ValueError:
        result = VulnerabilityResult(count=0, vuln_ids=[])
        _CACHE[normalized] = result
        return result

    vulns = data.get("vulns", [])
    vuln_ids: List[str] = []
    for v in vulns:
        if isinstance(v, dict) and "id" in v:
            vuln_ids.append(v["id"])

    result = VulnerabilityResult(count=len(vuln_ids), vuln_ids=vuln_ids[:3])
    _CACHE[normalized] = result
    return result
