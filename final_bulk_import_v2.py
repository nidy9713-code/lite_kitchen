import os
import shutil
import re
import asyncio
import sqlite3
from docx import Document
from bot.database.db import db

# Mapping of file names to categories and meal types
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

def parse_docx_v2(file_path, category, meal_type):
    doc = Document(file_path)
    recipes = []
    
    current_recipe = None
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text: continue
        
        # Heuristic for title: Bold or starts with emoji or is short and capitalized
        is_title = False
        if para.runs and para.runs[0].bold:
            is_title = True
        elif any(emoji in text for emoji in ['🍽', '🍳', '🥩', '🐟', '🥗', '🥞', '🥣']):
            is_title = True
        elif len(text) < 60 and text.isupper():
            is_title = True
            
        if is_title and len(text) > 3:
            if current_recipe:
                recipes.append(current_recipe)
            
            title = re.sub(r'[🍽🍳🥩🐟🥗🥞🥣]', '', text).strip()
            current_recipe = {
                "title": title,
                "about": "",
                "ingredients": "",
                "steps": "",
                "tips": "",
                "serving": "",
                "substitutions": "",
                "category": category,
                "meal_type": meal_type,
                "time_category": "medium",
                "cook_time": 30,
                "tags": []
            }
            current_section = "about"
            continue
            
        if not current_recipe: continue
        
        line_lower = text.lower()
        if "ингредиенты" in line_lower:
            current_section = "ingredients"
        elif "приготовление" in line_lower or "готовим" in line_lower:
            current_section = "steps"
        elif "подсказка" in line_lower or "лайфхак" in line_lower or "совет" in line_lower:
            current_section = "tips"
        elif "подача" in line_lower:
            current_section = "serving"
        elif "замены" in line_lower:
            current_section = "substitutions"
        elif "время" in line_lower or "⏰" in text:
            time_match = re.search(r'(\d+)', text)
            if time_match:
                current_recipe["cook_time"] = int(time_match.group(1))
        else:
            if current_section == "ingredients":
                current_recipe["ingredients"] += text + "\n"
            elif current_section == "steps":
                current_recipe["steps"] += text + "\n"
            elif current_section == "tips":
                current_recipe["tips"] += text + "\n"
            elif current_section == "serving":
                current_recipe["serving"] += text + "\n"
            elif current_section == "substitutions":
                current_recipe["substitutions"] += text + "\n"
            else:
                current_recipe["about"] += text + "\n"
                
    if current_recipe:
        recipes.append(current_recipe)
        
    for r in recipes:
        r["ingredients"] = r["ingredients"].strip()
        r["steps"] = r["steps"].strip()
        r["about"] = r["about"].strip()
        if r["cook_time"] <= 15: r["time_category"] = "quick"
        elif r["cook_time"] <= 30: r["time_category"] = "medium"
        else: r["time_category"] = "long"
        
    return recipes

async def main():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        
    total_added = 0
    for file_name, info in FILE_MAPPING.items():
        src = os.path.join(SOURCE_DIR, file_name)
        dst = os.path.join(TEMP_DIR, file_name)
        
        if not os.path.exists(src):
            print(f"File not found: {src}")
            continue
            
        try:
            shutil.copy2(src, dst)
            print(f"Processing {file_name}...")
            recipes = parse_docx_v2(dst, info["category"], info["meal_type"])
            print(f"Found {len(recipes)} recipes in {file_name}")
            
            for r in recipes:
                existing = await db.search_recipes(r["title"])
                is_duplicate = False
                for ex in existing:
                    if ex["title"].lower() == r["title"].lower():
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    await db.add_recipe(r)
                    total_added += 1
                else:
                    print(f"Skipping duplicate: {r['title']}")
                    
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
            
    print(f"Total new recipes added: {total_added}")
    
    print("Redistributing recipes to Lunch...")
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    # Move recipes > 20 mins from Meat, Fish, Vegetables, Liver to Lunch
    cursor.execute("""
        UPDATE recipes 
        SET meal_type = 'Обед' 
        WHERE category IN ('Мясо', 'Рыба', 'Блюда из овощей', 'Блюда из печени и сердца', 'Супы')
        AND cook_time >= 20
    """)
    print(f"Updated {cursor.rowcount} recipes to Lunch.")
    
    # Ensure Breakfast categories are Breakfast
    cursor.execute("""
        UPDATE recipes 
        SET meal_type = 'Завтрак' 
        WHERE category IN ('Каши', 'Завтраки из яиц', 'Оладушки и блины', 'Творог и молочка')
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
