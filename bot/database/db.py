import sqlite3
import json
from typing import List, Dict, Any, Optional

class Database:
    def __init__(self, db_path: str = "recipes.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            conn.execute("PRAGMA foreign_keys = ON")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    about TEXT,
                    ingredients TEXT,
                    steps TEXT,
                    tips TEXT,
                    serving TEXT,
                    substitutions TEXT,
                    tags TEXT,
                    category TEXT,
                    meal_type TEXT,
                    time_category TEXT,
                    cook_time INTEGER,
                    portions TEXT,
                    photo_id TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    is_onboarded INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS constructors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    suitable_for TEXT,
                    principle TEXT,
                    basis TEXT,
                    protein TEXT,
                    fats TEXT,
                    fiber TEXT,
                    how_to_assemble TEXT,
                    flexibility TEXT,
                    lifehacks TEXT,
                    kids_recommendation TEXT,
                    photo_id TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            # Initialize default settings if not exist
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('about_text', ?)", (
                "<b>О проекте «Легкая кухня»</b>\n\n"
                "Создатель идеи — Чекунова Диана!\n\n"
                "Чем этот бот вам полезен:\n\n"
                "🌱 Задача показать разные варианты приготовления одного и того же блюда через конструктор, а не привязать вас к определенному рецепту! Выбирайте вкус и текстуру, которую ценит ваша семья.\n\n"
                "🌱 Я подберу вам рецепт под прием пищи, чтобы вы заранее могли его спланировать.\n\n"
                "🌱 Не знаете, что приготовить? Введите имеющиеся продукты или время, которым вы располагаете на готовку.\n\n"
                "🌱 В некоторых рецептах вы можете менять продукты, альтернативы указаны в самом рецепте.\n\n"
                "🌱 Отдельно вынесены лайфхаки по группам продуктов (каши, омлеты, гарниры) для вашего удобства.\n\n"
                "🌱 Есть гайды, которые вы можете скачать и использовать их в любой удобный вам момент."
            ,))
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('pdf_text', ?)", (
                "📚 <b>Наши полезные гайды и PDF-материалы</b>\n\n"
                "Здесь вы можете скачать полезные материалы для вашей кухни.\n\n"
                "(Ссылки на PDF пока не добавлены)"
            ,))
            conn.commit()

    async def add_recipe(self, data: Dict[str, Any], bot=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recipes (
                    title, about, ingredients, steps, tips, serving, substitutions, tags, category, meal_type, time_category, cook_time, portions, photo_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['title'], data['about'], data['ingredients'], data['steps'], 
                data.get('tips', ''), data.get('serving', ''), data.get('substitutions', ''), 
                json.dumps(data.get('tags', [])), data['category'], data.get('meal_type', ''), 
                data['time_category'], data.get('cook_time', 0), data.get('portions', ''), data.get('photo_id')
            ))
            conn.commit()
            recipe_id = cursor.lastrowid
            
            if bot:
                from bot.utils.mailing import announce_new_recipe
                await announce_new_recipe(bot, data, self)
                
            return recipe_id

    async def get_recipes_by_category(self, category: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if category == "Все":
                cursor.execute("SELECT * FROM recipes")
            else:
                cursor.execute("SELECT * FROM recipes WHERE category = ?", (category,))
            return [dict(row) for row in cursor.fetchall()]

    async def get_recipe_by_id(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    async def search_recipes(self, query: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            q = f"%{query}%"
            cursor.execute("""
                SELECT * FROM recipes 
                WHERE title LIKE ? OR ingredients LIKE ? OR tags LIKE ?
            """, (q, q, q))
            return [dict(row) for row in cursor.fetchall()]

    async def filter_recipes(self, time_category: str, tag: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Map user-friendly tags to internal search terms
            tag_map = {
                "light": "лёгкое",
                "hearty": "сытное",
                "kids": "для детей"
            }
            search_tag = tag_map.get(tag, tag)
            
            # Smart search: by time AND tag in ingredients/about/tags
            # We also search in title and category for better matching
            cursor.execute("""
                SELECT * FROM recipes 
                WHERE time_category = ? 
                AND (tags LIKE ? OR about LIKE ? OR ingredients LIKE ? OR title LIKE ? OR category LIKE ?)
                ORDER BY RANDOM()
            """, (time_category, f"%{search_tag}%", f"%{search_tag}%", f"%{search_tag}%", f"%{search_tag}%", f"%{search_tag}%"))
            results = [dict(row) for row in cursor.fetchall()]
            
            # Fallback 1: only tag (if time is too restrictive)
            if not results:
                cursor.execute("""
                    SELECT * FROM recipes 
                    WHERE tags LIKE ? OR about LIKE ? OR ingredients LIKE ? OR title LIKE ? OR category LIKE ?
                    ORDER BY RANDOM()
                """, (f"%{search_tag}%", f"%{search_tag}%", f"%{search_tag}%", f"%{search_tag}%", f"%{search_tag}%"))
                results = [dict(row) for row in cursor.fetchall()]
            
            # Fallback 2: only time
            if not results:
                cursor.execute("SELECT * FROM recipes WHERE time_category = ? ORDER BY RANDOM()", (time_category,))
                results = [dict(row) for row in cursor.fetchall()]
            
            # Fallback 3: random
            if not results:
                cursor.execute("SELECT * FROM recipes ORDER BY RANDOM() LIMIT 5")
                results = [dict(row) for row in cursor.fetchall()]
                
            return results

    async def get_recipes_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recipes WHERE tags LIKE ?", (f"%{tag}%",))
            return [dict(row) for row in cursor.fetchall()]

    async def get_recipes_by_meal_type(self, meal_type: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recipes WHERE meal_type = ?", (meal_type,))
            return [dict(row) for row in cursor.fetchall()]

    async def get_recipes_by_meal_and_cat(self, meal_type: str, category: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recipes WHERE meal_type = ? AND category = ?", (meal_type, category))
            return [dict(row) for row in cursor.fetchall()]

    async def delete_recipe(self, recipe_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
            conn.commit()

    async def update_recipe(self, recipe_id: int, data: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE recipes SET 
                    title = ?, about = ?, ingredients = ?, steps = ?, 
                    tips = ?, serving = ?, substitutions = ?, tags = ?, 
                    category = ?, meal_type = ?, time_category = ?, cook_time = ?, 
                    portions = ?, photo_id = ?
                WHERE id = ?
            """, (
                data['title'], data['about'], data['ingredients'], data['steps'], 
                data.get('tips', ''), data.get('serving', ''), data.get('substitutions', ''), 
                json.dumps(data.get('tags', [])), data['category'], data.get('meal_type', ''), 
                data['time_category'], data.get('cook_time', 0), data.get('portions', ''), 
                data.get('photo_id'), recipe_id
            ))
            conn.commit()

    async def get_user(self, user_id: int):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    async def add_user(self, user_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            conn.commit()

    async def set_onboarded(self, user_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_onboarded = 1 WHERE user_id = ?", (user_id,))
            conn.commit()

    async def get_all_user_ids(self) -> List[int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            return [row[0] for row in cursor.fetchall()]

    # CONSTRUCTORS
    async def add_constructor(self, data: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO constructors (
                    title, suitable_for, principle, basis, protein, fats, fiber, 
                    how_to_assemble, flexibility, lifehacks, kids_recommendation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['title'], data['suitable_for'], data['principle'], data['basis'],
                data['protein'], data['fats'], data['fiber'], data['how_to_assemble'],
                data['flexibility'], data['lifehacks'], data['kids_recommendation']
            ))
            conn.commit()
            return cursor.lastrowid

    async def get_constructors(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Only return "real" constructors that have a basis/principle
            cursor.execute("SELECT * FROM constructors WHERE basis IS NOT NULL OR principle IS NOT NULL")
            return [dict(row) for row in cursor.fetchall()]

    async def get_constructor_by_id(self, const_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM constructors WHERE id = ?", (const_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    async def update_constructor(self, const_id: int, data: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE constructors SET 
                    title = ?, suitable_for = ?, principle = ?, basis = ?, 
                    protein = ?, fats = ?, fiber = ?, how_to_assemble = ?, 
                    flexibility = ?, lifehacks = ?, kids_recommendation = ?,
                    photo_id = ?
                WHERE id = ?
            """, (
                data['title'], data['suitable_for'], data['principle'], data['basis'],
                data['protein'], data['fats'], data['fiber'], data['how_to_assemble'],
                data['flexibility'], data['lifehacks'], data['kids_recommendation'],
                data.get('photo_id'), const_id
            ))
            conn.commit()

    async def get_all_tips_and_hacks(self):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 1. From Constructors
            cursor.execute("SELECT id, title, lifehacks FROM constructors WHERE lifehacks IS NOT NULL AND lifehacks != ''")
            hacks = [dict(row) for row in cursor.fetchall()]
            
            # 2. From Recipes
            cursor.execute("SELECT title, tips, category FROM recipes WHERE tips IS NOT NULL AND tips != ''")
            recipe_tips = [dict(row) for row in cursor.fetchall()]
            
            return hacks, recipe_tips

    async def get_setting(self, key: str, default: str = "") -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    async def update_setting(self, key: str, value: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()

    async def get_random_recipe_by_filters(self, meal_type: str, time_category: str, tag: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            tag_map = {"light": "лёгкое", "hearty": "сытное", "kids": "для детей"}
            search_tag = tag_map.get(tag, tag)
            
            # Try strict match: meal_type + time + tag
            cursor.execute("""
                SELECT * FROM recipes 
                WHERE meal_type = ? AND time_category = ? 
                AND (tags LIKE ? OR about LIKE ? OR ingredients LIKE ? OR title LIKE ? OR category LIKE ?)
                ORDER BY RANDOM() LIMIT 1
            """, (meal_type, time_category, f"%{search_tag}%", f"%{search_tag}%", f"%{search_tag}%", f"%{search_tag}%", f"%{search_tag}%"))
            row = cursor.fetchone()
            if row: return dict(row)
            
            # Fallback 1: meal_type + tag
            cursor.execute("""
                SELECT * FROM recipes 
                WHERE meal_type = ? 
                AND (tags LIKE ? OR about LIKE ? OR ingredients LIKE ? OR title LIKE ? OR category LIKE ?)
                ORDER BY RANDOM() LIMIT 1
            """, (meal_type, f"%{search_tag}%", f"%{search_tag}%", f"%{search_tag}%", f"%{search_tag}%", f"%{search_tag}%"))
            row = cursor.fetchone()
            if row: return dict(row)
            
            # Fallback 2: meal_type + time
            cursor.execute("SELECT * FROM recipes WHERE meal_type = ? AND time_category = ? ORDER BY RANDOM() LIMIT 1", (meal_type, time_category))
            row = cursor.fetchone()
            if row: return dict(row)
            
            # Fallback 3: meal_type only
            cursor.execute("SELECT * FROM recipes WHERE meal_type = ? ORDER BY RANDOM() LIMIT 1", (meal_type,))
            row = cursor.fetchone()
            return dict(row) if row else None

db = Database()
