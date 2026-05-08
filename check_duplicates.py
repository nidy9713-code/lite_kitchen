import sqlite3
from collections import Counter

def check_duplicates():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT title FROM recipes")
    titles = [row[0].strip().lower() for row in cursor.fetchall()]
    
    duplicates = [item for item, count in Counter(titles).items() if count > 1]
    
    if duplicates:
        print("Found duplicate titles:")
        for d in duplicates:
            print(f" - {d}")
    else:
        print("No duplicate titles found.")
        
    conn.close()

if __name__ == "__main__":
    check_duplicates()
