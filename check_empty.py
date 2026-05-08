import sqlite3
import sys

def check_remaining_empty():
    conn = sqlite3.connect("recipes.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, category FROM recipes WHERE ingredients = '' OR steps = ''")
    rows = cursor.fetchall()
    print(f"Remaining recipes with empty ingredients or steps: {len(rows)}")
    for row in rows:
        print(f"ID: {row['id']} | Title: {row['title']} | Cat: {row['category']}")
        
    conn.close()

if __name__ == "__main__":
    check_remaining_empty()
