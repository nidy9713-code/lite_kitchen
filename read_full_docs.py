import fitz
import docx
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def read_full_docs():
    files = [
        r"c:\Users\nidy9\OneDrive\Документы\контуктор рецептов.docx",
        r"c:\Users\nidy9\OneDrive\Документы\Топ 10 десертов.pdf",
        r"c:\Users\nidy9\OneDrive\Документы\Рецепты_для_улучшения_настроения_pptx_1.pdf",
        r"c:\Users\nidy9\OneDrive\Документы\НАИС_Сборник рецептов.pptx.pdf"
    ]
    
    for f in files:
        print(f"\n===== {os.path.basename(f)} =====")
        if not os.path.exists(f): continue
        
        if f.endswith(".docx"):
            doc = docx.Document(f)
            for p in doc.paragraphs:
                if p.text.strip():
                    print(p.text[:200])
        else:
            doc = fitz.open(f)
            for page in doc:
                text = page.get_text()
                # Print titles or first lines of pages
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                if lines:
                    print(f"Page {page.number}: {lines[0]} ... {lines[1] if len(lines)>1 else ''}")
            doc.close()

if __name__ == "__main__":
    read_full_docs()
