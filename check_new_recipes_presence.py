import sqlite3
import json
import sys

def check_new_recipes():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    titles = [
        "Куриная печень с морковью и луком",
        "Говяжье сердце с овощами",
        "Печеночные оладьи",
        "Тушеная капуста с куриными сердечками"
    ]
    
    for title in titles:
        print(f"\n--- Checking: {title} ---")
        # Use LIKE for fuzzy matching to handle slight variations in titles
        cursor.execute("SELECT * FROM recipes WHERE title LIKE ?", (f"%{title}%",))
        rows = cursor.fetchall()
        if rows:
            # Get column names
            cursor.execute("PRAGMA table_info(recipes)")
            cols = [c[1] for c in cursor.fetchall()]
            for row in rows:
                recipe_dict = dict(zip(cols, row))
                print(f"FOUND ID {recipe_dict['id']}: {recipe_dict['title']}")
                for key, value in recipe_dict.items():
                    if key not in ['id', 'title']:
                        print(f"  {key}: {value}")
        else:
            print("NOT FOUND")
    
    conn.close()

if __name__ == "__main__":
    check_new_recipes()
