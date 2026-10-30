from app.rag.ingest import InMemoryChromaCollection, chunk_text, ingest_package


def test_chunk_text():
    text = "word " * 1200
    chunks = chunk_text(text, chunk_size=500)
    assert len(chunks) == 3
    assert len(chunks[0].split()) == 500
    assert len(chunks[1].split()) == 500
    assert len(chunks[2].split()) == 200


def test_ingest_package_json():
    collection = InMemoryChromaCollection(name="test_symbols")
    count = ingest_package("json", collection=collection)
    assert count > 0
    assert collection.count() == count

    # Verify {package, symbol} metadata
    records = list(collection.records.values())
    assert any(
        r["metadata"].get("package") == "json" and "json.dumps" in r["metadata"].get("symbol", "")
        for r in records
    )
