import sqlite3

def cleanup():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    # Delete recipes with obviously wrong titles
    garbage_titles = ['Ингредиенты', 'Приготовление', 'Готовим', 'Подсказка', 'Замены', 'Подача']
    for title in garbage_titles:
        cursor.execute("DELETE FROM recipes WHERE title LIKE ?", (f"%{title}%",))
        print(f"Deleted {cursor.rowcount} recipes with title containing '{title}'")
        
    # Delete very short titles
    cursor.execute("DELETE FROM recipes WHERE length(title) < 4")
    print(f"Deleted {cursor.rowcount} recipes with very short titles")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    cleanup()
