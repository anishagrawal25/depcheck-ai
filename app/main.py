from fastapi import FastAPI
from app.checks.pypi import get_package_signals
from app.checks.typosquat import find_similar
from app.parser import extract_imports, to_pypi_name
from app.schemas import ScanReport, ScanRequest
from app.scoring import score_package

app = FastAPI(title="depcheck-ai", version="0.1.0")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/scan", response_model=ScanReport)
def scan_code(req: ScanRequest) -> ScanReport:
    raw_imports = extract_imports(req.code)
    seen_pkgs = set()
    findings = []

    for imp in raw_imports:
        pkg_name = to_pypi_name(imp)
        if pkg_name in seen_pkgs:
            continue
        seen_pkgs.add(pkg_name)

        signals = get_package_signals(pkg_name)
        similar = find_similar(pkg_name)
        finding = score_package(signals, similar=similar)
        findings.append(finding)

    return ScanReport(findings=findings, scanned_imports=len(raw_imports))
