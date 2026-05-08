import sqlite3
import json
import sys

def check_sides():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    titles = [
        "Картофельное пюре",
        "Запеченные овощи",
        "Стейки из капусты",
        "Волшебная гречка"
    ]
    
    for title in titles:
        print(f"\n--- Checking: {title} ---")
        cursor.execute("SELECT * FROM recipes WHERE title LIKE ?", (f"%{title}%",))
        rows = cursor.fetchall()
        if rows:
            cursor.execute("PRAGMA table_info(recipes)")
            cols = [c[1] for c in cursor.fetchall()]
            for row in rows:
                recipe_dict = dict(zip(cols, row))
                print(f"FOUND ID {recipe_dict['id']}: {recipe_dict['title']}")
                print(f"  Category: {recipe_dict['category']}")
                print(f"  About: {recipe_dict['about']}")
                print(f"  Ingredients: {recipe_dict['ingredients'][:100]}...")
        else:
            print("NOT FOUND")
    
    conn.close()

if __name__ == "__main__":
    check_sides()
