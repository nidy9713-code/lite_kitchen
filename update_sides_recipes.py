import asyncio
import json
from bot.database.db import db

async def update_sides_recipes():
    # 1. Add missing recipes
    missing_recipes = [
        {
            "title": "Картофельное пюре",
            "about": "Классический гарнир",
            "ingredients": "картофель\nмасло\nмолоко",
            "steps": "1. Очистить картофель\n2. Сварить\n3. Размять с маслом и молоком",
            "tips": "",
            "serving": "",
            "substitutions": "",
            "time_category": "quick",
            "cook_time": 25,
            "category": "Гарниры",
            "tags": [],
            "meal_type": "Обед"
        },
        {
            "title": "Запеченные овощи",
            "about": "Простой и полезный гарнир",
            "ingredients": "овощи\nмасло\nспеции",
            "steps": "1. Нарезать овощи\n2. Добавить масло и специи\n3. Запекать 30–35 минут",
            "tips": "",
            "serving": "",
            "substitutions": "",
            "time_category": "medium",
            "cook_time": 35,
            "category": "Гарниры",
            "tags": [],
            "meal_type": "Обед"
        }
    ]
    
    for r in missing_recipes:
        print(f"Adding: {r['title']}")
        await db.add_recipe(r)

    # 2. Update existing recipes metadata to match user list
    # ID 622: Стейки из капусты
    # ID 623: Волшебная гречка...
    
    updates = [
        {
            "id": 622,
            "data": {
                "about": "Запеченная капуста с хрустящей корочкой",
                "time_category": "medium",
                "cook_time": 30
            }
        },
        {
            "id": 623,
            "data": {
                "title": "Волшебная гречка",
                "about": "Смесь круп с насыщенным вкусом",
                "time_category": "quick",
                "cook_time": 20
            }
        }
    ]

    for update in updates:
        print(f"Updating ID {update['id']}: {update['data'].get('title', 'Existing Title')}")
        existing = await db.get_recipe_by_id(update['id'])
        if existing:
            merged_data = {**existing, **update['data']}
            if isinstance(merged_data.get('tags'), str):
                try:
                    merged_data['tags'] = json.loads(merged_data['tags'])
                except:
                    merged_data['tags'] = []
            await db.update_recipe(update['id'], merged_data)

if __name__ == "__main__":
    asyncio.run(update_sides_recipes())
