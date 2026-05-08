import sqlite3
import sys

# Set encoding for terminal output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def fix_title_case():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title FROM recipes")
    rows = cursor.fetchall()
    
    updated_count = 0
    for row_id, title in rows:
        # Standardize title: Capitalize first letter, rest lowercase
        # strip() to remove any accidental spaces
        clean_title = title.strip()
        if not clean_title:
            continue
            
        # We use capitalize() which does exactly this: First letter upper, rest lower
        new_title = clean_title.capitalize()
        
        if new_title != title:
            cursor.execute("UPDATE recipes SET title = ? WHERE id = ?", (new_title, row_id))
            updated_count += 1
            try:
                print(f"Updated case: '{title}' -> '{new_title}'")
            except:
                print(f"Updated ID {row_id}")
            
    conn.commit()
    print(f"Total titles case-standardized: {updated_count}")
    conn.close()

if __name__ == "__main__":
    fix_title_case()
