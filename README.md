# UniPath LK

Hybrid agentic assistant for **UGC Sri Lanka university admission** — structured SQLite for courses and cutoffs, plus RAG over the official 2025/26 Student Handbook.

> **Disclaimer:** Educational portfolio project only. Not official UGC advice. Always verify with [UGC Sri Lanka](https://www.ugc.ac.lk/).

**Documentation:**
- [Project guide](documentation/PROJECT_GUIDE.md) — architecture, workflows, diagrams
- [LLM & agent](documentation/LLM_AND_AGENT.md) — LangGraph, tool decisions, when chunk search runs
- [Data & chunking](documentation/DATA_AND_CHUNKING.md) — sources, chunking strategy, RAG tech

## Features

- **Structured data:** 101 courses, 2025 cutoff rows (21 course codes, 25 districts, 2024/2025 academic year)
- **Eligibility & gap analysis** from SQLite cutoffs
- **Policy Q&A** via hybrid RAG (Chroma + BM25 + RRF)
- **Agent** with LangGraph ReAct (falls back to legacy Ollama JSON loop if LangGraph unavailable)
- **Streamlit chat UI** — conversational agent (auto-routes tools + handbook search)
- **Eval harness** for policy (RAG) and structured (SQLite) checks

## Architecture

```
User question
    │
    ▼
Streamlit / CLI
    │
    ├── Agent ──► LangGraph ReAct + conversation history
    │                 (Ollama, OpenAI, or Google Gemini — switchable)
    │                      ├── SQLite tools: compare, find, eligible, gap
    │                      └── RAG tools: search_handbook, lookup_section
    │
    └── (RAG pipeline used internally via agent handbook tools)

**Note:** The Streamlit app is a single chat interface — no mode selection. The LLM decides when to call tools; handbook chunk search runs only when the agent calls `search_handbook` or `lookup_section`. See [LLM & agent](documentation/LLM_AND_AGENT.md).
```

**Design rule:** Z-scores and cutoffs come from SQLite only; policy prose from the handbook via RAG. The agent must not invent numbers.

## Prerequisites

- Python 3.12+
- **Local (Ollama):** [Ollama](https://ollama.com/) with `llama3.2` and `nomic-embed-text`
- **Google Gemini (optional):** API key — free tier has limits
- **OpenAI (optional):** API key — pay-as-you-go, good for Sinhala
- Chroma index built (see Setup)

## LLM providers

| Provider | Best for | Requires |
|----------|----------|----------|
| **ollama** (default) | Free, local, offline | `ollama serve` |
| **openai** | Sinhala, strong tool routing | `OPENAI_API_KEY` |
| **google** | Cloud alternative | `GOOGLE_API_KEY` |

Configure via `.env` (copy from `.env.example`):

```bash
cp .env.example .env
```

```env
LLM_PROVIDER=openai          # ollama | openai | google
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
GOOGLE_API_KEY=...
GOOGLE_MODEL=gemini-2.0-flash
```

In Streamlit, use the sidebar **AI model** dropdown to switch without restarting.

CLI / eval use `LLM_PROVIDER` from `.env`:

```bash
LLM_PROVIDER=openai python scripts/step8_agent_ask.py "Compare Physical Science vs Computer Science"
```

## Setup

```bash
conda create -n ugc-agent python=3.12 -y
conda activate ugc-agent
cd ugc-agent
pip install -r requirements.txt
export PYTHONPATH=.

# Build SQLite from structured JSON
python scripts/build_db.py

# Build vector index (if not already present)
python scripts/step5_build_index.py
```

## Run

```bash
# Streamlit chat UI
streamlit run app.py

# Agent CLI
python scripts/step8_agent_ask.py "My Z-score is 2.04 in Colombo. What courses can I get?"

# Course comparison
python scripts/compare_courses.py "Physical Science" "Computer Science"

# Evaluation
python scripts/run_eval.py
```

## Project layout

```
├── documentation/
│   ├── PROJECT_GUIDE.md        # Architecture, workflows, diagrams
│   ├── LLM_AND_AGENT.md        # LLM, LangGraph, tool routing
│   └── DATA_AND_CHUNKING.md    # Data sources, chunking, RAG
├── app.py                      # Streamlit UI
├── data/structured/
│   ├── courses.json            # Course catalogue
│   ├── cutoffs.json            # Z-score cutoffs
│   └── unipath.db              # Built SQLite (gitignored)
├── eval/
│   ├── golden_qa_policy.json   # RAG keyword checks
│   └── golden_qa_structured.json
├── scripts/
│   ├── build_db.py
│   ├── run_eval.py
│   └── step8_agent_ask.py
└── src/
    ├── agent/                  # LangGraph + legacy agent
    ├── db/                     # Schema and queries
    ├── ingestion/              # PDF parsing and chunking
    └── rag/                    # Retrieval and answering
```

## Limitations

- Cutoffs cover **21 major course codes**, not all 101 catalogue entries
- Cutoff academic year is **2024/2025** (embedded in the 2025/26 handbook)
- ~15 catalogue entries have incomplete metadata (Arts, Engineering, etc.)
- Requires local Ollama; answers depend on model quality
- Not connected to live UGC systems

## License

MIT — see repository for details.
