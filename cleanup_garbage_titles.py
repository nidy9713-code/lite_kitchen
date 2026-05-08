import sqlite3
import sys

def cleanup_titles():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    
    # 1. Find and delete recipes starting with "профилактирует запоры" or "🫜Свекла"
    # These are fragments of text that were misidentified as titles
    cursor.execute("SELECT id, title FROM recipes WHERE title LIKE 'профилактирует%' OR title LIKE '🫜Свекла%'")
    to_delete = cursor.fetchall()
    
    for row in to_delete:
        print(f"Deleting garbage recipe id {row[0]}: {row[1]}")
        cursor.execute("DELETE FROM recipes WHERE id = ?", (row[0],))
        
    # 2. Find and delete "Витамины из моркови"
    cursor.execute("SELECT id, title FROM recipes WHERE title LIKE 'Витамины из морковки%' OR title LIKE 'Витамины из моркови%'")
    to_delete_carrot = cursor.fetchall()
    
    for row in to_delete_carrot:
        print(f"Deleting garbage recipe id {row[0]}: {row[1]}")
        cursor.execute("DELETE FROM recipes WHERE id = ?", (row[0],))

    # 3. New garbage found in other categories
    # ID 466 [Десерты]: 15 + минут
    # ID 11 & 444 [Блюда из овощей]: Duplicate Pizza
    cursor.execute("DELETE FROM recipes WHERE id = 466")
    print("Deleted ID 466 (15 + минут)")
    
    # ID 468: Title too long/description
    cursor.execute("UPDATE recipes SET title = 'Фруктовый бутерброд' WHERE id = 468")
    print("Updated ID 468 title")
    
    # ID 503: Trim the description from title
    cursor.execute("UPDATE recipes SET title = 'Запеченая скумбрия с рисом' WHERE id = 503")
    print("Updated ID 503 title")
    
    # ID 512: Trim
    cursor.execute("UPDATE recipes SET title = 'Салат «Орлиный глаз»' WHERE id = 512")
    print("Updated ID 512 title")
    
    # ID 515: Trim
    cursor.execute("UPDATE recipes SET title = 'Зеленый салат' WHERE id = 515")
    print("Updated ID 515 title")
    
    # Duplicate Pizza: delete id 444, keep id 11
    cursor.execute("DELETE FROM recipes WHERE id = 444")
    print("Deleted duplicate Pizza id 444")
        
    conn.commit()
    conn.close()
    print("Cleanup completed.")

if __name__ == "__main__":
    cleanup_titles()
