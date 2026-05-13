import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from bot.database.db import db
from config import is_admin

# Simple in-memory cache for access status
# key: user_id, value: has_access (bool)
access_cache = {}

class AccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        # Admins always have access
        if is_admin(user_id):
            return await handler(event, data)
            
        # Check cache first
        if user_id in access_cache and access_cache[user_id]:
            return await handler(event, data)
            
        # Check if user has access in DB
        try:
            user = await db.get_user(user_id)
        except Exception as e:
            logging.error(f"Error fetching user {user_id} from DB: {e}")
            user = None
        
        # If user doesn't exist or doesn't have access
        has_access = user.get('has_access') if user else False
        
        # Update cache
        access_cache[user_id] = has_access
        
        if not has_access:
            # Allow /start command to process invite links
            if isinstance(event, Message) and event.text and event.text.startswith('/start'):
                return await handler(event, data)
                
            # Otherwise, block and show message
            text = (
                "⚠️ <b>Доступ ограничен</b>\n\n"
                "Этот бот является закрытым. Доступ предоставляется только по специальной ссылке администратора.\n\n"
                "Если вы приобрели доступ, пожалуйста, воспользуйтесь ссылкой, которую вам прислали."
            )
            
            try:
                if isinstance(event, Message):
                    await event.answer(text, parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    # For callback queries, we answer them to stop the loading spinner
                    try:
                        await event.answer("Доступ ограничен", show_alert=False)
                    except:
                        pass
                    
                    if event.message:
                        await event.message.answer(text, parse_mode="HTML")
                    else:
                        # Fallback if message is not available
                        logging.warning(f"CallbackQuery from user {user_id} has no message attached.")
            except Exception as e:
                logging.error(f"Error answering blocked event for user {user_id}: {e}")
                
            return
            
        return await handler(event, data)
