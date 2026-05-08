import os
import shutil
import re
import asyncio
from docx import Document
from bot.database.db import db

# Mapping of file names to categories and meal types
FILE_MAPPING = {
    "Завтраки из яиц.docx": {"category": "Завтраки из яиц", "meal_type": "Завтрак"},
    "Оладушки и и блины.docx": {"category": "Оладушки и блины", "meal_type": "Завтрак"},
    "Творог и молочка.docx": {"category": "Творог и молочка", "meal_type": "Завтрак"},
    "Мясо.docx": {"category": "Мясо", "meal_type": "Ужин"}, # Default to Dinner, will redistribute later
    "Рыба.docx": {"category": "Рыба", "meal_type": "Ужин"},
    "Блюда из овощей.docx": {"category": "Блюда из овощей", "meal_type": "Ужин"},
    "Блюда из печени и сердца.docx": {"category": "Блюда из печени и сердца", "meal_type": "Ужин"}
}

SOURCE_DIR = r"c:\Users\nidy9\OneDrive\Документы"
TEMP_DIR = "temp_docs"

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def parse_docx(file_path, category, meal_type):
    doc = Document(file_path)
    recipes = []
    current_recipe = None
    
    # Simple heuristic: bold text or large text might be a title
    # Or lines starting with specific emojis/keywords
    
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text.strip())
            
    # Join and split by common recipe delimiters if possible, 
    # but let's try paragraph by paragraph first
    
    content = "\n".join(full_text)
    # Split by double newline or common title patterns
    # Many recipes in these docs start with a title followed by time
    parts = re.split(r'\n(?=[🍽🍴🍳🥩🐟🥗]|(?:\d+\.))', content)
    
    for part in parts:
        lines = part.strip().split('\n')
        if not lines: continue
        
        title = lines[0].replace('🍽', '').replace('🍴', '').strip()
        if len(title) < 3 or len(title) > 100: continue
        
        recipe = {
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
        for line in lines[1:]:
            line_lower = line.lower()
            if "ингредиенты" in line_lower:
                current_section = "ingredients"
                continue
            elif "приготовление" in line_lower or "готовим" in line_lower:
                current_section = "steps"
                continue
            elif "подсказка" in line_lower or "лайфхак" in line_lower or "совет" in line_lower:
                current_section = "tips"
                continue
            elif "подача" in line_lower:
                current_section = "serving"
                continue
            elif "замены" in line_lower:
                current_section = "substitutions"
                continue
            elif "время" in line_lower or "⏰" in line:
                time_match = re.search(r'(\d+)', line)
                if time_match:
                    recipe["cook_time"] = int(time_match.group(1))
                continue
                
            if current_section == "ingredients":
                recipe["ingredients"] += line + "\n"
            elif current_section == "steps":
                recipe["steps"] += line + "\n"
            elif current_section == "tips":
                recipe["tips"] += line + "\n"
            elif current_section == "serving":
                recipe["serving"] += line + "\n"
            elif current_section == "substitutions":
                recipe["substitutions"] += line + "\n"
            else:
                recipe["about"] += line + "\n"
        
        # Clean up
        recipe["ingredients"] = recipe["ingredients"].strip()
        recipe["steps"] = recipe["steps"].strip()
        recipe["about"] = recipe["about"].strip()
        
        # Determine time category
        if recipe["cook_time"] <= 15: recipe["time_category"] = "quick"
        elif recipe["cook_time"] <= 30: recipe["time_category"] = "medium"
        else: recipe["time_category"] = "long"
        
        recipes.append(recipe)
        
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
            recipes = parse_docx(dst, info["category"], info["meal_type"])
            print(f"Found {len(recipes)} recipes in {file_name}")
            
            for r in recipes:
                # Check for duplicates by title
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
    
    # Redistribution logic
    print("Redistributing recipes to Lunch...")
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    # Move recipes > 25 mins from Meat, Fish, Vegetables to Lunch if they are not already there
    # Also move some to Lunch even if they are shorter but are "Meat" or "Fish"
    cursor.execute("""
        UPDATE recipes 
        SET meal_type = 'Обед' 
        WHERE (category IN ('Мясо', 'Рыба', 'Блюда из овощей', 'Блюда из печени и сердца', 'Супы'))
        AND cook_time >= 20
    """)
    print(f"Updated {cursor.rowcount} recipes to Lunch based on time and category.")
    
    # Ensure Breakfast categories are actually Breakfast
    cursor.execute("""
        UPDATE recipes 
        SET meal_type = 'Завтрак' 
        WHERE category IN ('Каши', 'Завтраки из яиц', 'Оладушки и блины', 'Творог и молочка')
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
