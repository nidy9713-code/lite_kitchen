import asyncio
import logging
from datetime import datetime
from aiogram import Bot
from config import is_admin

async def announce_new_recipe(bot: Bot, recipe_data: dict, db):
    """
    Рассылает уведомление о новом рецепте всем пользователям из базы данных.
    Если время после 19:00 или до 09:00, откладывает рассылку.
    """
    title = recipe_data.get('title', 'Новый рецепт')
    category = recipe_data.get('category', 'Разное')
    
    # Проверка времени (по МСК, считаем что сервер в UTC или МСК)
    # Для Amvera (обычно UTC) добавляем 3 часа для МСК
    current_hour = (datetime.now().hour + 3) % 24
    
    if current_hour >= 19 or current_hour < 9:
        logging.info(f"Откладываем уведомление для '{title}' (время: {current_hour}:00)")
        await db.add_pending_notification(title, category)
        return 0
        
    return await send_broadcast(bot, title, category, db)

async def send_broadcast(bot: Bot, title: str, category: str, db):
    user_ids = await db.get_all_user_ids()
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
            await asyncio.sleep(0.05)
        except Exception as e:
            logging.debug(f"Не удалось отправить сообщение пользователю {uid}: {e}")
            continue
            
    return count

async def check_and_send_delayed_notifications(bot: Bot, db):
    """
    Проверяет наличие отложенных уведомлений и отправляет их.
    """
    pending = await db.get_pending_notifications()
    if not pending:
        return
        
    logging.info(f"Отправка {len(pending)} отложенных уведомлений...")
    
    for item in pending:
        await send_broadcast(bot, item['title'], item['category'], db)
        
    await db.clear_pending_notifications()
