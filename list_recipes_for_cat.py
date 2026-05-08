import sqlite3
import json
import sys

def list_recipes_for_categorization():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    # Fetch recipes that are NOT Desserts or Drinks
    cursor.execute("""
        SELECT id, title, category, meal_type 
        FROM recipes 
        WHERE category NOT IN ('Десерты', 'Напитки')
    """)
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"ID {row[0]}: {row[1]} (Category: {row[2]}, Current Meal Type: {row[3]})")
        
    conn.close()

if __name__ == "__main__":
    list_recipes_for_categorization()
