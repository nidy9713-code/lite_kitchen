import asyncio
import logging
from aiogram import Bot

from config import is_admin

async def announce_new_recipe(bot: Bot, recipe_data: dict, db):
    """
    Рассылает уведомление о новом рецепте всем пользователям из базы данных.
    """
    user_ids = await db.get_all_user_ids()
    title = recipe_data.get('title', 'Новый рецепт')
    category = recipe_data.get('category', 'Разное')
    
    text = (
        f"🔔 <b>У нас новый рецепт!</b>\n\n"
        f"🍽 <b>{title}</b>\n"
        f"Раздел: {category}\n\n"
        f"Загляните в бота, чтобы посмотреть подробности! ✨"
    )
    
    count = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, text, parse_mode="HTML", protect_content=not is_admin(uid))
            count += 1
            # Задержка для обхода ограничений Telegram (около 30 сообщений в секунду)
            await asyncio.sleep(0.05)
        except Exception as e:
            logging.debug(f"Не удалось отправить сообщение пользователю {uid}: {e}")
            continue
            
    return count
