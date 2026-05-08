import asyncio
import json
from bot.database.db import db

async def update_pancakes_recipes():
    # 1. Recipe to add (completely missing)
    to_add = [
        {
            "title": "Чечевичные оладушки",
            "about": "Питательные оладьи с чечевицей и орехами",
            "ingredients": "красная чечевица — 1/4 стакана\nкешью — 1/4 стакана\nлимонный сок\nкокосовое масло\nкокосовая стружка — по желанию\nфиники — по желанию",
            "steps": "1. Замочить чечевицу и кешью на несколько часов.\n2. Измельчить все ингредиенты в блендере до однородности.\n3. Сформировать небольшие оладьи.\n4. Охладить в холодильнике (по желанию для лучшей формы).\n5. Запечь в духовке или обжарить на сковороде до золотистого цвета.",
            "tips": "Если масса получилась слишком жидкой — выкладывайте на сковороду ложкой.",
            "serving": "подавать с овощами или любимым соусом",
            "substitutions": "",
            "time_category": "medium",
            "cook_time": 25,
            "category": "Оладушки и блины",
            "meal_type": "Завтрак"
        }
    ]

    for r in to_add:
        print(f"Adding: {r['title']}")
        await db.add_recipe(r)

    # 2. Existing recipes to update (merging metadata)
    updates = [
        {
            "id": 646, 
            "data": {
                "about": "Нежные овощные оладьи с мягкой текстурой",
                "tips": "Можно не отжимать кабачок, но потребуется больше муки",
                "serving": "подавать со сметаной или йогуртом",
                "time_category": "quick",
                "cook_time": 15,
                "tags": ["для детей"]
            }
        },
        {
            "id": 647, 
            "data": {
                "about": "Овощные драники с насыщенным вкусом",
                "tips": "Можно использовать только желток",
                "serving": "подавать горячими",
                "time_category": "quick",
                "cook_time": 15
            }
        },
        {
            "id": 648, 
            "data": {
                "about": "Классические картофельные драники",
                "tips": "Можно экспериментировать с консистенцией",
                "serving": "подавать со сметаной",
                "time_category": "quick",
                "cook_time": 17
            }
        },
        {
            "id": 650, 
            "data": {
                "about": "Быстрые сладкие блинчики из банана",
                "tips": "Идеально для быстрого завтрака",
                "serving": "подавать с ягодами или йогуртом",
                "time_category": "quick",
                "cook_time": 5,
                "tags": ["для детей", "быстро"]
            }
        }
    ]

    for update in updates:
        print(f"Updating ID {update['id']}: {update['data'].get('title', 'Existing Title')}")
        existing = await db.get_recipe_by_id(update['id'])
        if existing:
            # Merge: keep existing ingredients/steps as they are usually more detailed in DB
            merged_data = {**existing, **update['data']}
            
            # Handle tags merging
            existing_tags = []
            if isinstance(existing.get('tags'), str):
                try:
                    existing_tags = json.loads(existing['tags'])
                except:
                    existing_tags = []
            elif isinstance(existing.get('tags'), list):
                existing_tags = existing['tags']
                
            new_tags = update['data'].get('tags', [])
            merged_tags = list(set(existing_tags + new_tags))
            merged_data['tags'] = merged_tags
            
            await db.update_recipe(update['id'], merged_data)

if __name__ == "__main__":
    asyncio.run(update_pancakes_recipes())
