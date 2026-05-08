import sqlite3
import sys

# Set encoding for terminal output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def debug_db_content():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    print("--- CATEGORY COUNTS ---")
    cursor.execute("SELECT category, COUNT(*) FROM recipes GROUP BY category")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]}")
        
    print("\n--- MEAL_TYPE COUNTS ---")
    cursor.execute("SELECT meal_type, COUNT(*) FROM recipes GROUP BY meal_type")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]}")
        
    print("\n--- DRINKS (Напитки) SAMPLE ---")
    cursor.execute("SELECT id, title, category, meal_type FROM recipes WHERE category = 'Напитки' OR meal_type = 'Напиток' LIMIT 10")
    for row in cursor.fetchall():
        print(f"ID: {row[0]} | Title: {row[1]} | Cat: {row[2]} | Meal: {row[3]}")

    print("\n--- DESSERTS (Десерты) SAMPLE ---")
    cursor.execute("SELECT id, title, category, meal_type FROM recipes WHERE category = 'Десерты' OR meal_type = 'Десерт' LIMIT 10")
    for row in cursor.fetchall():
        print(f"ID: {row[0]} | Title: {row[1]} | Cat: {row[2]} | Meal: {row[3]}")

    conn.close()

if __name__ == "__main__":
    debug_db_content()
