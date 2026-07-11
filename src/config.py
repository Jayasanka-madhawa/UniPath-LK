from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env from project root when present (optional; GOOGLE_API_KEY etc.)
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3.2"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
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
