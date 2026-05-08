import sqlite3

def delete_ids():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    ids = (493, 500, 523, 557, 576)
    cursor.execute(f"DELETE FROM recipes WHERE id IN {ids}")
    print(f"Deleted {cursor.rowcount} recipes by ID")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    delete_ids()
