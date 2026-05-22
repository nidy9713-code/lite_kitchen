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
TITLE = "Тост с хумусом"

ABOUT = (
    "Быстрая закуска или лёгкий завтрак.\n"
    "Сытно и удобно, если хумус уже заготовлен заранее.\n\n"
    "📌 Для этого рецепта можно использовать «Хумус» из раздела перекусов."
)


def main():
    rows = httpx.get(
        BASE,
        params={"select": "id,title,about", "title": f"eq.{TITLE}"},
        headers=HEADERS,
        timeout=30,
    ).json()
    if not rows:
        print("Recipe not found")
        return

    for row in rows:
        r = httpx.patch(
            BASE,
            params={"id": f"eq.{row['id']}"},
            json={"about": ABOUT},
            headers=HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        print(f"Updated id={row['id']}")


if __name__ == "__main__":
    main()
