import json
from pathlib import Path

import chromadb
import ollama
import tiktoken

from src.config import COLLECTION_NAME, EMBED_MODEL

enc = tiktoken.get_encoding("cl100k_base")
MAX_EMBED_TOKENS = 512


def embed_one(text: str) -> list[float]:
    tokens = enc.encode(text)

    if len(tokens) <= MAX_EMBED_TOKENS:
        return ollama.embeddings(model=EMBED_MODEL, prompt=text)["embedding"]

    vectors = []
    for i in range(0, len(tokens), MAX_EMBED_TOKENS):
        part_tokens = tokens[i : i + MAX_EMBED_TOKENS]
        part_text = enc.decode(part_tokens)
        vectors.append(
            ollama.embeddings(model=EMBED_MODEL, prompt=part_text)["embedding"]
        )

    dim = len(vectors[0])
    return [sum(v[j] for v in vectors) / len(vectors) for j in range(dim)]


def embed_texts(texts: list[str]) -> list[list[float]]:
    vectors = []
    for i, text in enumerate(texts, start=1):
        vectors.append(embed_one(text))
        if i % 20 == 0 or i == len(texts):
            print(f"  Embedded {i}/{len(texts)}")
    return vectors


def build_index(chunks_path: Path, chroma_path: Path = Path("data/chroma")) -> None:
    chunks = [
        json.loads(line)
        for line in chunks_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    print(f"Loading {len(chunks)} chunks from {chunks_path}")
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    db = chromadb.PersistentClient(path=str(chroma_path))

    try:
        db.delete_collection(COLLECTION_NAME)
        print("Deleted old collection")
    except Exception:
        pass

    collection = db.create_collection(name=COLLECTION_NAME)

    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[
            {
                "academic_year": c["academic_year"],
                "language": c["language"],
                "source_file": c["source_file"],
                "page_start": c["page_start"],
                "page_end": c["page_end"],
                "section": c.get("section") or "",
                "doc_type": c.get("doc_type", "content"),
            }
            for c in chunks
        ],
    )

    print(f"Indexed {len(chunks)} chunks into '{COLLECTION_NAME}'")
    print(f"Chroma DB saved at: {chroma_path}")
