import sqlite3
import re

def clean_dessert_titles():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    # 1. Fetch all desserts
    cursor.execute("SELECT id, title, about FROM recipes WHERE category = 'Десерты'")
    rows = cursor.fetchall()
    
    for rid, title, about in rows:
        # Check if title contains a long description (e.g., " - отличная сладость...")
        if " – " in title or " - " in title:
            parts = re.split(r' [–-] ', title, 1)
            new_title = parts[0].strip().capitalize()
            description_part = parts[1].strip()
            
            # Move the description part to 'about' if it's not already there
            new_about = about if about else ""
            if description_part.lower() not in new_about.lower():
                new_about = description_part + "\n\n" + new_about
            
            cursor.execute("UPDATE recipes SET title = ?, about = ? WHERE id = ?", (new_title, new_about.strip(), rid))
            print(f"Cleaned title: '{title}' -> '{new_title}'")

    # 2. Remove duplicates (keep the one with more content)
    cursor.execute("SELECT title, COUNT(*) as count FROM recipes GROUP BY title HAVING count > 1")
    duplicates = cursor.fetchall()
    for title, count in duplicates:
        cursor.execute("SELECT id, ingredients, steps FROM recipes WHERE title = ?", (title,))
        instances = cursor.fetchall()
        # Sort by content length descending
        instances.sort(key=lambda x: len(x[1] or "") + len(x[2] or ""), reverse=True)
        # Keep the first, delete the rest
        for inst in instances[1:]:
            cursor.execute("DELETE FROM recipes WHERE id = ?", (inst[0],))
            print(f"Deleted duplicate instance of '{title}' (ID: {inst[0]})")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    clean_dessert_titles()
