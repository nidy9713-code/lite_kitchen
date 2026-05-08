import sqlite3
import sys

# Set encoding for terminal output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def check_fish_recipes():
    conn = sqlite3.connect("recipes.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- Fish recipes (Рыба) ---")
    cursor.execute("SELECT id, title, about, ingredients, steps FROM recipes WHERE category = 'Рыба' OR title LIKE '%лосось%'")
    rows = cursor.fetchall()
    for row in rows:
        title = row['title']
        is_empty = not (row['about'] or row['ingredients'] or row['steps'])
        print(f"ID: {row['id']} | Title: {title[:50]}... | Empty: {is_empty}")
        if is_empty or len(title) > 60:
            print(f"  Full Title: {title}")
            
    conn.close()

if __name__ == "__main__":
    check_fish_recipes()
