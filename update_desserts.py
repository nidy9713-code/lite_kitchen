import asyncio
import json
from bot.database.db import db

async def update_desserts():
    # Recipes to add (not found in DB)
    to_add = [
        {
            "title": "Миндально-кокосовые батончики",
            "about": "Полезный десерт с ягодами и орехами",
            "ingredients": "миндаль — 75 г\nкокосовое масло — 1 ст.л.\nкокосовая стружка — 40 г\nзамороженные ягоды — 75 г\nэритрит — по вкусу\nкокосовое масло — 60 г\nшоколадная крошка — 180 г",
            "steps": "1. Смешать ягоды и миндаль в блендере\n2. Добавить эритрит и кокосовую стружку\n3. Выложить массу в форму\n4. Растопить масло и шоколад\n5. Залить глазурью\n6. Заморозить 30 минут\n7. Нарезать на кусочки",
            "time_category": "medium",
            "cook_time": 40,
            "category": "Десерты",
            "meal_type": "Десерт"
        },
        {
            "title": "Кокосовое печенье",
            "about": "Безглютеновое печенье с шоколадом",
            "ingredients": "кокосовая мука — 120 г\nэритрит — по вкусу\nсливочное масло — 170 г\nэкстракт ванили — 1 ч.л.\nсоль — щепотка\nкокосовое масло — 10 г\nшоколадная крошка — 90 г",
            "steps": "1. Разогреть духовку до 180°C\n2. Взбить масло и эритрит\n3. Добавить ваниль\n4. Вмешать муку и соль\n5. Сформировать печенье\n6. Выпекать 10–12 минут\n7. Остудить\n8. Покрыть шоколадом",
            "time_category": "medium",
            "cook_time": 30,
            "category": "Десерты",
            "meal_type": "Десерт"
        },
        {
            "title": "Шоколадный мусс",
            "about": "Нежный десерт с авокадо",
            "ingredients": "темный шоколад — 60 г\nавокадо — 1 шт\nкакао — 2 ст.л.\nмолоко — 3 ст.л.\nваниль — 1 ч.л.\nйогурт — 60 г\nэритрит — по вкусу",
            "steps": "1. Растопить шоколад\n2. Подготовить авокадо\n3. Взбить все ингредиенты\n4. Охладить 15 минут",
            "time_category": "quick",
            "cook_time": 20,
            "category": "Десерты",
            "meal_type": "Десерт"
        },
        {
            "title": "Миндальные блинчики",
            "about": "Полезные блинчики без глютена",
            "ingredients": "кокосовое молоко — 170 мл\nминдальная мука — 50 г\nяйца — 2 шт\nсахарозаменитель\nсоль\nоливковое масло — 30 мл",
            "steps": "1. Смешать яйца, соль и подсластитель\n2. Добавить молоко\n3. Вмешать муку\n4. Добавить масло\n5. Жарить блинчики",
            "time_category": "quick",
            "cook_time": 25,
            "category": "Оладушки и блины",
            "meal_type": "Завтрак"
        },
        {
            "title": "Маффины",
            "about": "Полезные кексы без сахара",
            "ingredients": "безглютеновая мука\nваниль\nразрыхлитель\nкорица\nурбеч\nфруктовое пюре\nоливковое масло",
            "steps": "1. Разогреть духовку\n2. Смешать сухие ингредиенты\n3. Взбить жидкие\n4. Соединить\n5. Выпекать 10–15 минут",
            "time_category": "quick",
            "cook_time": 25,
            "category": "Десерты",
            "meal_type": "Десерт"
        },
        {
            "title": "Пирожное мятное наслаждение",
            "about": "Десерт с мятным кремом",
            "ingredients": "орехи\nизюм\nкокосовая мука\nмята\nсироп топинамбура\nкокосовое молоко",
            "steps": "1. Подготовить корж\n2. Смешать ингредиенты крема\n3. Залить в форму\n4. Заморозить 2–3 часа",
            "time_category": "long",
            "cook_time": 180,
            "category": "Десерты",
            "meal_type": "Десерт"
        },
        {
            "title": "Тыквенный пирог",
            "about": "Нежный пирог с тыквой",
            "ingredients": "тыква\nсливки\nяйца\nмука\nкорица",
            "steps": "1. Сварить тыкву\n2. Сделать пюре\n3. Смешать с ингредиентами\n4. Выпекать 20–30 минут",
            "time_category": "medium",
            "cook_time": 50,
            "category": "Десерты",
            "meal_type": "Десерт"
        },
        {
            "title": "Морковная халва",
            "about": "Ароматный десерт с пряностями",
            "ingredients": "морковь\nгхи\nкокосовое молоко\nкардамон\nминдаль",
            "steps": "1. Обжарить морковь\n2. Добавить молоко и специи\n3. Варить до загустения",
            "time_category": "quick",
            "cook_time": 25,
            "category": "Десерты",
            "meal_type": "Десерт"
        },
        {
            "title": "Банановое мороженое",
            "about": "Натуральное мороженое",
            "ingredients": "банан\nкокосовое молоко",
            "steps": "1. Заморозить бананы\n2. Взбить\n3. Заморозить повторно",
            "time_category": "long",
            "cook_time": 240,
            "category": "Десерты",
            "meal_type": "Десерт"
        }
    ]

    for r in to_add:
        print(f"Adding: {r['title']}")
        await db.add_recipe(r)

    # Updates for existing recipes (merging data)
    # ID 699: Конфеты из семян, орехов и сухофруктов -> Конфеты из сухофруктов
    # ID 703: Запеченое яблоко -> Запеченные яблоки
    # ID 706: Банановый хлеб. -> Банановый хлеб
    
    updates = [
        {
            "id": 699,
            "data": {
                "title": "Конфеты из сухофруктов",
                "about": "Натуральные сладости",
                "time_category": "quick",
                "cook_time": 20
            }
        },
        {
            "id": 703,
            "data": {
                "title": "Запеченные яблоки",
                "about": "Простой полезный десерт",
                "time_category": "medium",
                "cook_time": 30,
                "tags": ["для детей"]
            }
        },
        {
            "id": 706,
            "data": {
                "title": "Банановый хлеб",
                "about": "Домашний кекс",
                "time_category": "medium",
                "cook_time": 45
            }
        }
    ]

    for update in updates:
        print(f"Updating ID {update['id']}: {update['data']['title']}")
        existing = await db.get_recipe_by_id(update['id'])
        if existing:
            # Merge: keep existing ingredients/steps if they are more detailed
            # In these cases, the user's list is a summary, so we keep DB's detail but update title/about/time
            merged_data = {**existing, **update['data']}
            if isinstance(merged_data.get('tags'), str):
                try:
                    merged_data['tags'] = json.loads(merged_data['tags'])
                except:
                    merged_data['tags'] = []
            await db.update_recipe(update['id'], merged_data)

if __name__ == "__main__":
    asyncio.run(update_desserts())
