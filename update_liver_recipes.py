import asyncio
import json
from bot.database.db import db

async def update_liver_recipes():
    # 1. Add missing recipe: Куриная печень с морковью и луком
    new_recipe = {
        "title": "Куриная печень с морковью и луком",
        "about": "Быстрое блюдо с высоким содержанием железа",
        "ingredients": "куриная печень — 600 г\nлук — 1 шт\nморковь — 2 шт\nмасло гхи — 1,5 ст. л.",
        "steps": "1. Обжарить лук и морковь\n2. Добавить печень\n3. Тушить 15 минут",
        "tips": "",
        "serving": "",
        "substitutions": "",
        "time_category": "quick",
        "cook_time": 20,
        "category": "Блюда из печени и сердца",
        "tags": [],
        "meal_type": "Обед"
    }
    
    print(f"Adding: {new_recipe['title']}")
    await db.add_recipe(new_recipe)

    # 2. Update existing recipes with better metadata
    # ID 617: Говяжье сердце с овощами.
    # ID 618: Печеночные оладьи.
    # ID 619: Тушеная капуста с куриными сердечками
    
    updates = [
        {
            "id": 617,
            "data": {
                "title": "Говяжье сердце с овощами",
                "about": "Питательное блюдо",
                "ingredients": "говяжье сердце\nморковь\nлук\nчеснок\nрепа",
                "steps": "1. Замочить сердце\n2. Обжарить\n3. Тушить 1,5–2 часа\n4. Добавить овощи",
                "time_category": "long",
                "cook_time": 120,
                "category": "Блюда из печени и сердца",
                "meal_type": "Обед"
            }
        },
        {
            "id": 618,
            "data": {
                "title": "Печеночные оладьи",
                "about": "Быстрое блюдо",
                "ingredients": "печень — 500 г\nяйца — 2 шт\nмука — 3 ст. л.\nморковь\nлук",
                "steps": "1. Измельчить печень\n2. Смешать ингредиенты\n3. Обжарить с двух сторон",
                "time_category": "quick",
                "cook_time": 25,
                "category": "Блюда из печени и сердца",
                "meal_type": "Обед"
            }
        },
        {
            "id": 619,
            "data": {
                "title": "Тушеная капуста с куриными сердечками",
                "about": "Сытное блюдо",
                "ingredients": "куриные сердечки\nкапуста\nморковь\nлук\nчеснок\nтоматная паста",
                "steps": "1. Подготовить сердечки\n2. Обжарить\n3. Добавить овощи\n4. Тушить 30–40 минут",
                "time_category": "medium",
                "cook_time": 45,
                "category": "Блюда из печени и сердца",
                "meal_type": "Обед"
            }
        }
    ]

    for update in updates:
        print(f"Updating ID {update['id']}: {update['data']['title']}")
        # We need to get the existing recipe to preserve photo_id and other fields not in the update
        existing = await db.get_recipe_by_id(update['id'])
        if existing:
            # Merge existing with new data
            merged_data = {**existing, **update['data']}
            # Ensure tags is a list for update_recipe (it expects a list, then json.dumps it)
            if isinstance(merged_data.get('tags'), str):
                try:
                    merged_data['tags'] = json.loads(merged_data['tags'])
                except:
                    merged_data['tags'] = []
            await db.update_recipe(update['id'], merged_data)

if __name__ == "__main__":
    asyncio.run(update_liver_recipes())
