from pathlib import Path
from src.ingestion.parse_pdf import parse_pdf

pdf = Path("docs/student_handbook_english_25:26.pdf")
pages = parse_pdf(pdf)

print("Parsed pages:", len(pages))
print("First page number:", pages[0].page_number)
print("Last page number:", pages[-1].page_number)
print("-" * 60)

# Show page 2 (intro text)
print("\nPage 2 preview:")
print(pages[1].text[:300])

print("-" * 60)

# Search for Section 1.7 (ineligibility) across ALL pages
print("\nSearching for 'Ineligibility'...")
for page in pages:
    if "Ineligibility" in page.text or "three (03) occasions" in page.text:
        print(f"Found on PDF page {page.page_number}")
        print(page.text[:500])
        break