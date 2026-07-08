import ollama

from src.config import CHAT_MODEL, RETRIEVE_TOP_K
from src.rag.retrieve import retrieve, retrieval_confidence

SYSTEM_PROMPT = """
You are a UGC Sri Lanka university admission assistant.

Rules:
- Answer ONLY using the provided context from the handbook.
- If the context does not contain enough information, say EXACTLY:
  "I don't have enough information in the handbook to answer this."
- Do NOT use knowledge outside the context. Do NOT guess or invent steps.
- Every answer MUST include at least one citation:
  (Section X.X, Handbook 2025/26, p.N)
  Use section and page numbers from the context headers.
- For yes/no questions, quote the relevant rule from the context first, then answer.
"""


def format_context(hits: list[dict]) -> str:
    blocks = []
    for i, hit in enumerate(hits, start=1):
        m = hit["metadata"]
        header = (
            f"[{i}] doc_type={m.get('doc_type', 'content')} | "
            f"Section: {m.get('section') or 'N/A'} | "
            f"Pages {m['page_start']}-{m['page_end']}"
        )
        blocks.append(f"{header}\n{hit['text']}")
    return "\n\n---\n\n".join(blocks)


def answer_question(question: str) -> str:
    hits = retrieve(question, top_k=RETRIEVE_TOP_K)

    if not retrieval_confidence(hits):
        return "I don't have enough information in the handbook to answer this."

    context = format_context(hits)

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
        options={"temperature": 0},
    )

    return response["message"]["content"]
