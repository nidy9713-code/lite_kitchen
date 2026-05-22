import sys
import httpx
from config import SUPABASE_URL, SUPABASE_KEY

sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}
BASE = f"{SUPABASE_URL}/rest/v1/recipes"

RECIPE = {
    "title": "Запечённая рваная говядина",
    "about": (
        "Мясо получается очень мягким, сочным и легко распадается на волокна.\n"
        "Домашние обычно съедают его очень быстро — отлично подходит для заготовки на несколько блюд."
    ),
    "ingredients": (
        "— кусок говядины (мякоть)\n"
        "— соль\n"
        "— перец\n\n"
        "*по желанию:\n"
        "— чеснок дольками\n"
        "— чернослив\n"
        "— курага\n"
        "— веточка розмарина\n"
        "— любимые специи"
    ),
    "steps": (
        "1. Натереть мясо солью и специями\n"
        "2. Завернуть мясо в пергамент\n"
        "3. Затем завернуть в фольгу в 2–3 слоя\n"
        "4. Переложить в жаропрочную форму\n"
        "5. Томить в духовке при 150°C около 4 часов"
    ),
    "tips": (
        "Чем дольше мясо томится на низкой температуре, тем мягче получается текстура.\n"
        "После приготовления можно слегка разобрать мясо вилкой прямо в собственном соку."
    ),
    "serving": (
        "Использовать для бутербродов\n"
        "Добавлять в шаурму\n"
        "Подавать с крупой\n"
        "Сочетать с салатами\n"
        "Хорошо сочетается с зелёным салатом и клубникой"
    ),
    "substitutions": (
        "— говядина → индейка или баранина для других вариаций\n"
        "— розмарин → тимьян или прованские травы"
    ),
    "category": "Мясо",
    "time_category": "long",
    "cook_time": 240,
    "tags": '["для всей семьи", "без глютена", "без молока"]',
}


def main():
    existing = httpx.get(
        BASE,
        params={"select": "id,meal_type", "title": f"eq.{RECIPE['title']}"},
        headers=HEADERS,
        timeout=30,
    ).json()
    if existing:
        print("Already exists:", existing)
        return

    for meal_type in ("Обед", "Ужин"):
        payload = {**RECIPE, "meal_type": meal_type}
        row = httpx.post(BASE, json=payload, headers=HEADERS, timeout=30).json()[0]
        print(f"Added id={row['id']} for {meal_type}")


if __name__ == "__main__":
    main()
