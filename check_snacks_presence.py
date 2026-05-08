import sqlite3
import json
import sys

def check_snacks():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    titles = [
        "Брускетта из киноа и авокадо",
        "Ролл с индейкой",
        "Тост с хумусом",
        "Хумус"
    ]
    
    print("=== Checking Category: Брускеты и закуски ===")
    cursor.execute("SELECT COUNT(*) FROM recipes WHERE category = 'Брускеты и закуски'")
    count = cursor.fetchone()[0]
    print(f"Total recipes in category: {count}")
    
    for title in titles:
        print(f"\n--- Checking: {title} ---")
        cursor.execute("SELECT * FROM recipes WHERE title LIKE ?", (f"%{title}%",))
        rows = cursor.fetchall()
        if rows:
            cursor.execute("PRAGMA table_info(recipes)")
            cols = [c[1] for c in cursor.fetchall()]
            for row in rows:
                recipe_dict = dict(zip(cols, row))
                print(f"FOUND ID {recipe_dict['id']}: {recipe_dict['title']} (Category: {recipe_dict['category']})")
        else:
            print("NOT FOUND")
    
    conn.close()

if __name__ == "__main__":
    check_snacks()
