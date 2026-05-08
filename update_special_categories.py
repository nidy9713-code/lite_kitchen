import asyncio
import sqlite3
import json

async def update_special_tags():
    conn = sqlite3.connect("recipes.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM recipes")
    recipes = cursor.fetchall()
    
    # Special categories from the image
    # "👶 Для детей", "👨‍👩‍👧 Для всей семьи", "🌿 Без глютена", "🥛 Без молока", "🥚 Без яиц", "⚡️ Быстрые рецепты", "💚 Лёгкие блюда"
    
    for r in recipes:
        tags = []
        try:
            if r['tags']:
                tags = json.loads(r['tags'])
                if not isinstance(tags, list):
                    tags = [tags]
        except:
            tags = []
            
        title = r['title'].lower()
        ingredients = r['ingredients'].lower() if r['ingredients'] else ""
        cook_time = r['cook_time'] if r['cook_time'] else 0
        category = r['category']
        about = r['about'].lower() if r['about'] else ""
        
        # 1. ⚡️ Быстрые рецепты (Fast recipes) - under 20 mins
        if cook_time > 0 and cook_time <= 20:
            if "⚡️ Быстрые рецепты" not in tags:
                tags.append("⚡️ Быстрые рецепты")
                
        # 2. 👶 Для детей (For kids)
        kids_keywords = ['детск', 'малоеж', 'ребен', 'ребёнк', 'для детей']
        if any(kw in title or kw in about for kw in kids_keywords) or category == 'Смузи для детей':
            if "👶 Для детей" not in tags:
                tags.append("👶 Для детей")
                
        # 3. 🌿 Без глютена (Gluten-free)
        gluten_ingredients = ['пшенич', 'мука в/с', 'макарон', 'булгур', 'манная', 'овсян']
        # This is a bit tricky, let's look for GF alternatives or absence of gluten
        if 'рисовая мука' in ingredients or 'миндальная мука' in ingredients or 'безглютен' in ingredients or 'киноа' in ingredients or 'гречка' in ingredients:
            if not any(kw in ingredients for kw in ['пшенич', 'ржан']):
                if "🌿 Без глютена" not in tags:
                    tags.append("🌿 Без глютена")
        
        # 4. 🥛 Без молока (Dairy-free)
        milk_ingredients = ['молок', 'сливк', 'сметан', 'творог', 'сыр', 'йогурт']
        if not any(kw in ingredients for kw in milk_ingredients) or 'кокосовое молок' in ingredients:
            if "🥛 Без молока" not in tags:
                tags.append("🥛 Без молока")
                
        # 5. 🥚 Без яиц (Egg-free)
        if 'яйц' not in ingredients and 'яич' not in ingredients:
            if "🥚 Без яиц" not in tags:
                tags.append("🥚 Без яиц")
                
        # 6. 💚 Лёгкие блюда (Light dishes)
        light_categories = ['Салаты', 'Блюда из овощей', 'Напитки', 'Смузи для детей']
        if category in light_categories or 'салат' in title or 'овощ' in title:
            if "💚 Лёгкие блюда" not in tags:
                tags.append("💚 Лёгкие блюда")
                
        # 7. 👨‍👩‍👧 Для всей семьи (For the whole family)
        # Almost everything fits, but let's prioritize main courses
        if category in ['Мясо', 'Рыба', 'Супы', 'Гарниры']:
            if "👨‍👩‍👧 Для всей семьи" not in tags:
                tags.append("👨‍👩‍👧 Для всей семьи")

        # Update the recipe with new tags
        cursor.execute("UPDATE recipes SET tags = ? WHERE id = ?", (json.dumps(tags, ensure_ascii=False), r['id']))
        
    conn.commit()
    print("Special categories (tags) updated successfully!")
    conn.close()

if __name__ == "__main__":
    asyncio.run(update_special_tags())
