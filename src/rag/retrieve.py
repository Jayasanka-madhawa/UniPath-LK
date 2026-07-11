import threading

import chromadb
import ollama

from src.config import (
    CHROMA_PATH,
    COLLECTION_NAME,
    EMBED_MODEL,
    EXCLUDED_DOC_TYPES,
    MIN_RRF_SCORE,
    RETRIEVE_CANDIDATES,
    RETRIEVE_TOP_K,
    RRF_K,
)
from src.rag.bm25_index import search_bm25

_embed_lock = threading.Lock()


def _chunk_to_hit(chunk_id: str, text: str, metadata: dict, **extra) -> dict:
    return {
        "chunk_id": chunk_id,
        "text": text,
        "metadata": metadata,
        **extra,
    }


def is_retrievable(hit: dict) -> bool:
    doc_type = hit.get("metadata", {}).get("doc_type", "content")
    return doc_type not in EXCLUDED_DOC_TYPES


def search_vector(query: str, top_k: int = RETRIEVE_CANDIDATES) -> list[dict]:
    query = (query or "").strip()
    if not query:
        return []

    with _embed_lock:
        query_vector = ollama.embeddings(
            model=EMBED_MODEL,
            prompt=query,
        )["embedding"]

    if not query_vector:
        return []

    db = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = db.get_collection(COLLECTION_NAME)

    try:
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
        )
    except (IndexError, ValueError):
        return []

    if not results.get("ids") or not results["ids"][0]:
        return []

    hits = []
    for i in range(len(results["ids"][0])):
        metadata = results["metadatas"][0][i]
        hit = _chunk_to_hit(
            results["ids"][0][i],
            results["documents"][0][i],
            metadata,
            distance=results["distances"][0][i],
        )
        if is_retrievable(hit):
            hits.append(hit)
    return hits


def reciprocal_rank_fusion(
    result_lists: list[list[dict]],
    top_k: int = RETRIEVE_TOP_K,
    k: int = RRF_K,
) -> list[dict]:
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for results in result_lists:
        for rank, hit in enumerate(results, start=1):
            chunk_id = hit["chunk_id"]
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
            items[chunk_id] = hit

    ranked_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)
    merged = []
    for chunk_id in ranked_ids[:top_k]:
        hit = items[chunk_id]
        hit["rrf_score"] = scores[chunk_id]
        merged.append(hit)
    return merged


def retrieve(query: str, top_k: int = RETRIEVE_TOP_K) -> list[dict]:
    """Generic hybrid retrieval: dense + BM25, merged with RRF."""
    vector_hits = search_vector(query, top_k=RETRIEVE_CANDIDATES)
    keyword_hits = search_bm25(query, top_k=RETRIEVE_CANDIDATES)
    return reciprocal_rank_fusion([vector_hits, keyword_hits], top_k=top_k)


def retrieval_confidence(hits: list[dict]) -> bool:
    """Generic check: top hit must have a minimum fusion score."""
    return bool(hits) and hits[0].get("rrf_score", 0) >= MIN_RRF_SCORE
