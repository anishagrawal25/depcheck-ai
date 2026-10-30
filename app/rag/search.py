from typing import Any, Dict, List, Optional
from app.rag.ingest import get_collection


def search_docs(
    package: str,
    query: str,
    k: int = 3,
    collection=None,
) -> List[Dict[str, Any]]:
    """
    Search indexed documentation for a given package and query.
    Returns up to k matching documents with metadata and distance.
    """
    if collection is None:
        collection = get_collection()

    where_filter = {"package": package}
    results = collection.query(
        query_texts=[query],
        n_results=k,
        where=where_filter,
    )

    docs = results.get("documents", [[]])[0] if results.get("documents") else []
    metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
    distances = results.get("distances", [[]])[0] if results.get("distances") else [0.0] * len(docs)
    ids = results.get("ids", [[]])[0] if results.get("ids") else []

    matches: List[Dict[str, Any]] = []
    for doc_id, doc, meta, dist in zip(ids, docs, metadatas, distances):
        matches.append({
            "id": doc_id,
            "document": doc,
            "metadata": meta,
            "symbol": meta.get("symbol", "") if meta else "",
            "distance": dist,
        })

    return matches
