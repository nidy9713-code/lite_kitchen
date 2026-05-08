import sqlite3
import sys

def list_all_by_cat():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT category, id, title FROM recipes ORDER BY category")
    rows = cursor.fetchall()
    
    current_cat = None
    for row in rows:
        cat, r_id, title = row
        if cat != current_cat:
            print(f"\n=== CATEGORY: {cat} ===")
            current_cat = cat
        print(f"  ID {r_id}: {title}")
        
    conn.close()

if __name__ == "__main__":
    list_all_by_cat()
