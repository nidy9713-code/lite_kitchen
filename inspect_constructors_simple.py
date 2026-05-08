import docx
import os
import sys

def inspect_constructors():
    sys.stdout.reconfigure(encoding='utf-8')
    src = "constructors_local.docx"
    
    try:
        doc = docx.Document(src)
        for i, para in enumerate(doc.paragraphs):
            if para.text.strip():
                print(f"{i}: {para.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_constructors()
