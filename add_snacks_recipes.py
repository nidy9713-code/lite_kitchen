import asyncio
import json
from bot.database.db import db

async def add_snacks_recipes():
    snacks_to_add = [
        {
            "title": "Брускетта из киноа и авокадо",
            "about": "Полезная альтернатива хлебным закускам",
            "ingredients": "киноа\nавокадо\nтоматы\nзелень\nлимонный сок",
            "steps": "1. Отварить киноа\n2. Нарезать авокадо и томаты\n3. Смешать ингредиенты\n4. Выложить на основу",
            "tips": "",
            "serving": "подавать свежим",
            "substitutions": "",
            "time_category": "quick",
            "cook_time": 25,
            "category": "Брускеты и закуски",
            "tags": [],
            "meal_type": "Закуска"
        },
        {
            "title": "Ролл с индейкой",
            "about": "Легкий перекус",
            "ingredients": "лаваш\nиндейка\nовощи\nсоус",
            "steps": "1. Подготовить ингредиенты\n2. Выложить на лаваш\n3. Свернуть ролл",
            "tips": "",
            "serving": "",
            "substitutions": "",
            "time_category": "quick",
            "cook_time": 10,
            "category": "Брускеты и закуски",
            "tags": [],
            "meal_type": "Закуска"
        },
        {
            "title": "Тост с хумусом",
            "about": "Быстрая закуска",
            "ingredients": "хлеб\nхумус\nовощи",
            "steps": "1. Поджарить хлеб\n2. Намазать хумус\n3. Добавить овощи",
            "tips": "",
            "serving": "",
            "substitutions": "",
            "time_category": "quick",
            "cook_time": 10,
            "category": "Брускеты и закуски",
            "tags": [],
            "meal_type": "Закуска"
        },
        {
            "title": "Хумус",
            "about": "Классическая нутовая паста",
            "ingredients": "нут\nтахини\nоливковое масло\nлимонный сок\nчеснок",
            "steps": "1. Замочить нут на ночь\n2. Отварить до мягкости\n3. Измельчить с остальными ингредиентами",
            "tips": "",
            "serving": "",
            "substitutions": "",
            "time_category": "long",
            "cook_time": 90,
            "category": "Брускеты и закуски",
            "tags": [],
            "meal_type": "Закуска"
        }
    ]
    
    for r in snacks_to_add:
        print(f"Adding: {r['title']}")
        await db.add_recipe(r)

if __name__ == "__main__":
    asyncio.run(add_snacks_recipes())
