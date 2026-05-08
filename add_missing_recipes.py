import asyncio
import json
from bot.database.db import db

async def add_missing_recipes():
    recipes_to_add = [
        {
            "title": "Фаршированный перец с чечевицей",
            "about": "Полезное овощное блюдо с растительным белком",
            "ingredients": "болгарский перец — 2 шт\nчечевица — 50 г\nбурый рис — 25 г\nпомидор — 1 шт\nзелень — 100 г\nлук — 50 г\nчеснок — 1 зубчик\nсыр — 40 г\nмасло МСТ — 1 ст. л.\nспеции — по вкусу",
            "steps": "1. Отварить рис и чечевицу\n2. Обжарить лук, чеснок и помидоры\n3. Смешать все ингредиенты с зеленью\n4. Начинить перцы\n5. Посыпать сыром\n6. Запекать при 180°C 35 минут",
            "tips": "",
            "serving": "подавать горячим",
            "substitutions": "",
            "time_category": "medium",
            "cook_time": 45,
            "category": "Блюда из овощей",
            "tags": [],
            "meal_type": "Обед"
        },
        {
            "title": "Овощная запеканка",
            "about": "Сытная овощная запеканка",
            "ingredients": "бурый рис — 80 г\nкабачок — 250 г\nлук — 120 г\nморковь — 115 г\nсыр — 100 г\nсметана — 100 г\nяйца — 3 шт\nчеснок — 2 зубчика\nмасло гхи — 2 ст. л.",
            "steps": "1. Отварить рис\n2. Нарезать овощи\n3. Обжарить лук и морковь\n4. Смешать яйца, сметану и сыр\n5. Соединить все ингредиенты\n6. Запекать 40 минут при 180°C",
            "tips": "",
            "serving": "подавать теплой",
            "substitutions": "",
            "time_category": "medium",
            "cook_time": 50,
            "category": "Блюда из овощей",
            "tags": [],
            "meal_type": "Обед"
        }
    ]
    
    # Update existing recipe: Пицца из цветной капусты (ID 616)
    # We'll update it to match the provided data more closely if needed, 
    # but the provided data is actually a bit simpler than what's in DB.
    # Let's just add the missing ones for now.

    for r in recipes_to_add:
        print(f"Adding: {r['title']}")
        await db.add_recipe(r)

if __name__ == "__main__":
    asyncio.run(add_missing_recipes())
