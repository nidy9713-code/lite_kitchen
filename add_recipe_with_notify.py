import asyncio
from bot.database.db import db
from aiogram import Bot
from config import TOKENS

async def add_single_recipe():
    # Пример данных рецепта
    new_recipe = {
        "title": "Тестовый рецепт из Cursor",
        "about": "Этот рецепт был добавлен через Cursor с автоматической рассылкой.",
        "ingredients": "— Ингредиент 1\n— Ингредиент 2",
        "steps": "1. Шаг 1\n2. Шаг 2",
        "category": "Мясо",
        "time_category": "quick",
        "cook_time": 20,
        "tags": ["для всей семьи"]
    }
    
    # Инициализируем бота для рассылки
    bot = Bot(token=TOKENS[0])
    
    # Добавляем рецепт (рассылка произойдет автоматически, так как передан bot)
    recipe_id = await db.add_recipe(new_recipe, bot=bot)
    
    await bot.session.close()
    print(f"Рецепт добавлен с ID: {recipe_id} и разослан пользователям.")

if __name__ == "__main__":
    asyncio.run(add_single_recipe())
