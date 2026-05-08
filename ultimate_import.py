import os
import shutil
import re
import asyncio
import sqlite3
import json
from docx import Document
from bot.database.db import db

FILE_MAPPING = {
    "Творог и молочка.docx": {"category": "Творог и молочка", "meal_type": "Завтрак"},
    "Блюда из овощей.docx": {"category": "Блюда из овощей", "meal_type": "Ужин"},
    "Блюда из печени и сердца.docx": {"category": "Блюда из печени и сердца", "meal_type": "Ужин"},
    "Брускеты и закуски.docx": {"category": "Брускеты и закуски", "meal_type": "Завтрак"},
    "Гарниры.docx": {"category": "Гарниры", "meal_type": "Ужин"},
    "Десерты.docx": {"category": "Десерты", "meal_type": "Десерт"},
    "Завтраки из яиц.docx": {"category": "Завтраки из яиц", "meal_type": "Завтрак"},
    "Запеканки.docx": {"category": "Запеканки", "meal_type": "Ужин"},
    "Каши.docx": {"category": "Каши", "meal_type": "Завтрак"},
    "Мясо.docx": {"category": "Мясо", "meal_type": "Ужин"},
    "Напитки.docx": {"category": "Напитки", "meal_type": "Напиток"},
    "Оладушки и и блины.docx": {"category": "Оладушки и блины", "meal_type": "Завтрак"},
    "Рыба.docx": {"category": "Рыба", "meal_type": "Ужин"},
    "Салаты.docx": {"category": "Салаты", "meal_type": "Ужин"},
    "Супы.docx": {"category": "Супы", "meal_type": "Обед"}
}

SOURCE_DIR = r"c:\Users\nidy9\OneDrive\Документы"
TEMP_DIR = "temp_docs_final"

def parse_docx_with_marker(file_path, category, meal_type):
    doc = Document(file_path)
    recipes = []
    
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    current_recipe = None
    for i, line in enumerate(lines):
        # NEW LOGIC: Title starts with "Название:"
        if line.lower().startswith("название:"):
            if current_recipe:
                if current_recipe['ingredients'] or current_recipe['steps']:
                    recipes.append(current_recipe)
            
            title = line[9:].strip() # Remove "Название:"
            current_recipe = {
                "title": re.sub(r'[🍽🍳🥩🐟🥗🥞🥣⏰⏱]', '', title).strip(),
                "about": "", "ingredients": "", "steps": "", "tips": "",
                "serving": "", "substitutions": "", "category": category,
                "meal_type": meal_type, "cook_time": 30, "tags": []
            }
            current_section = "about"
            continue
            
        if not current_recipe: continue
        
        line_lower = line.lower()
        if "ингредиенты" in line_lower: current_section = "ingredients"
        elif "приготовление" in line_lower or "готовим" in line_lower: current_section = "steps"
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
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    
    # CLEAR OLD DATA to avoid mess, but keep users
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recipes")
    conn.commit()
    print("Database cleared for fresh import.")

    total_added = 0
    for file_name, info in FILE_MAPPING.items():
        src = os.path.join(SOURCE_DIR, file_name)
        if not os.path.exists(src):
            print(f"File not found: {file_name}")
            continue
            
        dst = os.path.join(TEMP_DIR, file_name)
        shutil.copy2(src, dst)
        
        recipes = parse_docx_with_marker(dst, info["category"], info["meal_type"])
        print(f"File {file_name}: Found {len(recipes)} recipes")
        
        for r in recipes:
            # Final formatting cleanups
            r["ingredients"] = r["ingredients"].strip()
            r["steps"] = r["steps"].strip()
            r["about"] = r["about"].strip()
            
            # Time category
            if r["cook_time"] <= 15: r["time_category"] = "quick"
            elif r["cook_time"] <= 30: r["time_category"] = "medium"
            else: r["time_category"] = "long"
            
            # Check duplicates in THIS run
            cursor.execute("SELECT id FROM recipes WHERE LOWER(title) = ?", (r["title"].lower(),))
            if cursor.fetchone():
                print(f"  Skipping duplicate: {r['title']}")
                continue
                
            await db.add_recipe(r)
            total_added += 1
            
    # Redistribution to Lunch
    cursor.execute("UPDATE recipes SET meal_type = 'Обед' WHERE category IN ('Мясо', 'Рыба', 'Блюда из овощей', 'Блюда из печени и сердца', 'Супы') AND cook_time >= 20")
    print(f"Moved {cursor.rowcount} recipes to Lunch.")
    
    conn.commit()
    conn.close()
    print(f"Total recipes imported: {total_added}")

if __name__ == "__main__":
    asyncio.run(main())
