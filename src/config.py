from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3.2"
COLLECTION_NAME = "ugc_handbook_en_2526"
CHROMA_PATH = str(PROJECT_ROOT / "data/chroma")
CHUNKS_PATH = str(PROJECT_ROOT / "data/processed/chunks_2025_26_en.jsonl")
DB_PATH = PROJECT_ROOT / "data/structured/unipath.db"

# Retrieval
RETRIEVE_TOP_K = 5
RETRIEVE_CANDIDATES = 20
RRF_K = 60
MIN_RRF_SCORE = 0.015

# Doc types excluded from retrieval (noise for Q&A)
EXCLUDED_DOC_TYPES = {"toc"}
