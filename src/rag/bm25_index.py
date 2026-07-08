import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from src.config import CHUNKS_PATH, EXCLUDED_DOC_TYPES

_chunks: list[dict] | None = None
_bm25: BM25Okapi | None = None
_index_map: list[int] | None = None


def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"a/l", " al examination ", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return [t for t in text.split() if t]


def _chunk_metadata(chunk: dict) -> dict:
    return {
        "academic_year": chunk["academic_year"],
        "language": chunk["language"],
        "source_file": chunk["source_file"],
        "page_start": chunk["page_start"],
        "page_end": chunk["page_end"],
        "section": chunk.get("section") or "",
        "doc_type": chunk.get("doc_type", "content"),
    }


def load_bm25() -> tuple[BM25Okapi, list[dict]]:
    global _chunks, _bm25, _index_map
    if _bm25 is not None and _chunks is not None and _index_map is not None:
        return _bm25, _chunks

    all_chunks = [
        json.loads(line)
        for line in Path(CHUNKS_PATH).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    _chunks = []
    _index_map = []
    for idx, chunk in enumerate(all_chunks):
        if chunk.get("doc_type", "content") in EXCLUDED_DOC_TYPES:
            continue
        _chunks.append(chunk)
        _index_map.append(idx)

    corpus = [tokenize(c["text"]) for c in _chunks]
    _bm25 = BM25Okapi(corpus)
    return _bm25, _chunks


def search_bm25(query: str, top_k: int = 20) -> list[dict]:
    bm25, chunks = load_bm25()
    scores = bm25.get_scores(tokenize(query))

    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True,
    )[:top_k]

    hits = []
    for idx, score in ranked:
        if score <= 0:
            continue
        chunk = chunks[idx]
        hits.append(
            {
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "metadata": _chunk_metadata(chunk),
                "bm25_score": float(score),
            }
        )
    return hits
