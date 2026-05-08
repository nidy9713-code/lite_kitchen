import asyncio
import sqlite3
import json

async def distribute_recipes():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    # 1. Categories that are clearly BREAKFAST
    breakfast_categories = ['Творог и молочка', 'Завтраки из яиц', 'Каши', 'Оладушки и блины', 'Смузи для детей']
    cursor.execute(f"UPDATE recipes SET meal_type = 'Завтрак' WHERE category IN ({','.join(['?']*len(breakfast_categories))})", breakfast_categories)
    
    # 2. Categories that are clearly LUNCH (Soups)
    cursor.execute("UPDATE recipes SET meal_type = 'Обед' WHERE category = 'Супы'")
    
    # 3. Categories that can be LUNCH or DINNER (Meat, Fish, Vegetables, Salads, Sides, Snacks)
    # We will distribute them to balance Lunch and Dinner
    
    # Let's get these recipes
    other_categories = ['Мясо', 'Рыба', 'Блюда из овощей', 'Салаты', 'Гарниры', 'Брускеты и закуски', 'Блюда из печени и сердца']
    cursor.execute(f"SELECT id, category, title FROM recipes WHERE category IN ({','.join(['?']*len(other_categories))})", other_categories)
    rows = cursor.fetchall()
    
    # Distribution logic:
    # Meat/Fish -> Mostly Lunch, some Dinner
    # Salads/Vegetables -> Mostly Dinner, some Lunch
    # Sides -> Balanced
    
    for i, (r_id, cat, title) in enumerate(rows):
        meal_type = 'Обед'
        if cat in ['Салаты', 'Блюда из овощей', 'Гарниры']:
            # Every second salad/veg/side goes to Dinner
            if i % 2 == 0:
                meal_type = 'Ужин'
            else:
                meal_type = 'Обед'
        elif cat in ['Мясо', 'Рыба', 'Блюда из печени и сердца']:
            # Every third meat/fish goes to Dinner, others to Lunch
            if i % 3 == 0:
                meal_type = 'Ужин'
            else:
                meal_type = 'Обед'
        elif cat == 'Брускеты и закуски':
            # Snacks are mostly Dinner or Lunch (let's split 50/50)
            meal_type = 'Ужин' if i % 2 == 0 else 'Обед'
            
        cursor.execute("UPDATE recipes SET meal_type = ? WHERE id = ?", (meal_type, r_id))
    
    conn.commit()
    print("Recipes distributed successfully!")
    
    # Final check of counts
    cursor.execute("SELECT meal_type, COUNT(*) FROM recipes GROUP BY meal_type")
    counts = cursor.fetchall()
    for m_type, count in counts:
        print(f"{m_type}: {count}")
        
    conn.close()

if __name__ == "__main__":
    asyncio.run(distribute_recipes())
