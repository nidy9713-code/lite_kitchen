import sqlite3
import sys

# Настройка кодировки для вывода в терминал
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def check_db():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    print("=== АНАЛИЗ БАЗЫ ДАННЫХ ===")
    
    # 1. Проверка по meal_type (для меню "Подобрать рецепт")
    print("\n1. Распределение по типам приема пищи (meal_type):")
    cursor.execute("SELECT meal_type, COUNT(*) FROM recipes GROUP BY meal_type")
    for row in cursor.fetchall():
        print(f" - {row[0] if row[0] else 'ПУСТО'}: {row[1]}")
        
    # 2. Проверка по категориям (для меню "Категории")
    print("\n2. Распределение по категориям (category):")
    cursor.execute("SELECT category, COUNT(*) FROM recipes GROUP BY category")
    for row in cursor.fetchall():
        print(f" - {row[0]}: {row[1]}")
        
    # 3. Детальный аудит Напитков
    print("\n3. Аудит раздела НАПИТКИ:")
    cursor.execute("SELECT id, title, category, meal_type FROM recipes WHERE category = 'Напитки' OR meal_type = 'Напиток'")
    drinks = cursor.fetchall()
    if not drinks:
        print(" ! Напитки не найдены")
    for d in drinks:
        print(f" ID: {d[0]} | {d[1]} | Кат: {d[2]} | Тип: {d[3]}")
        
    # 4. Детальный аудит Десертов
    print("\n4. Аудит раздела ДЕСЕРТЫ:")
    cursor.execute("SELECT id, title, category, meal_type FROM recipes WHERE category = 'Десерты' OR meal_type = 'Десерт'")
    desserts = cursor.fetchall()
    if not desserts:
        print(" ! Десерты не найдены")
    for d in desserts:
        print(f" ID: {d[0]} | {d[1]} | Кат: {d[2]} | Тип: {d[3]}")

    conn.close()

if __name__ == "__main__":
    check_db()
