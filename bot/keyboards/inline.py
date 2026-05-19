from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

CATEGORIES = [
    "Все", "👶 Для детей", "👨‍👩‍👧 Для всей семьи", "🌿 Без глютена", 
    "🥛 Без молока", "🥚 Без яиц", "⚡️ Быстрые рецепты", "💚 Лёгкие блюда",
    "Каши", "Завтраки из яиц", "Оладушки и блины", 
    "Творог и молочка", "Супы", "Мясо", "Рыба", "Десерты",
    "Блюда из овощей", "Блюда из печени и сердца",
    "Гарниры", "Запеканки", "Напитки", "Салаты", "Брускеты и круассаны",
    "Смузи для детей", "Горячие напитки", "Лимонады", "Детокс", "Перекус",
    "Сезонные смузи"
]

def get_subcategories_keyboard(meal_type: str):
    builder = InlineKeyboardBuilder()
    
    # Define which categories belong to which meal type for the sub-menu
    subcats = {
        "Завтрак": ["Каши", "Завтраки из яиц", "Оладушки и блины", "Творог и молочка", "Брускеты и круассаны"],
        "Обед": ["Супы", "Мясо", "Рыба", "Блюда из овощей", "Блюда из печени и сердца"],
        "Ужин": ["Мясо", "Рыба", "Блюда из овощей", "Блюда из печени и сердца", "Гарниры"],
        "Десерт": ["Десерты"],
        "Напиток": ["Горячие напитки", "Лимонады", "Детокс", "Смузи для детей", "Сезонные смузи"]
    }
    
    current_subcats = subcats.get(meal_type, [])
    for cat in current_subcats:
        builder.row(InlineKeyboardButton(text=cat, callback_data=f"mealcat_{meal_type}_{cat}"))
    
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="get_recipe"))
    builder.adjust(2)
    return builder.as_markup()

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🍽 Подобрать рецепт", callback_data="get_recipe"))
    builder.row(InlineKeyboardButton(text="🤯 Не знаю, что приготовить", callback_data="dont_know"))
    builder.row(InlineKeyboardButton(text="📚 Категории", callback_data="categories"))
    builder.row(InlineKeyboardButton(text="🔍 Поиск", callback_data="search"))
    builder.row(InlineKeyboardButton(text="🧩 Конструктор", callback_data="constructor"))
    builder.row(InlineKeyboardButton(text="💡 Советы", callback_data="tips"))
    builder.row(InlineKeyboardButton(text="📥 PDF", callback_data="get_pdf"))
    builder.row(InlineKeyboardButton(text="ℹ️ О проекте", callback_data="about"))
    builder.row(InlineKeyboardButton(text="💬 Задать вопрос", callback_data="ask_question"))
    builder.adjust(2)
    return builder.as_markup()

def get_categories_main_keyboard():
    builder = InlineKeyboardBuilder()
    
    # High-level tag categories first
    tag_cats = [
        "👶 Для детей", "👨‍👩‍👧 Для всей семьи", "🌿 Без глютена", 
        "🥛 Без молока", "🥚 Без яиц", "⚡️ Быстрые рецепты", "💚 Лёгкие блюда"
    ]
    for t in tag_cats:
        builder.row(InlineKeyboardButton(text=t, callback_data=f"cat_{t}"))
        
    # Then the "All recipes" button which will lead to product categories
    builder.row(InlineKeyboardButton(text="📚 Все рецепты", callback_data="all_recipes_cats"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="start"))
    builder.adjust(2)
    return builder.as_markup()

def get_product_categories_keyboard():
    builder = InlineKeyboardBuilder()
    
    # Exclude tags that are already on the main screen and 'Все'
    tag_cats = ["👶 Для детей", "👨‍👩‍👧 Для всей семьи", "🌿 Без глютена", "🥛 Без молока", "🥚 Без яиц", "⚡️ Быстрые рецепты", "💚 Лёгкие блюда"]
    cats_to_show = [c for c in CATEGORIES if c != "Все" and c not in tag_cats]
    
    for cat in cats_to_show:
        builder.row(InlineKeyboardButton(text=cat, callback_data=f"cat_{cat}"))
        
    builder.row(InlineKeyboardButton(text="📜 Показать всё", callback_data="cat_Все"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="categories"))
    builder.adjust(2)
    return builder.as_markup()

def get_time_selection():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏱ До 15 минут", callback_data="time_quick"))
    builder.row(InlineKeyboardButton(text="⏱ 15–30 минут", callback_data="time_medium"))
    builder.row(InlineKeyboardButton(text="⏱ Есть время", callback_data="time_long"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="start"))
    return builder.as_markup()

def get_tag_selection():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🥗 Лёгкое", callback_data="tag_light"))
    builder.row(InlineKeyboardButton(text="🍽 Сытное", callback_data="tag_hearty"))
    builder.row(InlineKeyboardButton(text="👶 Для ребёнка", callback_data="tag_kids"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="dont_know"))
    return builder.as_markup()

def get_meal_type_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌅 Завтраки", callback_data="meal_Завтрак"))
    builder.row(InlineKeyboardButton(text="🍲 Обеды", callback_data="meal_Обед"))
    builder.row(InlineKeyboardButton(text="🌙 Ужины", callback_data="meal_Ужин"))
    builder.row(InlineKeyboardButton(text="🥪 Перекусы", callback_data="meal_Перекус"))
    builder.row(InlineKeyboardButton(text="🥗 Салаты", callback_data="meal_Салаты"))
    builder.row(InlineKeyboardButton(text="🥧 Запеканки", callback_data="meal_Запеканки"))
    builder.row(InlineKeyboardButton(text="🍰 Десерты", callback_data="meal_Десерт"))
    builder.row(InlineKeyboardButton(text="🍹 Напитки", callback_data="meal_Напиток"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="start"))
    builder.adjust(2)
    return builder.as_markup()

def get_constructor_list_keyboard(constructors):
    builder = InlineKeyboardBuilder()
    for c in constructors:
        builder.row(InlineKeyboardButton(text=f"🧩 {c['title']}", callback_data=f"const_{c['id']}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="start"))
    return builder.as_markup()

def get_recipe_list_keyboard(recipes, back_data="start"):
    builder = InlineKeyboardBuilder()
    for r in recipes:
        builder.row(InlineKeyboardButton(text=r['title'], callback_data=f"recipe_{r['id']}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=back_data))
    return builder.as_markup()

def _add_related_recipe_rows(builder: InlineKeyboardBuilder, related) -> None:
    seen = set()
    for item in related or []:
        rid = item["id"]
        if rid in seen:
            continue
        seen.add(rid)
        label = item.get("label") or f"Рецепт #{rid}"
        builder.row(InlineKeyboardButton(text=f"🍽 {label}", callback_data=f"recipe_{rid}"))

def get_related_recipes_keyboard(related):
    """Кнопки для связанных рецептов (без /start в чате)."""
    builder = InlineKeyboardBuilder()
    _add_related_recipe_rows(builder, related)
    return builder.as_markup() if related else None

def get_recipe_footer_keyboard(related, back_data=None, show_more_data="dont_know"):
    """Кнопки под рецептом: связанный рецепт + навигация."""
    builder = InlineKeyboardBuilder()
    _add_related_recipe_rows(builder, related)
    if back_data:
        builder.row(InlineKeyboardButton(text="🔙 Назад к списку", callback_data=back_data))

    show_more_text = "🔁 Показать ещё"
    if show_more_data == "plan_day":
        show_more_text = "🔁 Другое меню на день"

    builder.row(InlineKeyboardButton(text=show_more_text, callback_data=show_more_data))
    builder.row(InlineKeyboardButton(text="📅 Подобрать на весь день", callback_data="plan_day"))
    builder.row(InlineKeyboardButton(text="🏠 В меню", callback_data="start"))
    return builder.as_markup()

def get_tips_keyboard(has_hacks=False):
    builder = InlineKeyboardBuilder()
    
    # Static hardcoded tips
    builder.row(InlineKeyboardButton(text="🍽 Как собрать тарелку:", callback_data="tip_plate"))
    builder.row(InlineKeyboardButton(text="👶 Питание для детей:", callback_data="tip_kids"))
    builder.row(InlineKeyboardButton(text="📈 Введение продуктов (10%):", callback_data="tip_10percent"))
    builder.row(InlineKeyboardButton(text="🌿 Зелень для снижения веса:", callback_data="tip_greens"))
    builder.row(InlineKeyboardButton(text="❌ Частые ошибки:", callback_data="tip_errors"))
    
    # Folders for dynamic tips
    if has_hacks:
        builder.row(InlineKeyboardButton(text="✨ Советы по приготовлению:", callback_data="cooking_tips"))
            
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="start"))
    builder.adjust(1)
    return builder.as_markup()

def get_cooking_tips_keyboard(hacks):
    builder = InlineKeyboardBuilder()
    for h in hacks:
        title = h['title'].replace(":", "").strip()
        builder.row(InlineKeyboardButton(text=f"✨ {title}:", callback_data=f"dtip_h_{h['id']}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="tips"))
    builder.adjust(1)
    return builder.as_markup()

def get_seasonal_smoothies_keyboard():
    builder = InlineKeyboardBuilder()
    subs = [
        ("🍓 Весенне-летние (май-сентябрь)", "ss_spring_summer"),
        ("🍁 Осенне-зимние (октябрь-апрель)", "ss_autumn_winter"),
        ("🍫 Десертные (без чувства вины)", "ss_dessert"),
        ("🥑 Сытные (замена перекуса)", "ss_hearty"),
        ("🌿 Для детокса", "ss_detox"),
        ("🍊 Для иммунитета", "ss_immunity"),
        ("🥥 Экзотика", "ss_exotic"),
        ("🍵 Тёплые смузи (зима)", "ss_warm"),
        ("🍇 Для здоровья сердца", "ss_heart"),
        ("🍌 Для спортсменов", "ss_sport"),
        ("🍯 Для сладкоежек", "ss_sweet")
    ]
    for text, callback_data in subs:
        builder.row(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="meal_Напиток"))
    builder.adjust(2)
    return builder.as_markup()

def get_admin_main():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Добавить рецепт", callback_data="admin_add"))
    builder.row(InlineKeyboardButton(text="✏️ Редактировать разделы", callback_data="admin_edit_sections"))
    builder.row(InlineKeyboardButton(text="📁 Управление категориями", callback_data="admin_edit_categories"))
    builder.row(InlineKeyboardButton(text="🔑 Управление доступом", callback_data="admin_access_mgmt"))
    builder.row(InlineKeyboardButton(text="❌ Удалить рецепт", callback_data="admin_delete_list"))
    builder.row(InlineKeyboardButton(text="🏠 В меню", callback_data="start"))
    builder.adjust(1)
    return builder.as_markup()

def get_admin_edit_sections():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📝 Рецепты", callback_data="admin_edit_select"))
    builder.row(InlineKeyboardButton(text="🧩 Конструкторы", callback_data="admin_edit_constructors"))
    builder.row(InlineKeyboardButton(text="💡 Советы", callback_data="admin_edit_tips"))
    builder.row(InlineKeyboardButton(text="📥 PDF", callback_data="admin_edit_pdf"))
    builder.row(InlineKeyboardButton(text="ℹ️ О проекте", callback_data="admin_edit_about"))
    builder.row(InlineKeyboardButton(text="📁 Управление категориями", callback_data="admin_edit_categories"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel"))
    builder.adjust(2)
    return builder.as_markup()

def get_back_button(callback_data):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data))
    return builder.as_markup()

def get_final_options(back_data=None, show_more_data="dont_know"):
    builder = InlineKeyboardBuilder()
    if back_data:
        builder.row(InlineKeyboardButton(text="🔙 Назад к списку", callback_data=back_data))
    
    show_more_text = "🔁 Показать ещё"
    if show_more_data == "plan_day":
        show_more_text = "🔁 Другое меню на день"
        
    builder.row(InlineKeyboardButton(text=show_more_text, callback_data=show_more_data))
    builder.row(InlineKeyboardButton(text="📅 Подобрать на весь день", callback_data="plan_day"))
    builder.row(InlineKeyboardButton(text="🏠 В меню", callback_data="start"))
    builder.adjust(1)
    return builder.as_markup()
