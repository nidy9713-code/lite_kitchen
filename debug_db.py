import sqlite3
import json

def check_db():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    print("--- Constructors table ---")
    cursor.execute("SELECT id, title FROM constructors")
    rows = cursor.fetchall()
    print(f"Count: {len(rows)}")
    for row in rows:
        print(row)
        
    print("\n--- Recipes table (sample) ---")
    cursor.execute("SELECT id, title FROM recipes LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_db()
