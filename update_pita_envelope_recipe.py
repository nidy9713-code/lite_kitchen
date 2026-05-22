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

ABOUT = (
    "Быстрый и сытный вариант перекуса или завтрака.\n"
    "Отлично подходит для использования заранее приготовленной рваной говядины.\n\n"
    "📌 Для этого рецепта можно использовать «Запечённую рваную говядину» из раздела мясных блюд."
)

TAGS = '["для всей семьи", "перекус", "завтрак", "удобно в дорогу"]'


def main():
    rows = httpx.get(
        BASE,
        params={"select": "id,title,tags,about", "title": f"eq.{TITLE}"},
        headers=HEADERS,
        timeout=30,
    ).json()
    if not rows:
        print("Recipes not found")
        return

    for row in rows:
        r = httpx.patch(
            BASE,
            params={"id": f"eq.{row['id']}"},
            json={"about": ABOUT, "tags": TAGS},
            headers=HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        print(f"Updated id={row['id']}")


if __name__ == "__main__":
    main()
