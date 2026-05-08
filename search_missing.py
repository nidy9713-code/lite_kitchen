import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

def search_recipes():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    print("Tags in 'Сезонные смузи':")
    cursor.execute("SELECT DISTINCT tags FROM recipes WHERE category = 'Сезонные смузи'")
    for row in cursor.fetchall():
        print(row[0])
    conn.close()
        
    conn.close()

if __name__ == "__main__":
    search_recipes()
