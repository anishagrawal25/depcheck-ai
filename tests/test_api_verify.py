from app.checks.api_verify import verify_api_call
from app.rag.ingest import InMemoryChromaCollection


def test_verify_api_call_requests_get():
    result = verify_api_call("requests", "get")
    assert result == "found"


def test_verify_api_call_requests_gett():
    result = verify_api_call("requests", "gett")
    assert result == "not_found"


def test_verify_api_call_unknown_package():
    result = verify_api_call("non_existent_package_abc123", "func")
    assert result == "unknown"


def test_verify_api_call_chroma_first():
    # Test Chroma check finds the symbol
    collection = InMemoryChromaCollection(name="test_verify_collection")
    collection.add(
        ids=["doc_1"],
        documents=["Symbol: custompkg.do_something"],
        metadatas=[{"package": "custompkg", "symbol": "custompkg.do_something"}],
    )
    result = verify_api_call("custompkg", "do_something", collection=collection)
    assert result == "found"
