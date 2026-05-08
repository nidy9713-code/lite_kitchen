import asyncio
import sqlite3
import json

def fix_text_casing(text):
    if not text or not isinstance(text, str):
        return text
    text = text.strip()
    if not text:
        return text
    # Capitalize first letter, rest lowercase
    return text[0].upper() + text[1:].lower()

async def fix_all_recipes_casing():
    conn = sqlite3.connect("recipes.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, about FROM recipes")
    recipes = cursor.fetchall()
    
    print(f"Processing {len(recipes)} recipes...")
    
    for r in recipes:
        new_title = fix_text_casing(r['title'])
        new_about = fix_text_casing(r['about'])
        
        if new_title != r['title'] or new_about != r['about']:
            cursor.execute(
                "UPDATE recipes SET title = ?, about = ? WHERE id = ?",
                (new_title, new_about, r['id'])
            )
            
    conn.commit()
    print("Casing fixed successfully!")
    conn.close()

if __name__ == "__main__":
    asyncio.run(fix_all_recipes_casing())
