import asyncio
import json
from bot.database.db import db

async def update_drinks_recipes():
    # 1. Recipes to add (completely missing)
    to_add = [
        {
            "title": "Броне какао",
            "about": "Сытный напиток с полезными жирами и насыщенным шоколадным вкусом",
            "ingredients": "кокосовое молоко — 200 мл\nкокосовое масло — 1 ст.л.\nмасло гхи — 1 ст.л.\nкакао-порошок — 2 ст.л.\nкорица — 1/2 ч.л.",
            "steps": "1. Нагреть кокосовое молоко до кипения\n2. Снять с огня\n3. Добавить масла\n4. Добавить какао и корицу\n5. Взбить блендером до однородности",
            "tips": "Лучше взбивать для кремовой текстуры",
            "serving": "подавать горячим",
            "substitutions": "",
            "time_category": "quick",
            "cook_time": 5,
            "category": "Напитки",
            "meal_type": "Напиток"
        },
        {
            "title": "Зеленый смузи",
            "about": "Питательный смузи с зеленью и суперфудами",
            "ingredients": "шпинат — 2 чашки\nвода — 1 стакан\nкокосовое молоко — 1/2 стакана\nпаприка — 1/2 чашки\nльняные семена — 1 ст.л.\nспирулина — 1 ч.л.\nсемена шалфея — по желанию",
            "steps": "1. Замочить шпинат\n2. Промыть\n3. Смешать все ингредиенты\n4. Взбить\n5. Отрегулировать консистенцию",
            "tips": "Можно добавить фрукты для сладости",
            "serving": "подавать сразу",
            "substitutions": "",
            "time_category": "quick",
            "cook_time": 10,
            "category": "Напитки",
            "tags": ["смузи"],
            "meal_type": "Напиток"
        }
    ]

    for r in to_add:
        print(f"Adding: {r['title']}")
        await db.add_recipe(r)

    # 2. Existing recipes to update (merging metadata)
    updates = [
        {
            "id": 698, 
            "data": {
                "about": "Освежающий напиток-десерт с чиа и лимоном",
                "ingredients": "цедра лимона — 2 шт\nсок лимона — 2 шт\nкокосовое молоко — 1.5 чашки\nвода — 1/4 стакана\nподсластитель — по вкусу\nсоль — щепотка\nкуркума — 1/4 ч.л.\nсемена чиа — 3 ст.л.",
                "steps": "1. Смешать жидкие ингредиенты\n2. Добавить чиа\n3. Взбить\n4. Разлить по стаканам\n5. Оставить в холодильнике на ночь",
                "tips": "Можно украсить кокосовым кремом",
                "serving": "подавать охлажденным",
                "substitutions": "кокосовое молоко → любое растительное",
                "time_category": "long",
                "cook_time": 10
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
    asyncio.run(update_drinks_recipes())
