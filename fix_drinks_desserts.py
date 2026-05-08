import os
import shutil
import re
import asyncio
import sqlite3
from docx import Document
from bot.database.db import db

# Четкое соответствие файлов разделам
FILE_MAPPING = {
    "Напитки.docx": {"category": "Напитки", "meal_type": "Напиток"},
    "Десерты.docx": {"category": "Десерты", "meal_type": "Десерт"}
}

SOURCE_DIR = r"c:\Users\nidy9\OneDrive\Документы"

def parse_docx_final(file_path, category, meal_type):
    doc = Document(file_path)
    recipes = []
    
    # Собираем все параграфы
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    current_recipe = None
    current_section = "about"
    
    for line in lines:
        # Ищем маркер "Название:"
        if line.lower().startswith("название:"):
            if current_recipe:
                if current_recipe['ingredients'] or current_recipe['steps']:
                    recipes.append(current_recipe)
            
            title_text = line[9:].strip()
            current_recipe = {
                "title": re.sub(r'[🍽🍳🥩🐟🥗🥞🥣⏰⏱]', '', title_text).strip().capitalize(),
                "about": "", "ingredients": "", "steps": "", "tips": "",
                "serving": "", "substitutions": "", "category": category,
                "meal_type": meal_type, "cook_time": 15, "tags": []
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

async def main():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    # 1. Сначала удаляем старые (неправильные) десерты и напитки, чтобы не было дублей
    # Но оставляем Смузи для детей (у них категория "Смузи для детей")
    cursor.execute("DELETE FROM recipes WHERE category IN ('Напитки', 'Десерты')")
    print("Старые записи разделов Напитки и Десерты удалены.")

    total_added = 0
    for file_name, info in FILE_MAPPING.items():
        src = os.path.join(SOURCE_DIR, file_name)
        if not os.path.exists(src):
            print(f"Файл не найден: {file_name}")
            continue
            
        recipes = parse_docx_final(src, info["category"], info["meal_type"])
        print(f"Файл {file_name}: Найдено {len(recipes)} рецептов")
        
        for r in recipes:
            r["ingredients"] = r["ingredients"].strip()
            r["steps"] = r["steps"].strip()
            r["about"] = r["about"].strip()
            
            if r["cook_time"] <= 15: r["time_category"] = "quick"
            elif r["cook_time"] <= 30: r["time_category"] = "medium"
            else: r["time_category"] = "long"
            
            await db.add_recipe(r)
            total_added += 1
            print(f"  Добавлен: {r['title']}")
                
    conn.commit()
    conn.close()
    print(f"Импорт завершен. Добавлено {total_added} рецептов.")

if __name__ == "__main__":
    asyncio.run(main())
