import fitz
from pathlib import Path
from dataclasses import dataclass

@dataclass
class PageText:
    page_number: int   # 1, 2, 3 ... 210
    text: str

def parse_pdf(pdf_path: Path) -> list[PageText]:
    doc = fitz.open(pdf_path)
    pages = []

    for i in range(doc.page_count):
        text = doc[i].get_text("text").strip()
        if text:  # skip completely empty pages
            pages.append(PageText(page_number=i + 1, text=text))

    doc.close()
    return pages