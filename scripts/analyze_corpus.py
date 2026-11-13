import os
import json
import pypdf

PDF_PATH = "data/raw/20260319_VNM_Bao_cao_thuong_nien_2025_eae619d5f6.pdf"

def analyze_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    reader = pypdf.PdfReader(pdf_path)
    total_physical_pages = len(reader.pages)
    
    page_stats = []
    useful_pages = []
    
    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        text = page.extract_text() or ""
        char_count = len(text.strip())
        
        # Heuristic for useful content: page with at least 150 characters
        # (pages with very few characters are usually cover, blank, or divider pages)
        is_useful = char_count >= 150
        
        status = "useful" if is_useful else "empty_or_cover"
        if is_useful:
            useful_pages.append(page_num)
            
        page_stats.append({
            "page_num": page_num,
            "char_count": char_count,
            "status": status,
            "first_few_chars": text.strip()[:60].replace("\n", " ") if text else ""
        })

    print(f"Total physical pages: {total_physical_pages}")
    print(f"Total useful pages (>= 150 chars): {len(useful_pages)}")
    print(f"Pages excluded (< 150 chars): {total_physical_pages - len(useful_pages)}")
    
    # Save statistics
    os.makedirs("data", exist_ok=True)
    with open("data/page_analysis.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_physical_pages": total_physical_pages,
            "useful_page_count": len(useful_pages),
            "useful_pages": useful_pages,
            "page_details": page_stats
        }, f, ensure_ascii=False, indent=2)
    print("Page analysis saved to data/page_analysis.json")

if __name__ == "__main__":
    analyze_pdf(PDF_PATH)
