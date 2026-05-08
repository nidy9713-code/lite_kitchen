import docx
import fitz # PyMuPDF
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def inspect_files():
    files = [
        r"c:\Users\nidy9\OneDrive\Документы\контуктор рецептов.docx",
        r"c:\Users\nidy9\OneDrive\Документы\Топ 10 десертов.pdf",
        r"c:\Users\nidy9\OneDrive\Документы\Рецепты_для_улучшения_настроения_pptx_1.pdf",
        r"c:\Users\nidy9\OneDrive\Документы\НАИС_Сборник рецептов.pptx.pdf"
    ]
    
    for f in files:
        print(f"\n--- FILE: {os.path.basename(f)} ---")
        if not os.path.exists(f):
            print("NOT FOUND")
            continue
            
        if f.endswith(".docx"):
            doc = docx.Document(f)
            # Print first 20 paragraphs to see structure
            for i, p in enumerate(doc.paragraphs[:20]):
                print(f"P{i}: {p.text[:100]}")
        elif f.endswith(".pdf"):
            doc = fitz.open(f)
            # Print first page text
            if len(doc) > 0:
                print(doc[0].get_text()[:500])
            doc.close()

if __name__ == "__main__":
    inspect_files()
