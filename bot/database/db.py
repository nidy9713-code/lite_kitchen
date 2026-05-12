import json
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

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
        
        if bot:
            from bot.utils.mailing import announce_new_recipe
            await announce_new_recipe(bot, data, self)
            
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

    async def search_recipes(self, query: str) -> List[Dict[str, Any]]:
        # Supabase doesn't support complex OR in a single ilike easily without RPC or complex filters
        # We'll use a simpler approach or multiple queries if needed
        # For now, let's search in title, ingredients, and tags
        q = f"%{query}%"
        response = self.supabase.table("recipes").select("*").or_(
            f"title.ilike.{q},ingredients.ilike.{q},tags.ilike.{q}"
        ).execute()
        return response.data

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
        response = self.supabase.table("recipes").select("*").eq("meal_type", meal_type).execute()
        return response.data

    async def get_recipes_by_meal_and_cat(self, meal_type: str, category: str) -> List[Dict[str, Any]]:
        response = self.supabase.table("recipes").select("*").eq("meal_type", meal_type).eq("category", category).execute()
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

    async def grant_access(self, user_id: int):
        self.supabase.table("users").update({'has_access': True}).eq("user_id", user_id).execute()

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
        response = self.supabase.table("recipes").select("*").eq("meal_type", meal_type).eq("time_category", time_category).or_(
            f"tags.ilike.{q_tag},about.ilike.{q_tag},ingredients.ilike.{q_tag},title.ilike.{q_tag},category.ilike.{q_tag}"
        ).limit(1).execute()
        if response.data: return response.data[0]
        
        # Fallback 1: meal_type + tag
        response = self.supabase.table("recipes").select("*").eq("meal_type", meal_type).or_(
            f"tags.ilike.{q_tag},about.ilike.{q_tag},ingredients.ilike.{q_tag},title.ilike.{q_tag},category.ilike.{q_tag}"
        ).limit(1).execute()
        if response.data: return response.data[0]
        
        # Fallback 2: meal_type + time
        response = self.supabase.table("recipes").select("*").eq("meal_type", meal_type).eq("time_category", time_category).limit(1).execute()
        if response.data: return response.data[0]
        
        # Fallback 3: meal_type only
        response = self.supabase.table("recipes").select("*").eq("meal_type", meal_type).limit(1).execute()
        return response.data[0] if response.data else None

db = Database()
