import sqlite3

def migrate():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE recipes ADD COLUMN photo_id TEXT")
        conn.commit()
        print("Column 'photo_id' successfully added to 'recipes' table.")
    except sqlite3.OperationalError:
        print("Column 'photo_id' already exists.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
