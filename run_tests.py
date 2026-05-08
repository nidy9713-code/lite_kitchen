import asyncio
import sqlite3
import json
from bot.database.db import db

async def run_internal_test():
    print("🚀 Starting Internal Automated Test...")
    
    # 1. Check DB Integrity
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM recipes")
    recipe_count = cursor.fetchone()[0]
    print(f"✅ Database check: {recipe_count} recipes found.")
    
    cursor.execute("SELECT COUNT(*) FROM constructors")
    const_count = cursor.fetchone()[0]
    print(f"✅ Database check: {const_count} constructors found.")
    
    # 2. Check for empty recipes or garbage titles
    cursor.execute("SELECT id, title FROM recipes WHERE length(title) > 90 OR title LIKE 'Способ%' OR title LIKE 'Разогреть%'")
    garbage = cursor.fetchall()
    if garbage:
        print(f"❌ Found {len(garbage)} garbage titles!")
    else:
        print("✅ No garbage titles found.")
        
    cursor.execute("SELECT id, title FROM recipes WHERE ingredients = '' OR steps = ''")
    empty = cursor.fetchall()
    if empty:
        print(f"❌ Found {len(empty)} empty recipes!")
    else:
        print("✅ No empty recipes found.")
        
    # 3. Test DB Methods
    try:
        # Test search
        results = await db.search_recipes("Лосось")
        print(f"✅ DB Search test: Found {len(results)} recipes for 'Лосось'.")
        
        # Test meal type filtering
        breakfasts = await db.get_recipes_by_meal_and_cat("Завтрак", "Каши")
        print(f"✅ DB Filter test: Found {len(breakfasts)} breakfasts in 'Каши'.")
        
        # Test constructor fetch
        consts = await db.get_constructors()
        print(f"✅ DB Constructor test: Fetched {len(consts)} constructors.")
        
    except Exception as e:
        print(f"❌ DB Method test failed: {e}")
        
    print("\n🏁 Internal Test Finished.")

if __name__ == "__main__":
    asyncio.run(run_internal_test())
