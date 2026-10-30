"""Scoring engine for package risk assessment."""
from typing import Any, List, Optional
from app.schemas import Finding, PackageSignals

WEIGHTS = {
    "age": 0.2,
    "releases": 0.2,
    "repo": 0.2,
    "typosquat": 0.4,
    "vulnerabilities": 0.05,
}


def score_package(
    signals: PackageSignals,
    similar: Optional[List[str]] = None,
    vulnerabilities: Optional[Any] = None,
) -> Finding:
    """Score package risk based on registry signals, typosquat similarity, and known vulnerabilities."""
    if similar is None:
        similar = []

    # Rule: Not exists on PyPI = hallucinated
    if signals.exists is False:
        suggested_fix = f"Did you mean '{similar[0]}'?" if similar else None
        return Finding(
            package=signals.name,
            verdict="hallucinated",
            risk_score=0.95,
            confidence=0.95,
            reasons=[f"Package '{signals.name}' does not exist on the PyPI registry."],
            suggested_fix=suggested_fix,
        )

    # Unknown state (e.g. timeout / network error)
    if signals.exists is None:
        return Finding(
            package=signals.name,
            verdict="ok",
            risk_score=0.0,
            confidence=0.3,
            reasons=["Package existence could not be verified due to network lookup issues."],
        )

    risk_score = 0.0
    reasons: List[str] = []
    suggested_fix: Optional[str] = None

    # Rule: Age under 30 days
    if signals.age_days is not None and signals.age_days < 30:
        risk_score += WEIGHTS["age"]
        reasons.append(
            f"Package '{signals.name}' is newly published ({signals.age_days} days old, under 30-day threshold)."
        )

    # Rule: Release count under 3
    if signals.release_count is not None and signals.release_count < 3:
        risk_score += WEIGHTS["releases"]
        reasons.append(
            f"Package '{signals.name}' has a low release count ({signals.release_count} release(s), fewer than 3)."
        )

    # Rule: No repository link
    if signals.has_repo is False:
        risk_score += WEIGHTS["repo"]
        reasons.append(
            f"No public source repository (GitHub or GitLab) was found in package metadata."
        )

    # Rule: Typosquat similarity to popular packages
    if similar:
        risk_score += WEIGHTS["typosquat"]
        reasons.append(
            f"Package name '{signals.name}' is highly similar to popular package(s): {', '.join(similar)}."
        )
        suggested_fix = f"Did you mean '{similar[0]}'?"

    # Rule: Known vulnerabilities (OSV)
    if vulnerabilities:
        count = None
        ids = None
        if hasattr(vulnerabilities, "vuln_ids"):
            val = getattr(vulnerabilities, "count", None)
            if isinstance(val, int):
                count = val
            ids = getattr(vulnerabilities, "vuln_ids", None)

        if count is None and isinstance(vulnerabilities, (tuple, list)):
            if len(vulnerabilities) == 2 and isinstance(vulnerabilities[0], int):
                count, ids = vulnerabilities[0], vulnerabilities[1]
            else:
                count, ids = len(vulnerabilities), list(vulnerabilities)
        elif count is None and isinstance(vulnerabilities, int):
            count, ids = vulnerabilities, []

        if isinstance(count, int) and count > 0:
            risk_score += WEIGHTS["vulnerabilities"]
            ids_str = f" ({', '.join(ids[:3])})" if ids else ""
            reasons.append(
                f"Package '{signals.name}' has {count} known vulnerability/vulnerabilities reported in OSV{ids_str}."
            )

    verdict = "suspicious" if risk_score >= 0.5 else "ok"
    confidence = 0.85

    return Finding(
        package=signals.name,
        verdict=verdict,
        risk_score=min(1.0, round(risk_score, 2)),
        confidence=confidence,
        reasons=reasons,
        suggested_fix=suggested_fix,
    )
