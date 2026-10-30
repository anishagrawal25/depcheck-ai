from app.rag.ingest import InMemoryChromaCollection, chunk_text, ingest_package
from scripts.ingest import build_index, load_package_list


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


def test_build_index_two_packages():
    collection = InMemoryChromaCollection(name="test_multi_ingest")
    total = build_index(["json", "requests"], collection=collection)
    assert total > 0

    packages_in_meta = {r["metadata"]["package"] for r in collection.records.values()}
    assert "json" in packages_in_meta
    assert "requests" in packages_in_meta


def test_load_package_list_loads_file(tmp_path):
    p = tmp_path / "pkgs.txt"
    p.write_text("requests\n# comment\nnumpy\n")
    loaded = load_package_list(str(p))
    assert loaded == ["requests", "numpy"]
