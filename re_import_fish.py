import sqlite3
from docx import Document
import os
import re

def re_import_fish():
    file_path = r"c:\Users\nidy9\OneDrive\Документы\Рыба.docx"
    if not os.path.exists(file_path):
        print("File not found")
        return
        
    doc = Document(file_path)
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    current_recipe = None
    for i, line in enumerate(lines):
        # Title detection: bold or followed by time/ingredients
        is_title = False
        if i + 1 < len(lines):
            next_line = lines[i+1].lower()
            if "⏰" in next_line or "минут" in next_line or "ингредиенты" in next_line:
                is_title = True
        
        if is_title:
            if current_recipe:
                # Save previous
                if current_recipe['ingredients'] and current_recipe['steps']:
                    cursor.execute("INSERT INTO recipes (title, about, ingredients, steps, category, meal_type, cook_time, time_category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                   (current_recipe['title'], current_recipe['about'], current_recipe['ingredients'], current_recipe['steps'], 'Рыба', 'Ужин', current_recipe['cook_time'], 'medium'))
            
            current_recipe = {
                "title": re.sub(r'[🍽🍳🥩🐟🥗🥞🥣⏰⏱]', '', line).strip(),
                "about": "", "ingredients": "", "steps": "", "cook_time": 30
            }
            current_section = "about"
            continue
            
        if not current_recipe: continue
        
        line_lower = line.lower()
        if "ингредиенты" in line_lower: current_section = "ingredients"
        elif "приготовление" in line_lower or "готовим" in line_lower: current_section = "steps"
        elif "⏰" in line or "время" in line_lower:
            m = re.search(r'(\d+)', line)
            if m: current_recipe["cook_time"] = int(m.group(1))
        else:
            if current_section == "ingredients": current_recipe["ingredients"] += line + "\n"
            elif current_section == "steps": current_recipe["steps"] += line + "\n"
            else: current_recipe["about"] += line + "\n"
            
    if current_recipe and current_recipe['ingredients'] and current_recipe['steps']:
        cursor.execute("INSERT INTO recipes (title, about, ingredients, steps, category, meal_type, cook_time, time_category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (current_recipe['title'], current_recipe['about'], current_recipe['ingredients'], current_recipe['steps'], 'Рыба', 'Ужин', current_recipe['cook_time'], 'medium'))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    re_import_fish()
