import ast
import re
import sys
from typing import Dict, List, Set

STDLIB_MODULES: Set[str] = getattr(sys, "stdlib_module_names", set())

IMPORT_TO_PYPI: Dict[str, str] = {
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "bs4": "beautifulsoup4",
    "dotenv": "python-dotenv",
    "dateutil": "python-dateutil",
    "jose": "python-jose",
    "magic": "python-magic",
    "multipart": "python-multipart",
    "git": "GitPython",
    "serial": "pyserial",
    "jwt": "PyJWT",
    "Bio": "biopython",
    "Crypto": "pycryptodome",
    "OpenSSL": "pyOpenSSL",
    "socketio": "python-socketio",
}


def to_pypi_name(import_name: str) -> str:
    """Map top-level Python import name to canonical PyPI package name."""
    return IMPORT_TO_PYPI.get(import_name, import_name)


def extract_imports(code: str) -> List[str]:
    """Extract external (non-stdlib, non-relative) top-level module names from python code."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Syntax error at line {e.lineno}: {e.msg}") from e

    modules: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_level = alias.name.split(".")[0]
                if top_level and top_level not in STDLIB_MODULES:
                    modules.add(top_level)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                top_level = node.module.split(".")[0]
                if top_level and top_level not in STDLIB_MODULES:
                    modules.add(top_level)

    return sorted(list(modules))


def parse_requirements(text: str) -> List[str]:
    """Parse packages from requirements.txt content, handling specifiers, comments, extras, and flags."""
    packages: Set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Remove trailing comments
        line = line.split("#")[0].strip()
        if not line:
            continue
        # Exclude flags like -r, -i, --extra-index-url
        if line.startswith("-") or line.startswith("--"):
            continue
        # Exclude environment markers
        line = line.split(";")[0].strip()
        # Extract base package name ignoring extras e.g. package[extra]
        match = re.match(r"^([a-zA-Z0-9_\.\-]+)(?:\[[^\]]*\])?", line)
        if match:
            pkg_name = match.group(1).strip()
            if pkg_name:
                packages.add(pkg_name)

    return sorted(list(packages))
