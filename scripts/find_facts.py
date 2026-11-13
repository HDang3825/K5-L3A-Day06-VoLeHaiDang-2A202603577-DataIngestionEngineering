import sys
import os
sys.path.insert(0, os.path.abspath("."))
import re
from src.ingestion import load_pdf

def search_facts():
    pages, _ = load_pdf('data/raw/20260319_VNM_Bao_cao_thuong_nien_2025_eae619d5f6.pdf')
    page_dict = {p.page: p for p in pages}
    
    # Let's inspect some key pages
    targets = [4, 5, 8, 12, 18, 28, 35, 45, 55, 62, 70, 78, 88, 92, 102, 103, 104, 107, 108, 110]
    for p_num in targets:
        if p_num in page_dict:
            p = page_dict[p_num]
            print(f"=== Page {p_num} (Section: {p.metadata.get('section')}) ===")
            lines = [l.strip() for l in p.text.split('\n') if len(l.strip()) > 20]
            for l in lines[:5]:
                print(f"  * {l[:100]}")

if __name__ == "__main__":
    search_facts()
