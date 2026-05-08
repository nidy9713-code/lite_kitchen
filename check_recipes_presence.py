import sqlite3
import json
import sys

def check_recipes():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    titles = [
        "Фаршированный перец с чечевицей",
        "Овощная запеканка",
        "Пицца из цветной капусты",
        "Пицца из цветной капусты"
    ]
    
    for title in titles:
        print(f"\n--- Checking: {title} ---")
        cursor.execute("SELECT * FROM recipes WHERE title LIKE ?", (f"%{title}%",))
        row = cursor.fetchone()
        if row:
            # Get column names
            cursor.execute("PRAGMA table_info(recipes)")
            cols = [c[1] for c in cursor.fetchall()]
            recipe_dict = dict(zip(cols, row))
            for key, value in recipe_dict.items():
                print(f"{key}: {value}")
        else:
            print("NOT FOUND")
    
    conn.close()

if __name__ == "__main__":
    check_recipes()
