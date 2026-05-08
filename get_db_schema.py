import sqlite3
import json

def get_schema():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
    
    schema = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        schema[table] = cursor.fetchall()
        
    print(json.dumps(schema, indent=2, ensure_ascii=False))
    conn.close()

if __name__ == "__main__":
    get_schema()
