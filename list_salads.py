import sqlite3
import json
import sys

def check_all_salads():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM recipes WHERE category = 'Салаты'")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID {row[0]}: {row[1]}")
    conn.close()

if __name__ == "__main__":
    check_all_salads()
