import importlib
import inspect
from typing import Any, Dict, List


def extract_symbols(package_name: str) -> List[Dict[str, Any]]:
    """
    Extract public module-level functions and classes with docstrings for an installed package.
    """
    try:
        module = importlib.import_module(package_name)
    except ImportError as e:
        raise ImportError(f"Cannot import package '{package_name}': {e}") from e

    symbols: List[Dict[str, Any]] = []

    for name, obj in inspect.getmembers(module):
        # Exclude private/dunder attributes
        if name.startswith("_"):
            continue

        is_func = inspect.isfunction(obj) or inspect.isbuiltin(obj)
        is_cls = inspect.isclass(obj)

        if not (is_func or is_cls):
            continue

        doc = inspect.getdoc(obj) or ""
        kind = "function" if is_func else "class"

        symbols.append({
            "package": package_name,
            "name": name,
            "symbol": f"{package_name}.{name}",
            "kind": kind,
            "docstring": doc,
        })

    return sorted(symbols, key=lambda s: s["name"])
