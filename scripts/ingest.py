import argparse
import os
import sys
from typing import List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.ingest import get_collection, ingest_package

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rag_packages.txt")


def load_package_list(path: str = DATA_FILE) -> List[str]:
    """Load package names from text file."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def build_index(packages: List[str], collection=None) -> int:
    """Ingest multiple packages into the vector index."""
    total_chunks = 0
    if collection is None:
        collection = get_collection()

    for pkg in packages:
        try:
            count = ingest_package(pkg, collection=collection)
            print(f"[+] Ingested {pkg}: {count} chunks")
            total_chunks += count
        except (ImportError, Exception) as e:
            print(f"[-] Skipped {pkg}: {e}")

    return total_chunks


def main():
    parser = argparse.ArgumentParser(description="Build RAG vector index from package list")
    parser.add_argument("--file", default=DATA_FILE, help="Path to package list file")
    parser.add_argument("--packages", nargs="*", help="Specific packages to index")
    args = parser.parse_args()

    if args.packages:
        pkgs = args.packages
    else:
        pkgs = load_package_list(args.file)

    print(f"Starting ingestion for {len(pkgs)} packages...")
    total = build_index(pkgs)
    print(f"Ingestion complete. Total chunks: {total}")


if __name__ == "__main__":
    main()
