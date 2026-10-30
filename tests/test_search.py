from app.rag.ingest import InMemoryChromaCollection, ingest_package
from app.rag.search import search_docs


def test_search_docs_requests_get():
    collection = InMemoryChromaCollection(name="test_search_symbols")
    ingest_package("requests", collection=collection)

    results = search_docs("requests", "requests.get", k=3, collection=collection)
    assert len(results) > 0
    symbols = [r["symbol"] for r in results]
    assert "requests.get" in symbols or any("get" in s for s in symbols)


def test_search_docs_empty_collection():
    collection = InMemoryChromaCollection(name="empty_symbols")
    results = search_docs("nonexistent", "some query", k=3, collection=collection)
    assert results == []
