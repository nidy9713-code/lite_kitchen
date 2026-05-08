import sqlite3
import asyncio
from bot.database.db import db

async def check_stats():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    print("--- Recipe counts by category ---")
    cursor.execute("SELECT category, COUNT(*) FROM recipes GROUP BY category")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]}")
        
    print("\n--- Recipe counts by meal_type ---")
    cursor.execute("SELECT meal_type, COUNT(*) FROM recipes GROUP BY meal_type")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]}")
        
    print("\n--- Lunch (Обед) recipes sample ---")
    cursor.execute("SELECT title, category, cook_time FROM recipes WHERE meal_type = 'Обед' LIMIT 10")
    for row in cursor.fetchall():
        print(row)

    conn.close()

if __name__ == "__main__":
    asyncio.run(check_stats())
