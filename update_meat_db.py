import asyncio
import json
from bot.database.db import db

async def update_meat_recipes():
    # 1. Recipes to add (completely missing)
    to_add = [
        {
            "title": "Фаршированные перцы с курицей",
            "about": "Сытное запеченное блюдо с курицей и овощами",
            "ingredients": "филе куриного бедра — 500 г\nболгарские перцы — 5 шт\nпомидоры — 2 шт\nсыр чеддер — 200 г\nсметана — 1 ст.л.\nсоль, перец — по вкусу",
            "steps": "1. Разогреть духовку до 180°C\n2. Подготовить перцы\n3. Нарезать курицу и овощи\n4. Смешать с сыром и сметаной\n5. Начинить перцы\n6. Запекать 30–40 минут",
            "time_category": "medium",
            "cook_time": 45,
            "category": "Мясо",
            "meal_type": "Обед"
        },
        {
            "title": "Куриная грудка с баклажанами",
            "about": "Легкое блюдо с овощами",
            "ingredients": "куриное филе — 300 г\nбаклажан — 1 шт\nперец — 1/2\nпомидор — 1 шт\nлук\nмасло гхи\nспеции",
            "steps": "1. Обжарить курицу 5–7 минут\n2. Нарезать овощи\n3. Обжарить овощи 10 минут\n4. Добавить курицу и помидоры\n5. Тушить 5 минут",
            "time_category": "quick",
            "cook_time": 25,
            "category": "Мясо",
            "meal_type": "Обед"
        },
        {
            "title": "Рагу из индейки с фасолью",
            "about": "Сытное овощное рагу с индейкой",
            "ingredients": "индейка — 300 г\nфасоль — 200 г\nлук\nморковь\nцукини\nброкколи\nтоматная паста",
            "steps": "1. Обжарить лук и чеснок\n2. Добавить индейку\n3. Добавить овощи\n4. Добавить фасоль и воду\n5. Тушить до готовности",
            "time_category": "medium",
            "cook_time": 40,
            "category": "Мясо",
            "meal_type": "Обед"
        },
        {
            "title": "Котлеты с цукини",
            "about": "Сочные котлеты с овощами",
            "ingredients": "говяжий фарш — 500 г\nцукини — 2 шт\nлук\nчеснок\nяйца — 3 шт\nминдальная мука",
            "steps": "1. Измельчить овощи\n2. Смешать с фаршем\n3. Сформировать котлеты\n4. Обжарить",
            "time_category": "medium",
            "cook_time": 30,
            "category": "Мясо",
            "meal_type": "Обед"
        },
        {
            "title": "Говядина с грибами",
            "about": "Тушеное мясо с овощами",
            "ingredients": "говядина — 500 г\nшампиньоны — 500 г\nморковь\nлук\nперец\nчеснок",
            "steps": "1. Обжарить мясо\n2. Добавить овощи\n3. Добавить грибы\n4. Тушить до готовности",
            "time_category": "medium",
            "cook_time": 50,
            "category": "Мясо",
            "meal_type": "Обед"
        },
        {
            "title": "Гречка по-купечески с говядиной",
            "about": "Сытное блюдо с крупой и мясом",
            "ingredients": "гречка — 200 г\nговядина — 300 г\nморковь\nлук\nчеснок\nтоматная паста",
            "steps": "1. Промыть гречку\n2. Обжарить овощи\n3. Добавить мясо\n4. Тушить 30 минут\n5. Добавить гречку\n6. Готовить 15 минут",
            "time_category": "long",
            "cook_time": 60,
            "category": "Мясо",
            "meal_type": "Обед"
        }
    ]

    for r in to_add:
        print(f"Adding: {r['title']}")
        await db.add_recipe(r)

    # 2. Existing recipes to update (merging metadata)
    updates = [
        {"id": 641, "data": {"about": "Питательное блюдо с белком", "time_category": "medium", "cook_time": 30}},
        {"id": 642, "data": {"title": "Болоньезе домашнее", "about": "Классический соус с фаршем", "time_category": "quick", "cook_time": 20}},
        {"id": 643, "data": {"about": "Простая версия классического блюда", "time_category": "long", "cook_time": 60}},
        {"id": 644, "data": {"about": "Легкая версия лазаньи", "time_category": "long", "cook_time": 60}},
        {"id": 645, "data": {"about": "Запеченное блюдо с крупой", "time_category": "medium", "cook_time": 50}}
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
    asyncio.run(update_meat_recipes())
