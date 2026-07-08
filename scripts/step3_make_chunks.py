import json
from collections import Counter
from pathlib import Path

from src.ingestion.chunk import chunk_pages
from src.ingestion.parse_pdf import parse_pdf

pdf = Path("docs/student_handbook_english_25:26.pdf")
pages = parse_pdf(pdf)

chunks = chunk_pages(
    pages=pages,
    academic_year="2025/26",
    language="en",
    source_file=pdf.name,
)

out = Path("data/processed/chunks_2025_26_en.jsonl")
out.parent.mkdir(parents=True, exist_ok=True)

with out.open("w", encoding="utf-8") as f:
    for chunk in chunks:
        f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print("Total chunks:", len(chunks))
print("Saved to:", out)
print("-" * 60)

token_counts = [c["token_count"] for c in chunks]
print("Avg tokens per chunk:", round(sum(token_counts) / len(token_counts)))
print("Min tokens:", min(token_counts))
print("Max tokens:", max(token_counts))
print("-" * 60)

print("Chunks by doc_type:")
for doc_type, count in Counter(c["doc_type"] for c in chunks).most_common():
    print(f"  {doc_type}: {count}")

print("-" * 60)
print("\nSample policy chunk with A/L rule:")
for c in chunks:
    if "three (03) occasions" in c["text"]:
        print(f"  pages {c['page_start']}-{c['page_end']} | doc_type={c['doc_type']}")
        print(f"  tokens={c['token_count']} | section={c.get('section')}")
        print(c["text"][:400])
        break
