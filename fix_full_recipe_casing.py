import asyncio
import sqlite3
import re

def fix_text_casing(text):
    if not text or not isinstance(text, str):
        return text
    text = text.strip()
    if not text:
        return text
    
    # Special handling for lists (ingredients or steps)
    lines = text.split('\n')
    fixed_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            fixed_lines.append("")
            continue
            
        # Check if it starts with a bullet or number
        bullet_match = re.match(r'^([—•●*]|\d+\.)\s*(.*)', line)
        if bullet_match:
            bullet = bullet_match.group(1)
            content = bullet_match.group(2).strip()
            if content:
                fixed_content = content[0].upper() + content[1:].lower()
                fixed_lines.append(f"{bullet} {fixed_content}")
            else:
                fixed_lines.append(bullet)
        else:
            # Regular line
            fixed_lines.append(line[0].upper() + line[1:].lower())
            
    return '\n'.join(fixed_lines)

async def fix_full_recipes_casing():
    conn = sqlite3.connect("recipes.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM recipes")
    recipes = cursor.fetchall()
    
    print(f"Processing {len(recipes)} recipes for full casing fix...")
    
    fields_to_fix = ['ingredients', 'steps', 'tips', 'serving', 'substitutions']
    
    for r in recipes:
        updates = {}
        for field in fields_to_fix:
            original = r[field]
            fixed = fix_text_casing(original)
            if fixed != original:
                updates[field] = fixed
        
        if updates:
            set_clause = ", ".join([f"{field} = ?" for field in updates.keys()])
            values = list(updates.values()) + [r['id']]
            cursor.execute(f"UPDATE recipes SET {set_clause} WHERE id = ?", values)
            
    conn.commit()
    print("Full recipe casing fixed successfully!")
    conn.close()

if __name__ == "__main__":
    asyncio.run(fix_full_recipes_casing())
