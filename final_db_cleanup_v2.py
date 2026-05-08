import sqlite3
import re

def final_cleanup():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    # 1. Delete recipes where title is just a step
    cursor.execute("DELETE FROM recipes WHERE title LIKE 'Выпекать%' OR title LIKE 'Духовку%' OR title LIKE 'Соединить%' OR title LIKE 'Масса получится%' OR title LIKE 'практически из любой%'")
    print(f"Deleted {cursor.rowcount} garbage recipes (steps as titles)")
    
    # 2. Delete recipes where title is just time
    cursor.execute("SELECT id, title FROM recipes")
    rows = cursor.fetchall()
    to_delete = []
    for rid, title in rows:
        if re.match(r'^\d+([-–]\d+)?\s*(минут|мин)\.?\s*(на сковороде|в духовке)?$', title, re.I):
            to_delete.append(rid)
            
    for rid in to_delete:
        cursor.execute("DELETE FROM recipes WHERE id = ?", (rid,))
    print(f"Deleted {len(to_delete)} garbage recipes (time as titles)")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    final_cleanup()
