import sqlite3
import json
import sys

def check_soups():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    titles = [
        "Костный бульон",
        "Чечевичный суп",
        "Рыбная похлебка с киноа и шпинатом",
        "Брокколи крем-суп с зеленым горошком",
        "Тыквенный крем-суп",
        "Холодный томатный суп",
        "Куриный суп с кнелями",
        "Суп с брокколи и кедровыми орешками",
        "Минестроне на скорую руку",
        "Суп с фасолью и цветной капустой",
        "Грибной суп-пюре",
        "Суп из индейки с овощами"
    ]
    
    for title in titles:
        print(f"\n--- Checking: {title} ---")
        cursor.execute("SELECT id, title, category FROM recipes WHERE title LIKE ?", (f"%{title}%",))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"FOUND ID {row[0]}: {row[1]} ({row[2]})")
        else:
            print("NOT FOUND")
    
    conn.close()

if __name__ == "__main__":
    check_soups()
