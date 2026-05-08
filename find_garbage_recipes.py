import sqlite3
import sys

def find_garbage():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    
    # Selecting all recipes to analyze titles
    cursor.execute("SELECT id, title, category FROM recipes")
    rows = cursor.fetchall()
    
    garbage_ids = []
    
    # Heuristics for garbage titles:
    # 1. Very long titles (usually sentences/paragraphs)
    # 2. Titles containing bullets or typical instruction words
    # 3. Titles that look like tips (starting with "💡", "📌", "✨", or words like "Помните", "Важно", "Витамины")
    # 4. Titles that are too short/generic (e.g., "Готовим:", "Ингредиенты:")
    
    garbage_keywords = [
        "витамины", "способствует", "помогает", "нормализации", "выведению", 
        "профилактирует", "организм", "полезно", "важно", "помните", 
        "подходит для", "готовим:", "лайфхак", "совет:", "примечание",
        "🫜", "🥕", "🥑", "🥦", "🍎", "🍏", "🍐" # Emojis often used in tips but rarely at the start of a clean title
    ]
    
    print("Potential garbage recipes found:")
    print("-" * 50)
    for row in rows:
        r_id, title, category = row
        is_garbage = False
        reason = ""
        
        # Reason 1: Length
        if len(title) > 60:
            is_garbage = True
            reason = "Too long (>60 chars)"
            
        # Reason 2: Keywords
        lower_title = title.lower()
        for k in garbage_keywords:
            if k in lower_title:
                is_garbage = True
                reason = f"Contains keyword '{k}'"
                break
                
        # Reason 3: Bullets or generic headers
        if title.startswith("—") or title.startswith("•") or title.startswith("-"):
            is_garbage = True
            reason = "Starts with bullet"
            
        if is_garbage:
            print(f"ID {r_id} [{category}]: {title}")
            print(f"REASON: {reason}")
            print("-" * 30)
            garbage_ids.append(r_id)
            
    conn.close()
    return garbage_ids

if __name__ == "__main__":
    find_garbage()
