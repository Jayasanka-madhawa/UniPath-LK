import json
import re
from pathlib import Path

from src.config import CHUNKS_PATH, EXCLUDED_DOC_TYPES, RETRIEVE_TOP_K
from src.rag.answer import format_context
from src.rag.retrieve import retrieve, retrieval_confidence

_chunks: list[dict] | None = None


def _load_chunks() -> list[dict]:
    global _chunks
    if _chunks is None:
        _chunks = [
            __import__("json").loads(line)
            for line in Path(CHUNKS_PATH).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    return _chunks


def search_handbook_tool(query: str) -> str:
    query = (query or "").strip()
    if not query:
        return "No search query provided."
    try:
        hits = retrieve(query, top_k=RETRIEVE_TOP_K)
    except Exception as exc:
        return f"Handbook search failed: {exc}"
    if not hits:
        return "No matching handbook passages found."

    confidence = retrieval_confidence(hits)
    header = "Retrieval confidence: HIGH" if confidence else "Retrieval confidence: LOW"
    return f"{header}\n\n{format_context(hits)}"


def lookup_section_tool(section_id: str) -> str:
    section_id = section_id.strip()
    if not section_id:
        return "Error: section_id required, e.g. '1.7'"

    pattern = re.compile(rf"(?<!\d){re.escape(section_id)}(?!\d)")
    matches = []

    for chunk in _load_chunks():
        if chunk.get("doc_type", "content") in EXCLUDED_DOC_TYPES:
            continue

        section = chunk.get("section") or ""
        if section.strip().startswith(section_id) or pattern.search(section):
            matches.append(chunk)
        elif chunk.get("doc_type") == "policy" and pattern.search(chunk["text"][:400]):
            matches.append(chunk)

    if not matches:
        return f"No handbook content found for section {section_id}."

    matches.sort(key=lambda c: (c["page_start"], c["page_end"]))
    blocks = []
    for chunk in matches[:5]:
        blocks.append(
            f"Section: {chunk.get('section') or 'N/A'} | "
            f"pp. {chunk['page_start']}-{chunk['page_end']}\n{chunk['text']}"
        )
    return "\n\n---\n\n".join(blocks)