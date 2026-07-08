import sys

from src.config import RETRIEVE_TOP_K
from src.rag.answer import format_context
from src.rag.retrieve import retrieve, retrieval_confidence

question = " ".join(sys.argv[1:])
hits = retrieve(question, top_k=RETRIEVE_TOP_K)

print("QUESTION:", question)
print("CONFIDENT?:", retrieval_confidence(hits))
print("=" * 70)

for i, h in enumerate(hits, 1):
    m = h["metadata"]
    print(f"\n--- Chunk {i} | rrf={h.get('rrf_score', 0):.4f} ---")
    print(f"doc_type={m.get('doc_type')} | pages {m['page_start']}-{m['page_end']}")
    print(f"section={m.get('section', 'N/A')}")
    print(h["text"][:400])

print("\n" + "=" * 70)
print("Context preview:\n")
print(format_context(hits)[:2500])
