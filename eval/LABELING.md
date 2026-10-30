# Benchmark Dataset Labeling Methodology

This document outlines the guidelines and methodology used to curate and label snippets in `eval/snippets.jsonl`.

## Schema
Each snippet in `snippets.jsonl` has the following schema:
```json
{
  "id": "snippet_unique_id",
  "code": "Python code snippet containing import statements",
  "fake_packages": ["list", "of", "unverified_or_hallucinated_package_names"]
}
```

## Categories of Packages

1. **Legitimate Packages (`[]`)**:
   - Packages verified to exist on the PyPI registry with mature history, maintainer repositories, and active releases (e.g., `requests`, `pydantic`).
   - Standard library imports (`json`, `sys`, `math`) are filtered out by the AST parser and should never be marked as fake.

2. **Hallucinated Packages**:
   - Packages that do not exist on the PyPI registry. These are often invented by LLMs due to confabulated library names (e.g., `fastjsonparserx`, `totallyfakelib99`, `securecryptoxx`).

3. **Typosquat Packages**:
   - Packages designed with names resembling popular packages (e.g., `reqeusts`, `numpyy`) with high string similarity (>0.85).

## Evaluation Metrics

For each snippet and package evaluated:
- **True Positive (TP)**: Package in `fake_packages` flagged as `hallucinated` or `suspicious`.
- **False Positive (FP)**: Legitimate package incorrectly flagged as `hallucinated` or `suspicious`.
- **False Negative (FN)**: Package in `fake_packages` erroneously labeled `ok`.
- **True Negative (TN)**: Legitimate package correctly labeled `ok`.

Calculated metrics:
- **Precision**: $\frac{\text{TP}}{\text{TP} + \text{FP}}$
- **Recall**: $\frac{\text{TP}}{\text{TP} + \text{FN}}$
- **F1 Score**: $2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$
- **False Positive Rate (FPR)**: $\frac{\text{FP}}{\text{FP} + \text{TN}}$
- **Average Latency**: Mean wall-clock time per snippet in seconds.
