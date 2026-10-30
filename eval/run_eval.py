import json
import os
import sys
import time
from typing import Any, Dict, List

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import scan_code
from app.schemas import ScanRequest

DATA_PATH = os.path.join(os.path.dirname(__file__), "snippets.jsonl")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results.json")


def load_snippets(path: str = DATA_PATH) -> List[Dict[str, Any]]:
    snippets = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                snippets.append(json.loads(line))
    return snippets


def evaluate_mode(snippets: List[Dict[str, Any]], mode: str = "rule") -> Dict[str, float]:
    tp = 0
    fp = 0
    fn = 0
    tn = 0
    latencies = []

    for entry in snippets:
        code = entry["code"]
        expected_fakes = set(entry.get("fake_packages", []))

        start_time = time.perf_counter()
        report = scan_code(ScanRequest(code=code), mode=mode)
        latency = time.perf_counter() - start_time
        latencies.append(latency)

        findings_by_pkg = {f.package: f for f in report.findings}

        for pkg, finding in findings_by_pkg.items():
            is_flagged = finding.verdict in ("suspicious", "hallucinated")
            is_truth_fake = pkg in expected_fakes

            if is_flagged and is_truth_fake:
                tp += 1
            elif is_flagged and not is_truth_fake:
                fp += 1
            elif not is_flagged and is_truth_fake:
                fn += 1
            else:
                tn += 1

        # Check for expected fakes that weren't even in findings
        for fake_pkg in expected_fakes:
            if fake_pkg not in findings_by_pkg:
                fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "avg_latency": round(avg_latency, 4),
    }


def format_markdown_table(results: Dict[str, Dict[str, float]]) -> str:
    lines = [
        "| Mode | Precision | Recall | F1 Score | False Positive Rate | Avg Latency (s) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    for mode, metrics in results.items():
        mode_label = "Rule Mode" if mode == "rule" else "Agent Mode"
        lines.append(
            f"| **{mode_label}** | {metrics['precision']:.2f} | {metrics['recall']:.2f} | "
            f"{metrics['f1']:.2f} | {metrics['false_positive_rate']:.2f} | {metrics['avg_latency']:.4f}s |"
        )
    return "\n".join(lines)


def run_eval() -> Dict[str, Dict[str, float]]:
    snippets = load_snippets()
    results = {}

    for mode in ["rule", "agent"]:
        print(f"Evaluating {mode} mode on {len(snippets)} snippets...")
        results[mode] = evaluate_mode(snippets, mode=mode)

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    table = format_markdown_table(results)
    print("\nBenchmark Results:")
    print(table)
    return results


if __name__ == "__main__":
    run_eval()
