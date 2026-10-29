import ast
import sys
from typing import List, Set

STDLIB_MODULES: Set[str] = getattr(sys, "stdlib_module_names", set())


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
