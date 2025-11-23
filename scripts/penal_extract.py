import fitz  # PyMuPDF
import json
import re
from pathlib import Path
from time import time
from datetime import datetime

def parse_sections_from_text(text, page_num):
    sections = []
    # Regex: Section \d+\.?\s*(Title)?\s*\n?(content until next Section)
    pattern = r'(Section\s+(\d+)(?:\.\s*(.*?))?\s*\n?)(.*?)(?=\nSection\s+\d+|CHAPTER|\Z)'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    for match in matches:
        sec_num = match[1]
        title = match[2].strip() if match[2] else f"Section {sec_num}"
        description = match[3].strip()
        if len(description) > 50:  # Valid section
            summary = description[:300] + "..." if len(description) > 300 else description
            sections.append({
                "section": sec_num,
                "page": page_num,
                "title": title,
                "description": description,
                "summary": summary,
                "lang": "en"
            })
    return sections

# Main
pdf_path = r"E:\SLIIT\Research\Smart-Criminal-Judgement-Analysis-System\pdfs\Penal-Code-Consolidated2024.pdf"
start_time = time()

doc = fitz.open(pdf_path)
total_pages = len(doc)
all_sections = []

print(f"Starting Penal Code extraction: {total_pages} pages")
for page_num in range(total_pages):
    page = doc.load_page(page_num)
    text = page.get_text("text").strip()
    new_sections = parse_sections_from_text(text, page_num + 1)
    all_sections.extend(new_sections)
    print(f"Processing page {page_num + 1}/{total_pages}: Found {len(new_sections)} new sections so far (total: {len(all_sections)})")
    
    if (page_num + 1) % 50 == 0:  # Progress milestone
        print(f"--- Milestone: {page_num + 1} pages done, {len(all_sections)} sections ---")

doc.close()

# Save
output_dir = Path("./data/structured")
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "penal_code_sections.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_sections, f, ensure_ascii=False, indent=2)

elapsed = time() - start_time
print(f"\n✅ Penal Code complete! Total sections: {len(all_sections)} | Time: {elapsed:.1f}s | Saved: {output_file}")
print(f"Generated on: {datetime.now().isoformat()}")