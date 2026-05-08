import sqlite3
import sys

def check_recipe_categories():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    # Predefined categories from bot/keyboards/inline.py
    PREDEFINED_CATEGORIES = [
        "Каши", "Завтраки из яиц", "Оладушки и блины", 
        "Творог и молочка", "Супы", "Мясо", "Рыба", "Десерты",
        "Блюда из овощей", "Блюда из печени и сердца",
        "Гарниры", "Запеканки", "Напитки", "Салаты", "Брускеты и закуски",
        "Смузи для детей"
    ]
    
    print("=== Checking Recipe Categories ===")
    
    # 1. Check for recipes with NO category
    cursor.execute("SELECT id, title FROM recipes WHERE category IS NULL OR category = ''")
    no_cat = cursor.fetchall()
    print(f"\nRecipes with NO category: {len(no_cat)}")
    for r in no_cat:
        print(f"  ID {r[0]}: {r[1]}")
        
    # 2. Check for recipes with categories NOT in the predefined list
    cursor.execute("SELECT id, title, category FROM recipes")
    all_recipes = cursor.fetchall()
    invalid_cat = []
    for r_id, title, cat in all_recipes:
        if cat not in PREDEFINED_CATEGORIES:
            invalid_cat.append((r_id, title, cat))
            
    print(f"\nRecipes with INVALID/OTHER categories: {len(invalid_cat)}")
    for r in invalid_cat:
        print(f"  ID {r[0]}: {r[1]} (Category: '{r[2]}')")
        
    # 3. List recipes by category to see distribution
    print("\n=== Recipes by Category ===")
    cursor.execute("SELECT category, COUNT(*) FROM recipes GROUP BY category")
    counts = cursor.fetchall()
    for cat, count in counts:
        status = "✅ OK" if cat in PREDEFINED_CATEGORIES else "❌ NOT IN LIST"
        print(f"  {cat}: {count} recipes [{status}]")
        
    conn.close()

if __name__ == "__main__":
    check_recipe_categories()
