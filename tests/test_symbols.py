import pytest
from app.rag.symbols import extract_symbols


def test_extract_symbols_json():
    symbols = extract_symbols("json")
    assert isinstance(symbols, list)
    assert len(symbols) > 0

    names = {s["name"] for s in symbols}
    assert "dumps" in names
    assert "loads" in names
    assert "load" in names
    assert "dump" in names
    assert "JSONDecoder" in names
    assert "JSONEncoder" in names

    # Check structure
    dumps_symbol = next(s for s in symbols if s["name"] == "dumps")
    assert dumps_symbol["package"] == "json"
    assert dumps_symbol["symbol"] == "json.dumps"
    assert dumps_symbol["kind"] == "function"
    assert "Serialize" in dumps_symbol["docstring"] or len(dumps_symbol["docstring"]) > 0

    decoder_symbol = next(s for s in symbols if s["name"] == "JSONDecoder")
    assert decoder_symbol["package"] == "json"
    assert decoder_symbol["kind"] == "class"
    assert len(decoder_symbol["docstring"]) > 0


def test_extract_symbols_nonexistent_package():
    with pytest.raises(ImportError):
        extract_symbols("non_existent_package_xyz123")
