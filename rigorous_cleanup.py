import sqlite3
import re

def rigorous_cleanup():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    # 1. Delete recipes with titles that look like instructions or are too long
    # Heuristic: Title > 90 chars is almost certainly not a title
    cursor.execute("DELETE FROM recipes WHERE length(title) > 90")
    print(f"Deleted {cursor.rowcount} recipes with too long titles (>90 chars)")
    
    # 2. Delete recipes where title starts with instruction verbs or common phrases
    instruction_starts = [
        'Способ приготовления', 'Разогреть', 'Взбить', 'Выложить', 'Нарезать', 
        'Смешать', 'Добавить', 'Выпекать', 'Духовку', 'Соединить', 'Масса получится',
        'практически из любой', 'Как только', 'Подавать', 'Можно дополнить'
    ]
    for start in instruction_starts:
        cursor.execute("DELETE FROM recipes WHERE title LIKE ?", (f"{start}%",))
        print(f"Deleted {cursor.rowcount} recipes starting with '{start}'")
        
    # 3. Delete empty recipes
    cursor.execute("DELETE FROM recipes WHERE (ingredients IS NULL OR ingredients = '') AND (steps IS NULL OR steps = '')")
    print(f"Deleted {cursor.rowcount} empty recipes")
    
    # 4. Delete titles that are just sections
    sections = ['Ингредиенты', 'Приготовление', 'Готовим', 'Подсказка', 'Замены', 'Подача', 'Лайфхаки']
    for s in sections:
        cursor.execute("DELETE FROM recipes WHERE title = ?", (s,))
        cursor.execute("DELETE FROM recipes WHERE title = ?", (s + ":",))
        
    # 5. Specific garbage from the screenshot
    cursor.execute("DELETE FROM recipes WHERE title LIKE 'Рыбная пятиминутка. Тут вам%'")
    cursor.execute("DELETE FROM recipes WHERE title LIKE 'Запеченая скумбрия с рисом (%'")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    rigorous_cleanup()
