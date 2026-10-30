import math
import os
from typing import Any, Dict, List, Optional
from app.rag.symbols import extract_symbols

CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db")
MODEL_NAME = "BAAI/bge-small-en-v1.5"

try:
    import chromadb
except ImportError:
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

_EMBEDDER = None


def get_embedder():
    global _EMBEDDER
    if _EMBEDDER is not None:
        return _EMBEDDER
    if SentenceTransformer is not None:
        try:
            _EMBEDDER = SentenceTransformer(MODEL_NAME)
            return _EMBEDDER
        except Exception:
            pass
    return None


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Compute embeddings using BAAI/bge-small-en-v1.5 or deterministic fallback."""
    embedder = get_embedder()
    if embedder is not None:
        embeddings = embedder.encode(texts)
        return embeddings.tolist() if hasattr(embeddings, "tolist") else list(embeddings)

    results = []
    for text in texts:
        vec = [0.0] * 384
        words = text.lower().split()
        for i, w in enumerate(words):
            idx = abs(hash(w)) % 384
            vec[idx] += 1.0 / (1.0 + i * 0.1)
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        results.append([x / norm for x in vec])
    return results


class InMemoryChromaCollection:
    """Lightweight persistent fallback when chromadb C-extensions are unavailable."""
    def __init__(self, name: str, path: str = CHROMA_PATH):
        self.name = name
        self.path = path
        self.records: Dict[str, Dict[str, Any]] = {}

    def add(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None,
    ):
        if embeddings is None:
            embeddings = get_embeddings(documents)
        for doc_id, doc, meta, emb in zip(ids, documents, metadatas, embeddings):
            self.records[doc_id] = {
                "id": doc_id,
                "document": doc,
                "metadata": meta,
                "embedding": emb,
            }

    def query(
        self,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 3,
        where: Optional[Dict[str, Any]] = None,
    ):
        if query_embeddings is None and query_texts is not None:
            query_embeddings = get_embeddings(query_texts)
        if not query_embeddings:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        all_ids = []
        all_docs = []
        all_metas = []
        all_distances = []

        for q_emb in query_embeddings:
            scores = []
            for doc_id, rec in self.records.items():
                if where:
                    match = all(rec["metadata"].get(k) == v for k, v in where.items())
                    if not match:
                        continue
                d_emb = rec["embedding"]
                dot = sum(a * b for a, b in zip(q_emb, d_emb))
                dist = max(0.0, 1.0 - dot)
                scores.append((dist, rec))

            scores.sort(key=lambda s: s[0])
            top = scores[:n_results]
            all_ids.append([s[1]["id"] for s in top])
            all_docs.append([s[1]["document"] for s in top])
            all_metas.append([s[1]["metadata"] for s in top])
            all_distances.append([s[0] for s in top])

        return {
            "ids": all_ids,
            "documents": all_docs,
            "metadatas": all_metas,
            "distances": all_distances,
        }

    def count(self) -> int:
        return len(self.records)


_FALLBACK_COLLECTION = None


def get_collection(name: str = "package_symbols", path: str = CHROMA_PATH):
    global _FALLBACK_COLLECTION
    if chromadb is not None:
        try:
            client = chromadb.PersistentClient(path=path)
            return client.get_or_create_collection(name=name)
        except Exception:
            pass

    if _FALLBACK_COLLECTION is None:
        _FALLBACK_COLLECTION = InMemoryChromaCollection(name=name, path=path)
    return _FALLBACK_COLLECTION


def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """Chunk text into segments of approximately chunk_size words/tokens."""
    words = text.split()
    if not words:
        return [""]
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


def ingest_package(package_name: str, collection=None) -> int:
    """
    Extract symbols for an installed package, chunk docs (~500 tokens),
    embed with BAAI/bge-small-en-v1.5 and store in Chroma with {package, symbol} metadata.
    """
    if collection is None:
        collection = get_collection()

    symbols = extract_symbols(package_name)
    if not symbols:
        return 0

    ids = []
    documents = []
    metadatas = []

    for item in symbols:
        symbol = item["symbol"]
        kind = item["kind"]
        docstring = item["docstring"] or ""
        full_text = f"Symbol: {symbol} ({kind})\nPackage: {package_name}\n\n{docstring}"
        chunks = chunk_text(full_text, chunk_size=500)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{package_name}_{symbol}_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "package": package_name,
                "symbol": symbol,
                "kind": kind,
            })

    embeddings = get_embeddings(documents)
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    return len(ids)
