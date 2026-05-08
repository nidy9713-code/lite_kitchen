import sqlite3

def rename_recipes():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    
    # Update titles for ID 266 and 267
    cursor.execute("UPDATE recipes SET title = ? WHERE id = ?", ("Говяжье сердце с овощами", 266))
    cursor.execute("UPDATE recipes SET title = ? WHERE id = ?", ("Печеночные оладьи", 267))
    
    conn.commit()
    print("Рецепты успешно переименованы.")
    conn.close()

if __name__ == "__main__":
    rename_recipes()
