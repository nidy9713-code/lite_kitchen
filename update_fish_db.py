import asyncio
import json
from bot.database.db import db

async def update_fish_recipes():
    # 1. Recipes to add (completely missing or significantly different)
    to_add = [
        {
            "title": "Запеченная рыба с овощами и амарантом",
            "about": "Полезное блюдо с рыбой, овощами и гарниром из амаранта",
            "ingredients": "рыба — 600 г\nморковь — 3 шт\nлук — 1 шт\nцуккини — 500 г\nтоматы — 250 г\nмасло гхи — 1 ст.л.\nлимонный сок — 2 ч.л.\nамарант — 300 г\nспеции",
            "steps": "1. Замариновать рыбу с лимонным соком и специями.\n2. Нарезать овощи (морковь, лук, цуккини, томаты).\n3. Выложить овощи слоями в форму для запекания, сверху положить рыбу.\n4. Запекать 25 минут при 180°C.\n5. Отдельно отварить амарант и подавать вместе с рыбой и овощами.",
            "time_category": "medium",
            "cook_time": 35,
            "category": "Рыба",
            "meal_type": "Обед"
        },
        {
            "title": "Рыба на овощной подушке",
            "about": "Нежная рыба, приготовленная с овощами",
            "ingredients": "скумбрия — 500 г\nперец\nлук\nкабачок\nпомидоры\nтимьян\nмасло гхи",
            "steps": "1. Обжарить лук на масле гхи.\n2. Добавить нарезанные перец и кабачок.\n3. Сверху выложить ломтики помидоров.\n4. Положить рыбу на овощи, посыпать тимьяном.\n5. Тушить под крышкой 20–25 минут до готовности.",
            "time_category": "medium",
            "cook_time": 30,
            "category": "Рыба",
            "meal_type": "Обед"
        },
        {
            "title": "Запеченная скумбрия с салатом",
            "about": "Рыба с ароматными травами и свежим салатом",
            "ingredients": "скумбрия — 1 шт\nпомидоры — 500 г\nрозмарин\nтимьян\nмасло гхи",
            "steps": "1. Подготовить рыбу, натереть специями и травами.\n2. Добавить розмарин и тимьян внутрь рыбы.\n3. Выложить на противень, смазанный маслом гхи.\n4. Добавить немного воды на противень.\n5. Запекать 30–60 минут до готовности. Подавать с салатом из помидоров.",
            "time_category": "medium",
            "cook_time": 45,
            "category": "Рыба",
            "meal_type": "Обед"
        },
        {
            "title": "Рыбная пятиминутка",
            "about": "Быстрые рыбные оладьи для детей",
            "ingredients": "рыбное филе — 200 г\nкабачок\nлук\nморковь\nяйцо\nмука\nспеции",
            "steps": "1. Измельчить рыбное филе и овощи (кабачок, лук, морковь) в блендере или мелко нарезать.\n2. Добавить яйцо, муку и специи.\n3. Тщательно перемешать до однородности.\n4. Выкладывать массу ложкой на разогретую сковороду и жарить как оладьи с двух сторон.",
            "time_category": "quick",
            "cook_time": 20,
            "category": "Рыба",
            "tags": ["для детей"],
            "meal_type": "Обед"
        }
    ]

    for r in to_add:
        print(f"Adding: {r['title']}")
        await db.add_recipe(r)

    # 2. Existing recipes to update (merging metadata)
    updates = [
        {
            "id": 653, 
            "data": {
                "title": "Запеченный минтай с овощами",
                "about": "Легкое запеченное блюдо с овощами",
                "time_category": "medium",
                "cook_time": 40
            }
        },
        {
            "id": 654, 
            "data": {
                "title": "Скумбрия с рисом",
                "about": "Простое блюдо с рыбой и гарниром",
                "time_category": "medium",
                "cook_time": 40
            }
        },
        {
            "id": 655, 
            "data": {
                "about": "Запеченный лосось с овощами",
                "time_category": "medium",
                "cook_time": 30
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
    asyncio.run(update_fish_recipes())
