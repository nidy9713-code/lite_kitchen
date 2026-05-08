import sqlite3
import re

def final_polish():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    # 1. Delete garbage titles that are just time or instructions
    cursor.execute("DELETE FROM recipes WHERE title LIKE '%минут%' OR title LIKE '%минуты%' OR title LIKE '%часов%'")
    print(f"Deleted {cursor.rowcount} recipes with time-only titles.")
    
    # 2. Delete empty recipes
    cursor.execute("DELETE FROM recipes WHERE ingredients = '' OR steps = ''")
    print(f"Deleted {cursor.rowcount} empty recipes.")
    
    # 3. Fix titles that might have "Название:" prefix if parser missed it
    cursor.execute("SELECT id, title FROM recipes WHERE title LIKE 'Название:%'")
    rows = cursor.fetchall()
    for rid, title in rows:
        new_title = title[9:].strip().capitalize()
        cursor.execute("UPDATE recipes SET title = ? WHERE id = ?", (new_title, rid))
    print(f"Fixed {len(rows)} titles with prefix.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    final_polish()
