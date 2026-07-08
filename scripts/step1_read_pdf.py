import fitz
from pathlib import Path

PDF_PATH = Path("docs/student_handbook_english_25:26.pdf")
doc = fitz.open(PDF_PATH)

print("Total pages:", doc.page_count)
print("=" * 60)

# Try a few pages — cover vs content vs policy
for page_number in [1, 2, 3, 13]:
    page = doc[page_number - 1]
    text = page.get_text("text").strip()

    print(f"\n--- PDF page {page_number} ({len(text)} characters) ---")
    print(text[:600] if text else "(empty)")

doc.close()