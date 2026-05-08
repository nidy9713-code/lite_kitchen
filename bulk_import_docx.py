import docx
import os
import sqlite3
import json
import re
import asyncio
import sys
import shutil

sys.stdout.reconfigure(encoding='utf-8')
from bot.database.db import db

def estimate_time(title, ingredients, steps):
    title_lower = title.lower()
    steps_lower = steps.lower()
    if "хумус" in title_lower or "2 часа" in steps_lower: return 130, "long"
    if "запекать" in steps_lower or "духовку" in steps_lower: return 45, "medium"
    if "варить" in steps_lower or "тушить" in steps_lower: return 30, "medium"
    return 15, "quick"

def parse_time(text):
    match = re.search(r'(\d+)(?:-(\d+))?\s*(минут|мин|часа|час)', text, re.I)
    return int(match.group(1)) * (60 if 'час' in match.group(3).lower() else 1) if match else None

async def process_docx(file_path):
    category_name = os.path.basename(file_path).replace(".docx", "").replace("_copy", "")
    if category_name.lower() == "каши": category_name = "Каши"
    
    doc = docx.Document(file_path)
    full_text = "\n".join([p.text for p in doc.paragraphs])
    
    blocks = re.split(r'Ингредиенты:', full_text)
    
    recipes = []
    for i in range(1, len(blocks)):
        prev_block = blocks[i-1]
        curr_block = blocks[i]
        
        prev_lines = [l.strip() for l in prev_block.split('\n') if l.strip()]
        title = "Рецепт без названия"
        cook_time = None
        
        if prev_lines:
            for line in reversed(prev_lines):
                t = parse_time(line)
                if t and len(line) < 30:
                    cook_time = t
                    continue
                if "Приготовление" in line or "Способ приготовления" in line:
                    continue
                # If the line is too long, it's likely a description, skip it and look further up
                if len(line) > 100:
                    continue
                title = line
                break
        
        parts = re.split(r'Приготовление:|Способ приготовления:', curr_block)
        ingredients = parts[0].strip()
        steps = parts[1].strip() if len(parts) > 1 else ""
        
        recipes.append({
            "title": title,
            "ingredients": ingredients,
            "steps": steps,
            "category": category_name,
            "cook_time": cook_time
        })
        
    return recipes

async def main():
    folder = r"c:\Users\nidy9\OneDrive\Документы"
    target_files = [
        "Блюда из овощей.docx", "Блюда из печени и сердца.docx", "Брускеты и закуски.docx",
        "Гарниры.docx", "Десерты.docx", "Завтраки из яиц.docx", "Запеканки.docx",
        "каши.docx", "Мясо.docx", "Напитки.docx", "Оладушки и и блины.docx",
        "Рыба.docx", "Салаты.docx", "Супы.docx", "Творог и молочка.docx"
    ]
    
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recipes WHERE id >= 12")
    conn.commit()
    conn.close()
    print("Database cleaned. Re-importing...")

    total_added = 0
    for filename in target_files:
        original_path = os.path.join(folder, filename)
        if not os.path.exists(original_path):
            print(f"File not found: {filename}")
            continue
            
        copy_path = filename.replace(".docx", "_copy.docx")
        try:
            shutil.copy2(original_path, copy_path)
            recipes = await process_docx(copy_path)
            for r in recipes:
                r['ingredients'] = r['ingredients'].replace("●", "\n—").replace("•", "\n—").strip()
                if r['ingredients'].startswith("\n"): r['ingredients'] = r['ingredients'][1:]
                if r['ingredients'] and not r['ingredients'].startswith("—"): r['ingredients'] = "— " + r['ingredients']
                r['steps'] = re.sub(r'(\d+\.)', r'\n\1', r['steps']).strip()
                if r['title'].startswith(("—", "●", "•")): r['title'] = r['title'][1:].strip()
                
                if not r.get('cook_time'):
                    r['cook_time'], r['time_category'] = estimate_time(r['title'], r['ingredients'], r['steps'])
                else:
                    r['time_category'] = "quick" if r['cook_time'] <= 15 else ("medium" if r['cook_time'] <= 45 else "long")
                
                r['photo_id'] = None
                r['about'] = r['tips'] = r['serving'] = r['substitutions'] = ""
                r['tags'] = []
                await db.add_recipe(r)
                total_added += 1
                print(f"  [{r['category']}] Added: {r['title']}")
            os.remove(copy_path)
        except Exception as e:
            print(f"  Error processing {filename}: {e}")
            if os.path.exists(copy_path): os.remove(copy_path)

    print(f"\nSuccessfully imported {total_added} recipes.")

if __name__ == "__main__":
    asyncio.run(main())
