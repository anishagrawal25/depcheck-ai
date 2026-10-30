from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, Query
from app.checks.pypi import get_package_signals
from app.checks.typosquat import find_similar
from app.llm import explain_finding
from app.parser import extract_imports, to_pypi_name
from app.schemas import Finding, ScanReport, ScanRequest
from app.scoring import score_package

app = FastAPI(title="depcheck-ai", version="0.1.0")


def _inspect_package(pkg_name: str) -> Finding:
    signals = get_package_signals(pkg_name)
    similar = find_similar(pkg_name)
    return score_package(signals, similar=similar)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/scan", response_model=ScanReport)
def scan_code(req: ScanRequest, use_llm: bool = Query(default=False)) -> ScanReport:
    try:
        raw_imports = extract_imports(req.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    seen_pkgs = set()
    unique_pkgs = []

    for imp in raw_imports:
        pkg = to_pypi_name(imp)
        if pkg not in seen_pkgs:
            seen_pkgs.add(pkg)
            unique_pkgs.append(pkg)

    if not unique_pkgs:
        return ScanReport(findings=[], scanned_imports=len(raw_imports))

    with ThreadPoolExecutor() as executor:
        findings = list(executor.map(_inspect_package, unique_pkgs))

    if use_llm:
        for finding in findings:
            if finding.verdict != "ok":
                exp = explain_finding(finding, req.code)
                if exp.explanation:
                    finding.reasons = [exp.explanation]
                if exp.suggested_fix:
                    finding.suggested_fix = exp.suggested_fix

    return ScanReport(findings=findings, scanned_imports=len(raw_imports))
