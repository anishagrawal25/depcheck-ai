"""Scoring engine for package risk assessment."""

WEIGHTS = {
    "age": 0.2,
    "releases": 0.2,
    "repo": 0.2,
    "typosquat": 0.4,
}
