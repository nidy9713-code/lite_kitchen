import sqlite3
import sys

def cleanup_more():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    
    # Let's search for keywords to find titles that might contain the text you mentioned
    keywords = ["профилактирует", "запоры", "Свекла", "Витамины", "зрение"]
    
    for k in keywords:
        cursor.execute("SELECT id, title FROM recipes WHERE title LIKE ?", (f"%{k}%",))
        rows = cursor.fetchall()
        for row in rows:
            # If title is long and looks like a description, delete it
            if len(row[1]) > 50:
                print(f"Deleting likely garbage id {row[0]}: {row[1]}")
                cursor.execute("DELETE FROM recipes WHERE id = ?", (row[0],))
            elif k in ["профилактирует", "Свекла", "Витамины"] and row[1].startswith(k):
                print(f"Deleting specific garbage id {row[0]}: {row[1]}")
                cursor.execute("DELETE FROM recipes WHERE id = ?", (row[0],))
                
    conn.commit()
    conn.close()

if __name__ == "__main__":
    cleanup_more()
