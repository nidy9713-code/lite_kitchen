import sqlite3
import json

def update_tags():
    conn = sqlite3.connect('recipes.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, ingredients, cook_time, category, tags FROM recipes")
    recipes = cursor.fetchall()
    
    for r in recipes:
        # Load existing tags
        existing_tags = []
        if r['tags']:
            try:
                existing_tags = json.loads(r['tags'])
            except:
                existing_tags = [t.strip() for t in r['tags'].split('\n') if t.strip()]
        
        new_tags = set(existing_tags)
        
        title = r['title'].lower()
        ingredients = r['ingredients'].lower() if r['ingredients'] else ""
        category = r['category'].lower() if r['category'] else ""
        cook_time = r['cook_time'] if r['cook_time'] else 999
        
        # 👶 Для детей
        kids_keywords = ["для детей", "детск", "малыш", "kids", "ребенок", "ребёнка"]
        if any(k in title or k in ingredients or k in category for k in kids_keywords) or "kids" in existing_tags:
            new_tags.add("👶 Для детей")
            
        # 👨‍👩‍👧 Для всей семьи
        family_keywords = ["семьи", "всей семье", "всем", "family"]
        if any(k in title or k in ingredients or k in category for k in family_keywords) or "family" in existing_tags or "👨‍👩‍👧 Для всей семьи" not in new_tags:
            # Almost everything is for the whole family unless specified otherwise
            new_tags.add("👨‍👩‍👧 Для всей семьи")
            
        # 🌿 Без глютена
        gluten_ingredients = ["мука пшеничная", "макароны", "спагетти", "хлеб", "батон", "манка", "кускус", "булгур", "перловка", "пшеница", "глютен", "тесто"]
        if not any(k in ingredients for k in gluten_ingredients):
            new_tags.add("🌿 Без глютена")
            
        # 🥛 Без молока
        dairy_ingredients = ["молоко", "сливки", "сметана", "творог", "сыр", "масло сливочное", "йогурт", "кефир"]
        if not any(k in ingredients for k in dairy_ingredients):
            new_tags.add("🥛 Без молока")
            
        # 🥚 Без яиц
        egg_ingredients = ["яйцо", "яйца", "желток", "белок яй"]
        if not any(k in ingredients for k in egg_ingredients):
            new_tags.add("🥚 Без яиц")
            
        # ⚡️ Быстрые рецепты
        if cook_time <= 20:
            new_tags.add("⚡️ Быстрые рецепты")
            
        # 💚 Лёгкие блюда
        light_categories = ["салаты", "блюда из овощей", "напитки"]
        if category in light_categories or "light" in existing_tags or "🥗 Лёгкое" in existing_tags:
            new_tags.add("💚 Лёгкие блюда")

        # Update DB
        cursor.execute("UPDATE recipes SET tags = ? WHERE id = ?", (json.dumps(list(new_tags), ensure_ascii=False), r['id']))
        
    conn.commit()
    conn.close()
    print("Tags updated successfully!")

if __name__ == "__main__":
    update_tags()
