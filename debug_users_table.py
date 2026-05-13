import asyncio
from bot.database.db import db

async def debug_users():
    try:
        res = db.supabase.table("users").select("*").limit(1).execute()
        if res.data:
            print("Columns in 'users' table:", res.data[0].keys())
        else:
            print("'users' table is empty.")
    except Exception as e:
        print(f"Error accessing 'users' table: {e}")

if __name__ == "__main__":
    asyncio.run(debug_users())
