from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from bot.database.db import db
from config import is_admin

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
            
        # Check if user has access in DB
        user = await db.get_user(user_id)
        
        # If user doesn't exist or doesn't have access
        if not user or not user.get('has_access'):
            # Allow /start command to process invite links
            if isinstance(event, Message) and event.text and event.text.startswith('/start'):
                return await handler(event, data)
                
            # Otherwise, block and show message
            text = (
                "⚠️ <b>Доступ ограничен</b>\n\n"
                "Этот бот является закрытым. Доступ предоставляется только по специальной ссылке администратора.\n\n"
                "Если вы приобрели доступ, пожалуйста, воспользуйтесь ссылкой, которую вам прислали."
            )
            if isinstance(event, Message):
                await event.answer(text, parse_mode="HTML")
            elif isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            return
            
        return await handler(event, data)
