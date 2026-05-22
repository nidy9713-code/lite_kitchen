import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Union

from aiogram import Bot
from zoneinfo import ZoneInfo

from config import is_admin

MSK = ZoneInfo("Europe/Moscow")


def _msk_hour() -> int:
    return datetime.now(MSK).hour


def _is_quiet_hours_msk() -> bool:
    h = _msk_hour()
    return h >= 19 or h < 9


async def schedule_recipe_notification(bot: Optional[Union[Bot, List[Bot]]], recipe_data: dict, db):
    """
    Уведомление о новом рецепте: с 09:00 до 19:00 МСК — сразу (если передан bot),
    иначе запись в очередь на утреннюю рассылку.
    Добавление через скрипт без bot — в очередь, чтобы уведомление не терялось.
    """
    title = recipe_data.get("title", "Новый рецепт")
    category = recipe_data.get("category", "Разное")

    if _is_quiet_hours_msk() or bot is None:
        logging.info(
            "Откладываем уведомление для '%s' (МСК %02d:xx, bot=%s)",
            title,
            _msk_hour(),
            "есть" if bot is not None else "нет",
        )
        await db.add_pending_notification(title, category)
        return 0

    return await send_broadcast(bot, title, category, db)


async def announce_new_recipe(bot: Union[Bot, List[Bot]], recipe_data: dict, db):
    """Совместимость: то же, что schedule_recipe_notification с bot."""
    return await schedule_recipe_notification(bot, recipe_data, db)


async def send_broadcast(bot: Union[Bot, List[Bot]], title: str, category: str, db) -> int:
    user_ids = await db.get_all_user_ids()
    if not user_ids:
        logging.warning(
            "Рассылка '%s': в таблице users нет ни одного user_id — сообщения не отправлены",
            title,
        )

    text = (
        f"🔔 <b>У нас новый рецепт!</b>\n\n"
        f"🍽 <b>{title}</b>\n"
        f"Раздел: {category}\n\n"
        f"Загляните в бота, чтобы посмотреть подробности! ✨"
    )

    bots = [bot] if isinstance(bot, Bot) else bot
    count = 0
    for uid in user_ids:
        # Try each bot until one succeeds
        sent = False
        for b in bots:
            try:
                await b.send_message(
                    uid, text, parse_mode="HTML", protect_content=not is_admin(uid)
                )
                count += 1
                sent = True
                break # Success, move to next user
            except Exception:
                continue
        
        if sent:
            await asyncio.sleep(0.05)
            
    return count


async def check_and_send_delayed_notifications(bot: Union[Bot, List[Bot]], db):
    """
    Отправка накопившихся уведомлений (cron в 09:00 МСК и догон при старте в окне 09–19 МСК).
    Удаляем из очереди только те записи, по которым удалось отправить хотя бы одно сообщение.
    """
    try:
        pending = await db.get_pending_notifications()
        if not pending:
            return

        logging.info("Отложенные уведомления: %s записей в очереди", len(pending))

        for item in pending:
            title = item.get("title", "Новый рецепт")
            category = item.get("category", "Разное")
            nid = item.get("id")
            sent = await send_broadcast(bot, title, category, db)
            if sent > 0 and nid is not None:
                await db.delete_pending_notification(nid)
                logging.info(
                    "Отложенное уведомление отправлено (%s получателей), id=%s удалён из очереди",
                    sent,
                    nid,
                )
            else:
                logging.warning(
                    "Отложенное уведомление не отправлено ни одному пользователю "
                    "(title=%r, id=%s) — запись остаётся в очереди для повторной попытки",
                    title,
                    nid,
                )
    except Exception:
        logging.exception("Ошибка при обработке отложенных уведомлений")
