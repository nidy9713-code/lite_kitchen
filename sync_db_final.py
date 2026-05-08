import sqlite3
import sys
import os
import re
from docx import Document

# Четкое соответствие файлов разделам
FILE_MAPPING = {
    "Напитки.docx": {"category": "Напитки", "meal_type": "Напиток"},
    "Десерты.docx": {"category": "Десерты", "meal_type": "Десерт"}
}

SOURCE_DIR = r"c:\Users\nidy9\OneDrive\Документы"

def parse_docx_final(file_path, category, meal_type):
    doc = Document(file_path)
    recipes = []
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    current_recipe = None
    current_section = "about"
    for line in lines:
        if line.lower().startswith("название:"):
            if current_recipe:
                if current_recipe['ingredients'] or current_recipe['steps']:
                    recipes.append(current_recipe)
            title_text = line[9:].strip()
            current_recipe = {
                "title": re.sub(r'[🍽🍳🥩🐟🥗🥞🥣⏰⏱]', '', title_text).strip().capitalize(),
                "about": "", "ingredients": "", "steps": "", "tips": "",
                "serving": "", "substitutions": "", "category": category,
                "meal_type": meal_type, "cook_time": 15, "tags": "[]"
            }
            current_section = "about"
            continue
        if not current_recipe: continue
        line_lower = line.lower()
        if "ингредиенты" in line_lower: current_section = "ingredients"
        elif any(x in line_lower for x in ["приготовление", "готовим"]): current_section = "steps"
        elif any(x in line_lower for x in ["подсказка", "лайфхак", "совет"]): current_section = "tips"
        elif "подача" in line_lower: current_section = "serving"
        elif "замены" in line_lower: current_section = "substitutions"
        elif "⏰" in line or "время" in line_lower:
            m = re.search(r'(\d+)', line)
            if m: current_recipe["cook_time"] = int(m.group(1))
        else:
            if current_section == "ingredients": current_recipe["ingredients"] += line + "\n"
            elif current_section == "steps": current_recipe["steps"] += line + "\n"
            elif current_section == "tips": current_recipe["tips"] += line + "\n"
            elif current_section == "serving": current_recipe["serving"] += line + "\n"
            elif current_section == "substitutions": current_recipe["substitutions"] += line + "\n"
            else: current_recipe["about"] += line + "\n"
    if current_recipe and (current_recipe['ingredients'] or current_recipe['steps']):
        recipes.append(current_recipe)
    return recipes

def sync_db():
    conn = sqlite3.connect("recipes.db", timeout=20)
    cursor = conn.cursor()
    
    # 1. Удаляем старые записи
    cursor.execute("DELETE FROM recipes WHERE category IN ('Напитки', 'Десерты')")
    print("Старые записи удалены.")

    for file_name, info in FILE_MAPPING.items():
        src = os.path.join(SOURCE_DIR, file_name)
        if not os.path.exists(src):
            print(f"Файл не найден: {file_name}")
            continue
        recipes = parse_docx_final(src, info["category"], info["meal_type"])
        print(f"Файл {file_name}: Найдено {len(recipes)} рецептов")
        for r in recipes:
            cursor.execute("""
                INSERT INTO recipes (
                    title, about, ingredients, steps, tips, serving, substitutions, tags, category, meal_type, time_category, cook_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r['title'], r['about'].strip(), r['ingredients'].strip(), r['steps'].strip(), 
                r['tips'].strip(), r['serving'].strip(), r['substitutions'].strip(), 
                r['tags'], r['category'], r['meal_type'], 
                "quick" if r['cook_time'] <= 15 else "medium", r['cook_time']
            ))
            print(f"  Добавлен: {r['title']}")
                
    conn.commit()
    conn.close()
    print("Синхронизация завершена.")

if __name__ == "__main__":
    sync_db()
