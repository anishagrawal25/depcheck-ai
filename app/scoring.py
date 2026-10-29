"""Scoring engine for package risk assessment."""
from typing import List, Optional
from app.schemas import Finding, PackageSignals

WEIGHTS = {
    "age": 0.2,
    "releases": 0.2,
    "repo": 0.2,
    "typosquat": 0.4,
}


def score_package(signals: PackageSignals, similar: Optional[List[str]] = None) -> Finding:
    """Score package risk based on registry signals and typosquat similarity."""
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
            reasons=["Package does not exist on PyPI"],
            suggested_fix=suggested_fix,
        )

    risk_score = 0.0
    reasons: List[str] = []
    suggested_fix: Optional[str] = None

    # Rule: Age under 30 days
    if signals.age_days is not None and signals.age_days < 30:
        risk_score += WEIGHTS["age"]
        reasons.append(f"Package is newly created ({signals.age_days} days old)")

    # Rule: Release count under 3
    if signals.release_count is not None and signals.release_count < 3:
        risk_score += WEIGHTS["releases"]
        reasons.append(f"Low release count ({signals.release_count} releases)")

    # Rule: No repository link
    if signals.has_repo is False:
        risk_score += WEIGHTS["repo"]
        reasons.append("No source repository link found in package metadata")

    # Rule: Typosquat similarity to popular packages
    if similar:
        risk_score += WEIGHTS["typosquat"]
        reasons.append(f"Name is very similar to popular package(s): {', '.join(similar)}")
        suggested_fix = f"Did you mean '{similar[0]}'?"

    verdict = "suspicious" if risk_score >= 0.5 else "ok"
    confidence = 0.85 if signals.exists is True else 0.5

    return Finding(
        package=signals.name,
        verdict=verdict,
        risk_score=min(1.0, round(risk_score, 2)),
        confidence=confidence,
        reasons=reasons,
        suggested_fix=suggested_fix,
    )
