# UniPath LK — Data & Chunking Guide

> Summary of data sources, chunking pipeline, technologies, and retrieval strategies.

---

## 1. Two types of data

UniPath uses a **hybrid** design: structured facts in SQLite, policy text via RAG.

| Type | Source files | Storage | Chunked? | Used for |
|------|--------------|---------|----------|----------|
| **Structured** | `courses.json`, `cutoffs.json` | SQLite `unipath.db` | No | Z-scores, eligibility, course compare |
| **Handbook** | UGC PDF | JSONL + Chroma | Yes | Policies, SLIATE, Uni-Code, procedures |

**Design rule:** Numbers from SQLite only. Policy prose from handbook chunks only.

---

## 2. Structured data (no chunking)

### Sources

- **`courses.json`** — 101 course catalogue entries (name, intake, universities, eligibility)
- **`cutoffs.json`** — Z-score cutoffs by district, university, course code (2024/2025)

### Build

```bash
python scripts/build_db.py
```

Creates `data/structured/unipath.db` (gitignored).

### Agent access

SQLite tools: `get_eligible_courses`, `get_gap_analysis`, `compare_courses`, `find_course`

### Known gaps

- Cutoffs cover **21 course codes**, not all 101
- ~**15 incomplete** catalogue rows
- **Medicine** in cutoffs but missing from catalogue

---

## 3. Handbook data (chunked for RAG)

### Pipeline

```
PDF (docs/student_handbook_english_25:26.pdf)
  → parse_pdf.py          (PyMuPDF)
  → chunk.py              (token buffering)
  → step3_make_chunks.py  (JSONL output)
  → step5_build_index.py  (Chroma vectors)
  → retrieve.py           (search at query time)
```

### Output files

| File | In Git? | Description |
|------|---------|-------------|
| `data/processed/chunks_2025_26_en.jsonl` | Yes | ~336 chunks + metadata |
| `data/chroma/` | No | Vector index (rebuild locally) |

**Language:** English only (`language: "en"`).

---

## 4. Chunking strategy

### Type

**Token-based buffered accumulation** — not LLM semantic chunking.

### Parameters (`src/ingestion/chunk.py`)

| Setting | Value |
|---------|-------|
| Target size | **400 tokens** |
| Max size | **500 tokens** |
| Tokenizer | **tiktoken** `cl100k_base` |

### Steps

1. **PDF → pages** (`parse_pdf.py`)  
   One page per object; empty pages skipped.

2. **Page → units** (`page_to_units`)  
   - Split by `\n\n` (paragraph blocks)  
   - Small blocks (≤250 tokens): keep as units  
   - Large blocks: split **line by line** (lists/tables)  
   - Hard cap: `split_text_by_tokens()` at 500 tokens  

3. **Units → chunks** (`chunk_pages`)  
   - Accumulate units in a buffer  
   - Flush when buffer ≥ **400 tokens**  
   - Flush before exceeding **500 tokens**  
   - Chunks can span **multiple pages**  
   - No overlap between chunks  

4. **Metadata per chunk**
   - `chunk_id`, `text`, `academic_year`, `language`, `source_file`
   - `page_start`, `page_end`
   - `section` — regex (`1.7`, `SECTION 1`, etc.)
   - `doc_type` — heuristic classification
   - `token_count`

### Doc types

| `doc_type` | Content | Retrieved? |
|------------|---------|------------|
| `toc` | Table of contents | **No** (excluded) |
| `reference` | Abbreviations | Yes |
| `procedure` | Application steps | Yes |
| `table` | Course/university lists | Yes |
| `policy` | Numbered rules | Yes |
| `content` | General prose | Yes |

Exclusion config: `EXCLUDED_DOC_TYPES = {"toc"}` in `src/config.py`.

---

## 5. Technologies

| Stage | Technology | File |
|-------|------------|------|
| PDF parsing | **PyMuPDF** (`fitz`) | `parse_pdf.py` |
| Token counting | **tiktoken** | `chunk.py` |
| Chunk storage | **JSONL** | `step3_make_chunks.py` |
| Embeddings | **Ollama** `nomic-embed-text` | `index.py`, `retrieve.py` |
| Vector DB | **ChromaDB** | `index.py`, `retrieve.py` |
| Keyword search | **BM25** (`rank-bm25`) | `bm25_index.py` |
| Rank fusion | **RRF** (custom) | `retrieve.py` |

**Planned:** OpenAI `text-embedding-3-small` for cloud deploy (no Ollama).

---

## 6. Indexing (after chunking)

### Vector index

- Each chunk embedded via Ollama
- Chunks >512 embed tokens: split, embed parts, average vectors
- Stored in Chroma collection `ugc_handbook_en_2526`

### BM25 index

- Built in memory from JSONL at first search
- Custom tokenizer: `A/L` → `al examination` for domain terms
- Skips `toc` chunks

---

## 7. Retrieval strategy (hybrid search)

Entry point: `retrieve()` in `src/rag/retrieve.py`:

```python
def retrieve(query: str, top_k: int = RETRIEVE_TOP_K) -> list[dict]:
    vector_hits = search_vector(query, top_k=RETRIEVE_CANDIDATES)
    keyword_hits = search_bm25(query, top_k=RETRIEVE_CANDIDATES)
    return reciprocal_rank_fusion([vector_hits, keyword_hits], top_k=top_k)
```

Two search methods run on the same query, then rankings are merged.

```
Query
  ├── Vector search (Chroma)     → top 20
  ├── BM25 search (keywords)     → top 20
  └── RRF merge                  → top 5 final chunks
```

| Config | Value | Meaning |
|--------|-------|---------|
| `RETRIEVE_CANDIDATES` | 20 | Candidates per method before merge |
| `RETRIEVE_TOP_K` | 5 | Final chunks passed to the agent |
| `RRF_K` | 60 | RRF smoothing constant |
| `MIN_RRF_SCORE` | 0.015 | Minimum confidence for top hit |

---

### 7.1 Vector search (Chroma) → top 20

**Idea:** Find chunks **similar in meaning**, even when words differ.

**Steps** (`search_vector` in `retrieve.py`):

1. Embed the query with Ollama `nomic-embed-text` → vector (list of floats)
2. Chroma compares query vector to all stored chunk vectors
3. Return the **20 nearest** chunks
4. Filter out `toc` chunks via `is_retrievable()`

**Good at:**
- Paraphrases (*“maximum A/L attempts”* ↔ *“three occasions”*)
- Conceptual questions when exact keywords are missing

**Weak at:**
- Rare exact terms (**SLIATE**, **Uni-Code**) if embeddings miss them
- Very short queries

Each hit includes a `distance` score (lower = more similar).

---

### 7.2 BM25 search (keywords) → top 20

**Idea:** Classic **keyword** search — score chunks by word overlap with the query.

**Steps** (`search_bm25` in `bm25_index.py`):

1. Load chunks from JSONL (skip `toc`)
2. Tokenize query and corpus (lowercase, strip punctuation)
3. Domain fix: `A/L` → `al examination` in tokenizer
4. BM25 scores every chunk; return **top 20**

**Good at:**
- Exact/rare words: **SLIATE**, **Uni-Code**, **60 days**
- Policy numbers and named entities

**Weak at:**
- Rephrased questions with different wording
- Semantic similarity without shared words

Each hit includes a `bm25_score`.

---

### 7.3 Why use both?

| Query type | Vector | BM25 |
|------------|--------|------|
| “SLIATE registration apply” | Maybe OK | **Strong** (word match) |
| “How many times can I sit A/L?” | **Strong** (meaning) | OK if “three occasions” in chunk |
| “Change preference order” | **Strong** | OK if “Uni-Code” in chunk |

One method alone can miss good chunks; hybrid covers both failure modes.

---

### 7.4 RRF merge → top 5 final chunks

**RRF** = **Reciprocal Rank Fusion**. Merges **rankings**, not raw scores.

**Formula** (`reciprocal_rank_fusion` in `retrieve.py`):

```
For each chunk, across each result list:
  RRF_score += 1 / (k + rank)
```

- `k = 60` (`RRF_K`) — dampens how much rank #1 dominates vs #20
- `rank` = 1 for best match, 2 for second, etc.

**Example** (query: *“SLIATE apply university”*):

| Chunk | Vector rank | BM25 rank | Effect |
|-------|-------------|-----------|--------|
| A (Section 1.7 SLIATE) | 3 | **1** | High — strong in both lists |
| B (general policy) | **1** | 15 | Medium — vector only |
| C (unrelated) | 8 | 20 | Low |

Chunks that rank well in **both** lists get the highest fused score. Sort by total RRF → take **top 5**. Each final hit gets an `rrf_score`.

---

### 7.5 Confidence check

```python
def retrieval_confidence(hits: list[dict]) -> bool:
    return bool(hits) and hits[0].get("rrf_score", 0) >= MIN_RRF_SCORE
```

If the top chunk’s RRF score is below **0.015**, retrieval is **low confidence** — the agent may say it lacks enough handbook information (`tools_rag.py` reports HIGH/LOW to the LLM).

---

### 7.6 End-to-end example

```
User: "Can I apply if I registered at SLIATE?"
         │
         ▼
Vector search → top 20 (semantic: ineligibility, registration rules)
         │
         ▼
BM25 search   → top 20 (keywords: "sliate", "apply", "60")
         │
         ▼
RRF merge     → top 5 chunks with rrf_score
         │
         ▼
Agent reads passages + writes answer with section citation
```

**Code path:** `search_handbook` tool → `retrieve()` → `format_context()` → LangGraph LLM

---

## 8. How agent uses data

There is no hardcoded router in Python. The **LLM in LangGraph ReAct** picks tools from the system prompt and tool docstrings. See [LLM_AND_AGENT.md](LLM_AND_AGENT.md) for the full decision flow.

```
User question
    │
    ├── Greeting / small talk?
    │     → No tools — direct reply
    │
    ├── Course / Z-score / cutoff / compare?
    │     → Structured tools → SQLite (no chunk search)
    │
    └── Policy / procedure / handbook?
          ├── search_handbook(query)  → retrieve() — vector + BM25 + RRF
          └── lookup_section("1.7") → JSONL scan by section (no hybrid search)
```

| Tool | Data touched | Chunk search |
|------|--------------|--------------|
| `get_eligible_courses`, `get_gap_analysis`, `compare_courses`, `find_course` | `unipath.db` | No |
| `search_handbook` | Chroma + BM25 + chunks JSONL | **Yes** — hybrid top-K |
| `lookup_section` | chunks JSONL only | Section match only |

Low-confidence retrieval (`rrf_score` below threshold) is reported to the LLM as `Retrieval confidence: LOW` in the tool output; the agent should not invent handbook text.

---

## 9. Commands cheat sheet

```bash
# Structured DB
python scripts/build_db.py

# Chunks (if rebuilding from PDF)
python scripts/step3_make_chunks.py

# Vector index
python scripts/step5_build_index.py

# Requires: ollama serve + nomic-embed-text
```

---

## 10. One-line summary

**Handbook PDF → 400-token chunks with section/doc_type metadata → Chroma (semantic) + BM25 (keywords) → RRF merge → top 5 chunks; courses/cutoffs stay in SQLite with no chunking.**

---

*See also:* [PROJECT_GUIDE.md](PROJECT_GUIDE.md) for full architecture and workflows.
