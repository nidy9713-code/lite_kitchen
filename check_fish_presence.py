import sqlite3
import json
import sys

def check_fish_recipes():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    titles = [
        "Запеченная рыба с овощами и амарантом",
        "Рыба на овощной подушке",
        "Запеченная скумбрия с салатом",
        "Рыбная пятиминутка",
        "Запеченный минтай с овощами",
        "Скумбрия с рисом",
        "Лосось с овощами"
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
        else:
            print("NOT FOUND")
    
    conn.close()

if __name__ == "__main__":
    check_fish_recipes()
