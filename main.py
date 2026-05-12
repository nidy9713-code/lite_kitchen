import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.handlers import main_handlers
from bot.admin import handlers as admin_handlers
from bot.database.db import db
from bot.utils.access_middleware import AccessMiddleware
from config import TOKEN

# Вставьте ваш токен здесь

async def on_startup():
    # Проверка наличия рецептов, если база пуста - добавим пару демонстрационных
    recipes = await db.get_recipes_by_category("Все")
    if not recipes:
        print("База пуста, добавляю демо-рецепты...")
        demo_recipes = [
            {
                "title": "Сырники с курагой",
                "about": "Для здорового сердца и сосудов. Курага богата калием.",
                "ingredients": "— Творог (180 гр)\n— 1 банан\n— Курага (3-5 шт)\n— 1 яйцо\n— Мука (2-3 ст.л.)",
                "steps": "1. Залить курагу водой.\n2. Размять банан.\n3. Смешать все.\n4. Пожарить.",
                "tips": "Банан дает сладость.",
                "serving": "с ягодами или сметаной",
                "substitutions": "Курага -> изюм",
                "category": "Творог и молочка",
                "time_category": "quick",
                "cook_time": 15,
                "tags": ["hearty"]
            },
            {
                "title": "Омлет по-французски",
                "about": "Лайфхак для детей: кабачок совсем не чувствуется.",
                "ingredients": "— 2 яйца\n— Кабачок (тертый)\n— Масло ГХИ",
                "steps": "1. Растопить масло.\n2. Смешать яйца и кабачок.\n3. Пожарить.",
                "tips": "Вливайте горячее масло в яйца.",
                "serving": "со свежими овощами",
                "substitutions": "Кабачок -> шпинат",
                "category": "Завтраки из яиц",
                "time_category": "quick",
                "cook_time": 10,
                "tags": ["light", "kids"]
            }
        ]
        for r in demo_recipes:
            await db.add_recipe(r)

async def main() -> None:
    logging.info("Инициализация бота...")
    
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()

    # Регистрация мидлварей
    dp.message.middleware(AccessMiddleware())
    dp.callback_query.middleware(AccessMiddleware())

    # Регистрация роутеров
    dp.include_router(admin_handlers.router)
    dp.include_router(main_handlers.router)

    # Вызов инициализации данных
    await on_startup()

    # Удаление вебхука перед запуском
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот выключен")
    except Exception as e:
        print(f"Не удалось запустить бота: {e}")
