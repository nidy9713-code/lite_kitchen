import sqlite3
import sys

def debug_smoothies():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    print("=== All categories in DB ===")
    cursor.execute("SELECT DISTINCT category FROM recipes")
    cats = cursor.fetchall()
    for c in cats:
        print(f"'{c[0]}'")
        
    print("\n=== Recipes in 'Смузи для детей' ===")
    cursor.execute("SELECT id, title, category, meal_type FROM recipes WHERE category = 'Смузи для детей'")
    recipes = cursor.fetchall()
    for r in recipes:
        print(f"ID {r[0]}: {r[1]} (Cat: {r[2]}, Meal: {r[3]})")
        
    conn.close()

if __name__ == "__main__":
    debug_smoothies()
