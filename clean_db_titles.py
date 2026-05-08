import sqlite3
import re

def clean_titles():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title FROM recipes")
    rows = cursor.fetchall()
    
    updated_count = 0
    for row_id, title in rows:
        # Pattern to match leading time like "15 минут", "5-7 мин", etc., or emojis
        # and remove them from the title
        new_title = title.strip()
        
        # Remove leading emojis
        new_title = re.sub(r'^[🍽🍴🍳🥩🐟🥗🥞🥣⏰⏱]+\s*', '', new_title)
        
        # Remove leading time patterns like "15 минут", "5-7 минут"
        new_title = re.sub(r'^\d+([-–]\d+)?\s*(минут|мин)\.?\s*', '', new_title, flags=re.IGNORECASE)
        
        # Remove any leading dashes or dots that might be left
        new_title = re.sub(r'^[-–.\s]+', '', new_title)
        
        if new_title != title:
            cursor.execute("UPDATE recipes SET title = ? WHERE id = ?", (new_title, row_id))
            updated_count += 1
            print(f"Updated: '{title}' -> '{new_title}'")
            
    conn.commit()
    print(f"Total titles cleaned: {updated_count}")
    conn.close()

if __name__ == "__main__":
    clean_titles()
