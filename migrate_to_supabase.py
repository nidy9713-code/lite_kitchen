import sqlite3
import json
import asyncio
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

# This script migrates data from SQLite to Supabase
# IMPORTANT: Run this only AFTER creating the tables in Supabase SQL Editor

async def migrate():
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Connect to SQLite
    conn = sqlite3.connect('recipes.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Migrate Users
    print("Migrating users...")
    cursor.execute("SELECT * FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    if users:
        supabase.table("users").upsert(users).execute()
        print(f"Migrated {len(users)} users.")
    
    # 2. Migrate Recipes
    print("Migrating recipes...")
    cursor.execute("SELECT * FROM recipes")
    recipes = [dict(row) for row in cursor.fetchall()]
    if recipes:
        # PostgreSQL doesn't like auto-incrementing IDs being sent manually if not handled
        # But upsert should handle it if 'id' is provided
        supabase.table("recipes").upsert(recipes).execute()
        print(f"Migrated {len(recipes)} recipes.")
        
    # 3. Migrate Constructors
    print("Migrating constructors...")
    cursor.execute("SELECT * FROM constructors")
    constructors = [dict(row) for row in cursor.fetchall()]
    if constructors:
        supabase.table("constructors").upsert(constructors).execute()
        print(f"Migrated {len(constructors)} constructors.")
        
    # 4. Migrate Settings
    print("Migrating settings...")
    cursor.execute("SELECT * FROM settings")
    settings = [dict(row) for row in cursor.fetchall()]
    if settings:
        supabase.table("settings").upsert(settings).execute()
        print(f"Migrated {len(settings)} settings.")
        
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
