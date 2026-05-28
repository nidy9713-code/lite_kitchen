import json
import re
from typing import List, Dict, Any, Optional

from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

# Типичные окончания (длинные → короткие): по одному снятию за шаг для «корня» слова в поиске.
_RU_SEARCH_SUFFIXES: tuple = (
    "ьными", "ными", "ями", "ами", "его", "ого", "ему", "ому", "ыми", "ими",
    "ах", "ях", "ам", "ям", "ов", "ев", "ей", "ой", "ый", "ий",
    "ая", "яя", "ое", "ее", "ую", "юю", "ые", "ие", "ом", "ем",
    "а", "я", "о", "е", "ы", "и", "у", "ю", "ь", "й",
)
class Database:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def add_recipe(self, data: Dict[str, Any], bot=None):
        recipe_data = {
            'title': data['title'],
            'about': data['about'],
            'ingredients': data['ingredients'],
            'steps': data['steps'],
            'tips': data.get('tips', ''),
            'serving': data.get('serving', ''),
            'substitutions': data.get('substitutions', ''),
            'tags': json.dumps(data.get('tags', []), ensure_ascii=False),
            'category': data['category'],
            'meal_type': data.get('meal_type', ''),
            'time_category': data['time_category'],
            'cook_time': data.get('cook_time', 0),
            'portions': data.get('portions', ''),
            'photo_id': data.get('photo_id')
        }
        
        response = self.supabase.table("recipes").insert(recipe_data).execute()
        recipe_id = response.data[0]['id']

        from bot.utils.mailing import schedule_recipe_notification
        await schedule_recipe_notification(bot, data, self)

        return recipe_id

    async def get_recipes_by_category(self, category: str) -> List[Dict[str, Any]]:
        if category == "Все":
            response = self.supabase.table("recipes").select("*").execute()
        else:
            response = self.supabase.table("recipes").select("*").eq("category", category).execute()
        return response.data

    async def get_recipe_by_id(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        response = self.supabase.table("recipes").select("*").eq("id", recipe_id).execute()
        return response.data[0] if response.data else None

    async def find_recipe_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        response = (
            self.supabase.table("recipes")
            .select("*")
            .eq("title", title)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def _token_variants(self, token: str) -> List[str]:
        """Варианты одного слова: исходное + несколько шагов снятия русских окончаний (корень для ILIKE)."""
        t = token.replace("ё", "е").lower().strip()
        if len(t) < 2:
            return []
        out: List[str] = []
        seen: set = set()
        cur = t
        for _ in range(6):
            if cur in seen:
                break
            if len(cur) >= 2:
                seen.add(cur)
                out.append(cur)
            if len(cur) <= 3:
                break
            nxt: Optional[str] = None
            for suf in _RU_SEARCH_SUFFIXES:
                if cur.endswith(suf):
                    cand = cur[: -len(suf)]
                    if len(cand) >= 3:
                        nxt = cand
                    break
            if nxt is None:
                break
            cur = nxt
        return out

    def _search_ilike_patterns(self, safe: str) -> List[str]:
        """
        Шаблоны ILIKE: целая фраза, затем по каждому слову — полная форма и морфологические корни
        (для любых ингредиентов и названий). Плюс расширения для «курица / курочка / куриный…».
        Порядок списка = приоритет (pattern_tier): раньше — релевантнее.
        """
        patterns: List[str] = []
        seen: set = set()

        def add_pat(p: str) -> None:
            if p not in seen:
                seen.add(p)
                patterns.append(p)

        add_pat(f"%{safe}%")

        # слова из запроса: кириллица/латиница/цифры/дефис, минимум 2 символа
        tokens = re.findall(r"[а-яА-ЯёЁa-zA-Z0-9\-]{2,}", safe)
        for tok in tokens:
            variants = self._token_variants(tok)
            for i, v in enumerate(variants):
                if i == 0:
                    if len(v) >= 2:
                        add_pat(f"%{v}%")
                else:
                    if len(v) >= 4:
                        add_pat(f"%{v}%")

        n = safe.replace("ё", "е").lower()
        if "куриц" in n or n in ("курочка", "курочки", "курочку", "курочке", "курочкой"):
            for extra in (
                "%куроч%",
                "%курин%",
                "%курят%",
                "%цыплён%",
                "%цыплен%",
                "%цыпля%",
            ):
                add_pat(extra)

        # ограничение числа запросов к Supabase (паттерн × колонка)
        max_patterns = 36
        if len(patterns) > max_patterns:
            patterns = patterns[:max_patterns]

        return patterns

    async def search_recipes(self, query: str) -> List[Dict[str, Any]]:
        """
        Поиск по подстроке (без учёта регистра): название, ингредиенты, теги, описание, замены, категория.
        Оптимизировано: используем .or_() для поиска по всем колонкам за один запрос на каждый паттерн.
        """
        raw = (query or "").strip()
        if not raw:
            return []
        safe = raw.replace("%", "").replace("_", "").strip()
        if not safe:
            return []
        patterns = self._search_ilike_patterns(safe)

        columns_priority = (
            "title",
            "ingredients",
            "tags",
            "about",
            "substitutions",
            "category",
            "meal_type"
        )
        col_rank = {c: i for i, c in enumerate(columns_priority)}

        best_by_title: Dict[str, tuple] = {}

        for pattern_tier, pattern in enumerate(patterns):
            # Формируем условие OR для всех колонок
            or_filter = ",".join([f"{col}.ilike.{pattern}" for col in columns_priority])
            response = self.supabase.table("recipes").select("*").or_(or_filter).execute()
            
            for row in response.data or []:
                title_key = (row.get("title") or "").strip().lower()
                if not title_key:
                    continue
                
                # Определяем, в какой колонке нашлось совпадение для ранжирования
                # (так как мы использовали OR, нам нужно проверить вручную или просто взять минимальный ранг)
                match_col_tier = len(columns_priority)
                for col in columns_priority:
                    val = str(row.get(col) or "").lower()
                    if pattern.replace("%", "").lower() in val:
                        match_col_tier = min(match_col_tier, col_rank[col])
                
                has_photo = row.get("photo_id") is not None
                key = (match_col_tier, pattern_tier)
                
                prev = best_by_title.get(title_key)
                if prev is None:
                    best_by_title[title_key] = (key, has_photo, row)
                else:
                    prev_key, prev_has_photo, prev_row = prev
                    if (has_photo and not prev_has_photo) or (has_photo == prev_has_photo and key < prev_key):
                        best_by_title[title_key] = (key, has_photo, row)

        items = list(best_by_title.values())
        items.sort(key=lambda x: (x[0], (x[2].get("title") or "").lower()))
        return [row for _, _, row in items]

    async def filter_recipes(self, time_category: str, tag: str) -> List[Dict[str, Any]]:
        tag_map = {
            "light": "лёгкое",
            "hearty": "сытное",
            "kids": "для детей"
        }
        search_tag = tag_map.get(tag, tag)
        q_tag = f"%{search_tag}%"
        
        # Smart search: by time AND tag in various fields
        response = self.supabase.table("recipes").select("*").eq("time_category", time_category).or_(
            f"tags.ilike.{q_tag},about.ilike.{q_tag},ingredients.ilike.{q_tag},title.ilike.{q_tag},category.ilike.{q_tag}"
        ).execute()
        results = response.data
        
        # Fallback 1: only tag
        if not results:
            response = self.supabase.table("recipes").select("*").or_(
                f"tags.ilike.{q_tag},about.ilike.{q_tag},ingredients.ilike.{q_tag},title.ilike.{q_tag},category.ilike.{q_tag}"
            ).execute()
            results = response.data
            
        # Fallback 2: only time
        if not results:
            response = self.supabase.table("recipes").select("*").eq("time_category", time_category).execute()
            results = response.data
            
        # Fallback 3: random (we'll just take first 5 for simplicity instead of true random)
        if not results:
            response = self.supabase.table("recipes").select("*").limit(5).execute()
            results = response.data
                
        return results

    async def get_recipes_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        response = self.supabase.table("recipes").select("*").ilike("tags", f"%{tag}%").execute()
        return response.data

    async def get_recipes_by_meal_type(self, meal_type: str) -> List[Dict[str, Any]]:
        response = self.supabase.table("recipes").select("*").ilike("meal_type", f"%{meal_type}%").execute()
        return response.data

    async def get_recipes_by_meal_and_cat(self, meal_type: str, category: str) -> List[Dict[str, Any]]:
        response = self.supabase.table("recipes").select("*").ilike("meal_type", f"%{meal_type}%").eq("category", category).execute()
        return response.data

    async def delete_recipe(self, recipe_id: int):
        self.supabase.table("recipes").delete().eq("id", recipe_id).execute()

    async def update_recipe(self, recipe_id: int, data: Dict[str, Any]):
        recipe_data = {
            'title': data['title'],
            'about': data['about'],
            'ingredients': data['ingredients'],
            'steps': data['steps'],
            'tips': data.get('tips', ''),
            'serving': data.get('serving', ''),
            'substitutions': data.get('substitutions', ''),
            'tags': json.dumps(data.get('tags', []), ensure_ascii=False) if isinstance(data.get('tags'), list) else data.get('tags'),
            'category': data['category'],
            'meal_type': data.get('meal_type', ''),
            'time_category': data['time_category'],
            'cook_time': data.get('cook_time', 0),
            'portions': data.get('portions', ''),
            'photo_id': data.get('photo_id')
        }
        self.supabase.table("recipes").update(recipe_data).eq("id", recipe_id).execute()

    async def get_user(self, user_id: int):
        response = self.supabase.table("users").select("*").eq("user_id", user_id).execute()
        return response.data[0] if response.data else None

    async def add_user(self, user_id: int, has_access: bool = False):
        self.supabase.table("users").upsert({'user_id': user_id, 'has_access': has_access}).execute()
        # Update cache
        from bot.utils.access_middleware import access_cache
        access_cache[user_id] = has_access

    async def grant_access(self, user_id: int):
        self.supabase.table("users").update({'has_access': True}).eq("user_id", user_id).execute()
        # Clear cache if exists
        from bot.utils.access_middleware import access_cache
        if user_id in access_cache:
            access_cache[user_id] = True

    async def set_onboarded(self, user_id: int):
        self.supabase.table("users").update({'is_onboarded': 1}).eq("user_id", user_id).execute()

    async def get_all_user_ids(self) -> List[int]:
        response = self.supabase.table("users").select("user_id").execute()
        return [row['user_id'] for row in response.data]

    # CONSTRUCTORS
    async def add_constructor(self, data: Dict[str, Any]):
        response = self.supabase.table("constructors").insert(data).execute()
        return response.data[0]['id']

    async def get_constructors(self) -> List[Dict[str, Any]]:
        # Only return "real" constructors that have a basis or principle
        response = self.supabase.table("constructors").select("*").or_("basis.not.is.null,principle.not.is.null").execute()
        return response.data

    async def get_constructor_by_id(self, const_id: int) -> Optional[Dict[str, Any]]:
        response = self.supabase.table("constructors").select("*").eq("id", const_id).execute()
        return response.data[0] if response.data else None

    async def update_constructor(self, const_id: int, data: Dict[str, Any]):
        self.supabase.table("constructors").update(data).eq("id", const_id).execute()

    async def get_all_tips_and_hacks(self):
        # 1. From Constructors
        response_hacks = self.supabase.table("constructors").select("id,title,lifehacks").neq("lifehacks", "").execute()
        hacks = response_hacks.data
        
        # 2. From Recipes
        response_tips = self.supabase.table("recipes").select("title,tips,category").neq("tips", "").execute()
        recipe_tips = response_tips.data
        
        return hacks, recipe_tips

    async def get_setting(self, key: str, default: str = "") -> str:
        response = self.supabase.table("settings").select("value").eq("key", key).execute()
        return response.data[0]['value'] if response.data else default

    async def update_setting(self, key: str, value: str):
        self.supabase.table("settings").upsert({'key': key, 'value': value}).execute()

    async def get_random_recipe_by_filters(self, meal_type: str, time_category: str, tag: str) -> Optional[Dict[str, Any]]:
        tag_map = {"light": "лёгкое", "hearty": "сытное", "kids": "для детей"}
        search_tag = tag_map.get(tag, tag)
        q_tag = f"%{search_tag}%"
        
        # Try strict match: meal_type + time + tag
        response = self.supabase.table("recipes").select("*").ilike("meal_type", f"%{meal_type}%").eq("time_category", time_category).or_(
            f"tags.ilike.{q_tag},about.ilike.{q_tag},ingredients.ilike.{q_tag},title.ilike.{q_tag},category.ilike.{q_tag}"
        ).limit(1).execute()
        if response.data: return response.data[0]
        
        # Fallback 1: meal_type + tag
        response = self.supabase.table("recipes").select("*").ilike("meal_type", f"%{meal_type}%").or_(
            f"tags.ilike.{q_tag},about.ilike.{q_tag},ingredients.ilike.{q_tag},title.ilike.{q_tag},category.ilike.{q_tag}"
        ).limit(1).execute()
        if response.data: return response.data[0]
        
        # Fallback 2: meal_type + time
        response = self.supabase.table("recipes").select("*").ilike("meal_type", f"%{meal_type}%").eq("time_category", time_category).limit(1).execute()
        if response.data: return response.data[0]
        
        # Fallback 3: meal_type only
        response = self.supabase.table("recipes").select("*").ilike("meal_type", f"%{meal_type}%").limit(1).execute()
        return response.data[0] if response.data else None

    # PENDING NOTIFICATIONS
    async def add_pending_notification(self, title: str, category: str):
        self.supabase.table("pending_notifications").insert({
            'title': title,
            'category': category
        }).execute()

    async def get_pending_notifications(self) -> List[Dict[str, Any]]:
        response = self.supabase.table("pending_notifications").select("*").execute()
        return response.data

    async def clear_pending_notifications(self):
        # Delete all records from pending_notifications
        # In Supabase/Postgrest we can use .neq("id", 0) to match all
        self.supabase.table("pending_notifications").delete().neq("id", 0).execute()

    async def delete_pending_notification(self, notification_id: int):
        self.supabase.table("pending_notifications").delete().eq("id", notification_id).execute()

db = Database()
