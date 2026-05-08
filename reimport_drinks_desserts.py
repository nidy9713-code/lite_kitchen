import os
import shutil
import re
import asyncio
import sqlite3
from docx import Document
from bot.database.db import db

FILE_MAPPING = {
    "Напитки.docx": {"category": "Напитки", "meal_type": "Напиток"},
    "Десерты.docx": {"category": "Десерты", "meal_type": "Десерт"}
}

SOURCE_DIR = r"c:\Users\nidy9\OneDrive\Документы"
TEMP_DIR = "temp_docs_reimport"

def parse_docx_flexible(file_path, category, meal_type):
    doc = Document(file_path)
    recipes = []
    
    # Get all text first
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    current_recipe = None
    current_section = "about"
    
    for i, line in enumerate(lines):
        # Title detection: starts with "Название:", or is bold, or followed by ⏰/ингредиенты
        is_title = False
        if line.lower().startswith("название:"):
            is_title = True
            title_text = line[9:].strip()
        elif i + 1 < len(lines):
            next_line = lines[i+1].lower()
            if any(marker in next_line for marker in ["⏰", "минут", "ингредиенты", "готовим"]):
                is_title = True
                title_text = line
        
        if is_title:
            if current_recipe:
                if current_recipe['ingredients'] or current_recipe['steps']:
                    recipes.append(current_recipe)
            
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
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    
    total_added = 0
    for file_name, info in FILE_MAPPING.items():
        src = os.path.join(SOURCE_DIR, file_name)
        if not os.path.exists(src):
            print(f"File not found: {file_name}")
            continue
            
        dst = os.path.join(TEMP_DIR, file_name)
        shutil.copy2(src, dst)
        
        recipes = parse_docx_flexible(dst, info["category"], info["meal_type"])
        print(f"File {file_name}: Found {len(recipes)} recipes")
        
        for r in recipes:
            r["ingredients"] = r["ingredients"].strip()
            r["steps"] = r["steps"].strip()
            r["about"] = r["about"].strip()
            
            if r["cook_time"] <= 15: r["time_category"] = "quick"
            elif r["cook_time"] <= 30: r["time_category"] = "medium"
            else: r["time_category"] = "long"
            
            # Check for duplicates before adding
            existing = await db.search_recipes(r["title"])
            if not any(ex["title"].lower() == r["title"].lower() for ex in existing):
                await db.add_recipe(r)
                total_added += 1
                print(f"  Added: {r['title']}")
            else:
                # Update existing if needed (optional, but let's just skip for now to avoid mess)
                print(f"  Already exists: {r['title']}")
                
    print(f"Total new recipes added from Drinks/Desserts: {total_added}")

if __name__ == "__main__":
    asyncio.run(main())
