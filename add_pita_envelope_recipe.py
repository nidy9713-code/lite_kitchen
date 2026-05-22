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
TITLE = "Конвертик с рваной говядиной"

RECIPE = {
    "title": TITLE,
    "about": (
        "Быстрый и сытный вариант перекуса или завтрака.\n"
        "Отлично подходит для использования заранее приготовленной рваной говядины.\n\n"
    "📌 Для этого рецепта можно использовать «Запечённую рваную говядину» из раздела мясных блюд."
    ),
    "ingredients": (
        "— готовая рваная говядина\n"
        "— листья салата\n"
        "— творожный сыр\n"
        "— огурцы\n"
        "— пита"
    ),
    "steps": (
        "1. Разогреть питу на сухой сковороде или в микроволновке 10–20 секунд\n"
        "2. Аккуратно срезать верхушку и разделить внутренние края\n"
        "3. Намазать внутренние стенки творожным сыром\n"
        "4. Добавить листья салата, огурцы и мясо\n"
        "5. Подавать сразу после приготовления"
    ),
    "tips": (
        "Начинку можно менять под настроение и продукты в холодильнике.\n"
        "Более лёгкий вариант получится с курицей или индейкой.\n"
        "Говядина делает вкус более насыщенным и сытным."
    ),
    "serving": (
        "Как самостоятельный перекус\n"
        "Удобно брать с собой\n"
        "Подходит до и после тренировки\n"
        "Перед тренировкой можно добавить больше овощей\n"
        "После тренировки — увеличить количество мяса"
    ),
    "substitutions": (
        "— говядина → курица или индейка\n"
        "— листья салата → любая зелень\n"
        "— огурцы → квашеная капуста\n"
        "— творожный сыр → хумус / гуакамоле / томатный соус"
    ),
    "time_category": "quick",
    "cook_time": 5,
    "tags": '["для всей семьи", "перекус", "завтрак", "удобно в дорогу"]',
}

ENTRIES = [
    {"meal_type": "Перекус", "category": "Перекус"},
    {"meal_type": "Завтрак", "category": "Брускеты и круассаны"},
]


def main():
    existing = httpx.get(
        BASE,
        params={"select": "id,meal_type", "title": f"eq.{TITLE}"},
        headers=HEADERS,
        timeout=30,
    ).json()
    if existing:
        ids = [r["id"] for r in existing]
        httpx.delete(
            BASE,
            params={"id": f"in.({','.join(str(i) for i in ids)})"},
            headers=HEADERS,
            timeout=30,
        ).raise_for_status()
        print(f"Removed old entries: {ids}")

    for entry in ENTRIES:
        payload = {**RECIPE, **entry}
        row = httpx.post(BASE, json=payload, headers=HEADERS, timeout=30).json()[0]
        print(f"Added id={row['id']} → {entry['meal_type']} / {entry['category']}")


if __name__ == "__main__":
    main()
