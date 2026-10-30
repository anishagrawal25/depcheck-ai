import json
import os
from eval.run_eval import format_markdown_table, load_snippets, run_eval

SNIPPETS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "eval", "snippets.jsonl")
RESULTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "eval", "results.json")


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


def test_run_eval_results_and_markdown():
    results = run_eval()
    assert "rule" in results
    assert "agent" in results
    assert "precision" in results["rule"]
    assert "f1" in results["agent"]
    assert os.path.exists(RESULTS_FILE)

    md = format_markdown_table(results)
    assert "| Mode | Precision | Recall |" in md
    assert "Rule Mode" in md
    assert "Agent Mode" in md
