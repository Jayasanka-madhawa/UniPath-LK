import re
import uuid

import tiktoken

from src.ingestion.parse_pdf import PageText

enc = tiktoken.get_encoding("cl100k_base")

TARGET_TOKENS = 400
MAX_TOKENS = 500


def count_tokens(text: str) -> int:
    return len(enc.encode(text))


def detect_section(text: str) -> str | None:
    matches = re.findall(
        r"(?:SECTION\s+\d+|^\d+\.\d+(?:\.\d+)*)[^\n]{0,80}",
        text,
        flags=re.MULTILINE,
    )
    if not matches:
        return None
    section = matches[-1].strip()
    return section[:120]


def detect_doc_type(text: str, page_start: int) -> str:
    upper = text.upper()

    if page_start <= 6 and ("CONTENTS" in upper or ("TITLE" in upper and "PAGE" in upper)):
        return "toc"

    if "ABBREVIATIONS" in upper and page_start <= 15:
        return "reference"

    if re.search(r"STEP \d", upper) or "FILL THE APPLICATION" in upper:
        return "procedure"

    if page_start >= 118 and ("STEP " in upper or "ONLINE APPLICATION" in upper):
        return "procedure"

    numbered_lines = sum(
        1 for line in text.splitlines() if re.match(r"^\s*\d+\.", line.strip())
    )
    if numbered_lines >= 12:
        return "table"

    if re.search(r"SECTION \d", upper) or re.search(r"^\s*\d+\.\d+", text, re.MULTILINE):
        return "policy"

    return "content"


def split_text_by_tokens(text: str, max_tokens: int) -> list[str]:
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return [text]

    parts = []
    for i in range(0, len(tokens), max_tokens):
        parts.append(enc.decode(tokens[i : i + max_tokens]))
    return parts


def page_to_units(page_text: str) -> list[str]:
    units: list[str] = []

    for block in page_text.split("\n\n"):
        block = block.strip()
        if not block:
            continue

        if count_tokens(block) <= MAX_TOKENS // 2:
            units.extend(split_text_by_tokens(block, MAX_TOKENS))
            continue

        for line in block.split("\n"):
            line = line.strip()
            if line:
                units.extend(split_text_by_tokens(line, MAX_TOKENS))

    return units


def chunk_pages(
    pages: list[PageText],
    academic_year: str,
    language: str,
    source_file: str,
    target_tokens: int = TARGET_TOKENS,
    max_tokens: int = MAX_TOKENS,
) -> list[dict]:
    chunks: list[dict] = []
    buffer: list[str] = []
    buffer_pages: list[int] = []

    def flush() -> None:
        nonlocal buffer, buffer_pages
        if not buffer:
            return

        text = "\n".join(buffer).strip()
        page_start = min(buffer_pages)
        chunks.append(
            {
                "chunk_id": str(uuid.uuid4()),
                "text": text,
                "academic_year": academic_year,
                "language": language,
                "source_file": source_file,
                "page_start": page_start,
                "page_end": max(buffer_pages),
                "section": detect_section(text),
                "doc_type": detect_doc_type(text, page_start),
                "token_count": count_tokens(text),
            }
        )
        buffer.clear()
        buffer_pages.clear()

    for page in pages:
        for unit in page_to_units(page.text):
            candidate = "\n".join(buffer + [unit])
            if buffer and count_tokens(candidate) > max_tokens:
                flush()

            buffer.append(unit)
            buffer_pages.append(page.page_number)

            if count_tokens("\n".join(buffer)) >= target_tokens:
                flush()

    flush()
    return chunks
