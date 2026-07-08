from src.config import RETRIEVE_TOP_K
from src.rag.retrieve import retrieve

QUESTIONS = [
    "What is the maximum number of A/L attempts allowed for university admission?",
    "Can I apply if I registered at SLIATE?",
    "How do I change my Uni-Code preference order?",
]

for question in QUESTIONS:
    print("\n" + "=" * 70)
    print("Question:", question)
    hits = retrieve(question, top_k=RETRIEVE_TOP_K)

    for i, hit in enumerate(hits, start=1):
        m = hit["metadata"]
        print(f"\nResult {i} | RRF={hit.get('rrf_score', 0):.4f}")
        print(f"doc_type={m.get('doc_type')} | pages {m['page_start']}-{m['page_end']}")
        print(f"Section: {m.get('section', 'N/A')}")
        print("Preview:", hit["text"][:250].replace("\n", " "))
