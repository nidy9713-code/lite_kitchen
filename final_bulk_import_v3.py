import os
import shutil
import re
import asyncio
import sqlite3
from docx import Document
from bot.database.db import db

FILE_MAPPING = {
    "Завтраки из яиц.docx": {"category": "Завтраки из яиц", "meal_type": "Завтрак"},
    "Оладушки и и блины.docx": {"category": "Оладушки и блины", "meal_type": "Завтрак"},
    "Творог и молочка.docx": {"category": "Творог и молочка", "meal_type": "Завтрак"},
    "Мясо.docx": {"category": "Мясо", "meal_type": "Ужин"},
    "Рыба.docx": {"category": "Рыба", "meal_type": "Ужин"},
    "Блюда из овощей.docx": {"category": "Блюда из овощей", "meal_type": "Ужин"},
    "Блюда из печени и сердца.docx": {"category": "Блюда из печени и сердца", "meal_type": "Ужин"}
}

SOURCE_DIR = r"c:\Users\nidy9\OneDrive\Документы"
TEMP_DIR = "temp_docs"

def parse_docx_v3(file_path, category, meal_type):
    doc = Document(file_path)
    recipes = []
    
    # Get all text first
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    current_recipe = None
    
    for i, line in enumerate(lines):
        # A title is likely a line followed by "⏰" or "время" or "ингредиенты"
        is_title = False
        if i + 1 < len(lines):
            next_line = lines[i+1].lower()
            if "⏰" in next_line or "минут" in next_line or "ингредиенты" in next_line:
                is_title = True
        
        if is_title:
            if current_recipe:
                recipes.append(current_recipe)
            
            current_recipe = {
                "title": re.sub(r'[🍽🍳🥩🐟🥗🥞🥣]', '', line).strip(),
                "about": "", "ingredients": "", "steps": "", "tips": "",
                "serving": "", "substitutions": "", "category": category,
                "meal_type": meal_type, "time_category": "medium", "cook_time": 30, "tags": []
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
            
    if current_recipe: recipes.append(current_recipe)
    
    for r in recipes:
        r["ingredients"] = r["ingredients"].strip()
        r["steps"] = r["steps"].strip()
        if r["cook_time"] <= 15: r["time_category"] = "quick"
        elif r["cook_time"] <= 30: r["time_category"] = "medium"
        else: r["time_category"] = "long"
    return recipes

async def main():
    total_added = 0
    for file_name, info in FILE_MAPPING.items():
        src = os.path.join(SOURCE_DIR, file_name)
        if not os.path.exists(src): continue
        
        try:
            recipes = parse_docx_v3(src, info["category"], info["meal_type"])
            print(f"File {file_name}: Found {len(recipes)} recipes")
            for r in recipes:
                existing = await db.search_recipes(r["title"])
                if not any(ex["title"].lower() == r["title"].lower() for ex in existing):
                    await db.add_recipe(r)
                    total_added += 1
        except Exception as e:
            print(f"Error {file_name}: {e}")
            
    print(f"Added {total_added} new recipes.")
    
    # Final redistribution
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE recipes SET meal_type = 'Обед' WHERE category IN ('Мясо', 'Рыба', 'Блюда из овощей', 'Блюда из печени и сердца', 'Супы') AND cook_time >= 20")
    print(f"Moved {cursor.rowcount} to Lunch.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
