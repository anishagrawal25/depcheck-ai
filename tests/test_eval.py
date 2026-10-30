import json
import os

SNIPPETS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "eval", "snippets.jsonl")


def test_snippets_jsonl_format():
    assert os.path.exists(SNIPPETS_FILE)
    with open(SNIPPETS_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    assert len(lines) >= 5
    for line in lines:
        entry = json.loads(line)
        assert "id" in entry
        assert "code" in entry
        assert "fake_packages" in entry
        assert isinstance(entry["fake_packages"], list)
