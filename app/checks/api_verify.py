import importlib
from typing import Literal, Optional
from app.rag.ingest import get_collection

VerificationResult = Literal["found", "not_found", "unknown"]


def verify_api_call(package: str, symbol: str, collection=None) -> VerificationResult:
    """
    Verify if an API symbol exists in a package.
    Checks Chroma first, then hasattr on the installed module.
    Returns: 'found', 'not_found', or 'unknown'.
    """
    # 1. Check Chroma first
    try:
        if collection is None:
            collection = get_collection()

        full_symbol = symbol if symbol.startswith(f"{package}.") else f"{package}.{symbol}"

        results = collection.query(
            query_texts=[full_symbol],
            n_results=5,
            where={"package": package},
        )
        metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
        for meta in metadatas:
            if meta:
                meta_symbol = meta.get("symbol", "")
                if meta_symbol == full_symbol or meta_symbol == symbol or meta.get("name") == symbol:
                    return "found"
    except Exception:
        pass

    # 2. Check hasattr on installed module
    try:
        mod = importlib.import_module(package)
    except (ImportError, Exception):
        return "unknown"

    curr = mod
    sub_symbol = symbol[len(package) + 1 :] if symbol.startswith(f"{package}.") else symbol
    parts = sub_symbol.split(".")

    for part in parts:
        if hasattr(curr, part):
            try:
                curr = getattr(curr, part)
            except Exception:
                return "unknown"
        else:
            return "not_found"

    return "found"
