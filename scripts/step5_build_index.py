from pathlib import Path
from src.ingestion.index import build_index

chunks_path = Path("data/processed/chunks_2025_26_en.jsonl")

if not chunks_path.exists():
    raise FileNotFoundError("Run step3_make_chunks.py first")

build_index(chunks_path)