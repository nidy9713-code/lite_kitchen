import docx
import shutil
import os

def inspect_constructors():
    src = r"c:\Users\nidy9\OneDrive\Документы\Конструкторы.docx"
    dst = "temp_constructors.docx"
    shutil.copy2(src, dst)
    
    doc = docx.Document(dst)
    for i, para in enumerate(doc.paragraphs):
        if para.text.strip():
            print(f"{i}: {para.text}")
    
    os.remove(dst)

if __name__ == "__main__":
    inspect_constructors()
