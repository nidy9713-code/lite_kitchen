import asyncio
from bot.database.db import db

async def check_users():
    print("Checking users in Supabase...")
    res = db.supabase.table("users").select("*").execute()
    print(f"Found {len(res.data)} users:")
    for u in res.data:
        print(u)

if __name__ == "__main__":
    asyncio.run(check_users())
