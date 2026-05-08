import sqlite3
import re
import sys

# Set encoding for terminal output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def clean_titles():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title FROM recipes")
    rows = cursor.fetchall()
    
    updated_count = 0
    for row_id, title in rows:
        new_title = title.strip()
        
        # Remove leading emojis
        new_title = re.sub(r'^[🍽🍴🍳🥩🐟🥗🥞🥣⏰⏱]+\s*', '', new_title)
        
        # Remove leading time patterns like "15 минут", "5-7 минут"
        # But only if there is something else in the title
        temp_title = re.sub(r'^\d+([-–]\d+)?\s*(минут|мин)\.?\s*', '', new_title, flags=re.IGNORECASE)
        temp_title = re.sub(r'^[-–.\s]+', '', temp_title)
        
        if temp_title:
            new_title = temp_title
        
        if new_title != title:
            cursor.execute("UPDATE recipes SET title = ? WHERE id = ?", (new_title, row_id))
            updated_count += 1
            try:
                print(f"Updated: '{title}' -> '{new_title}'")
            except:
                print(f"Updated ID {row_id}")
            
    conn.commit()
    print(f"Total titles cleaned: {updated_count}")
    conn.close()

if __name__ == "__main__":
    clean_titles()
