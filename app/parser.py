import ast
from typing import List


def extract_imports(code: str) -> List[str]:
    """Extract top-level module names from python code."""
    tree = ast.parse(code)
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_level = alias.name.split(".")[0]
                modules.append(top_level)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top_level = node.module.split(".")[0]
                modules.append(top_level)
    return modules
