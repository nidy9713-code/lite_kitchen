"""Проверка таблицы favorites в Supabase. Запуск: py verify_favorites_table.py"""
import asyncio

from bot.database.db import db


async def main():
    try:
        response = db.supabase.table("favorites").select("user_id").limit(1).execute()
        print("OK: таблица favorites доступна.")
        print(f"Записей (выборка): {len(response.data or [])}")
    except Exception as e:
        print("ОШИБКА: таблица favorites недоступна.")
        print(f"Детали: {e}")
        print()
        print("Выполните SQL из migrations/create_favorites_table.sql в Supabase SQL Editor.")


if __name__ == "__main__":
    asyncio.run(main())
