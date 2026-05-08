import sqlite3
import json
import sys

# Set encoding for stdout to utf-8
sys.stdout.reconfigure(encoding='utf-8')

def list_categories():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM recipes")
    cats = [row[0] for row in cursor.fetchall()]
    print("Unique categories in DB:")
    for c in cats:
        print(f"- {c}")
    
    cursor.execute("SELECT DISTINCT meal_type FROM recipes")
    meals = [row[0] for row in cursor.fetchall()]
    print("\nUnique meal_types in DB:")
    for m in meals:
        print(f"- {m}")
    conn.close()

if __name__ == "__main__":
    list_categories()
