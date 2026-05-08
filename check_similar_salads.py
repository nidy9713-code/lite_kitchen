import sqlite3
import json
import sys

def check_similar_salads():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    queries = ["Детокс", "Умник", "Красна девица", "Зеленый салат", "Орлиный глаз", "креветок", "фасолью"]
    
    for q in queries:
        print(f"\n--- Searching for: {q} ---")
        cursor.execute("SELECT id, title, category FROM recipes WHERE title LIKE ?", (f"%{q}%",))
        rows = cursor.fetchall()
        for row in rows:
            print(f"ID {row[0]}: {row[1]} ({row[2]})")
    
    conn.close()

if __name__ == "__main__":
    check_similar_salads()
