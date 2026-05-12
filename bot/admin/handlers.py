import asyncio
import json
import re
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from bot.keyboards.inline import (
    get_admin_main, CATEGORIES, get_back_button, get_admin_edit_sections
)
from bot.database.db import db
from config import ADMIN_IDS

router = Router()

def clean_input(text, header_pattern=None):
    if not text or text == "-":
        return text
    
    res = text.strip()
    if header_pattern:
        res = re.sub(header_pattern, '', res, flags=re.IGNORECASE | re.MULTILINE)
    
    # Remove leading bullets/numbers from each line if they were copied from template
    lines = res.strip().split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            # Only remove if it looks like a template placeholder or a bullet
            line = re.sub(r'^[—\-•📌]\s*', '', line)
            if line and line != "…":
                cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines)

class AdminStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_about = State()
    waiting_for_ingredients = State()
    waiting_for_steps = State()
    waiting_for_tips = State()
    waiting_for_serving = State()
    waiting_for_substitutions = State()
    waiting_for_category = State()
    waiting_for_time_category = State()
    waiting_for_cook_time = State()
    waiting_for_suitable = State()
    waiting_for_photo = State()
    waiting_for_new_category_name = State()
    waiting_for_setting_value = State()

class EditStates(StatesGroup):
    waiting_for_recipe_selection = State()
    waiting_for_field_selection = State()
    waiting_for_new_value = State()
    waiting_for_photo = State()
    waiting_for_const_field_selection = State()
    waiting_for_const_new_value = State()

def is_admin(user_id: int):
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def admin_start(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🛠 Панель администратора", reply_markup=get_admin_main(), protect_content=True)

@router.callback_query(F.data == "admin_add")
async def admin_add_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.set_state(AdminStates.waiting_for_title)
    await callback.message.answer("Введите название блюда (🍽 Название блюда):", protect_content=True)
    await callback.answer()

@router.message(AdminStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AdminStates.waiting_for_about)
    template = (
        "Введите 1–2 коротких предложения: зачем блюдо, польза, когда удобно.\n"
        "При необходимости добавьте обучающую сноску.\n\n"
        "⚠️ НЕ пишите заголовок '💛 О рецепте', он добавится автоматически."
    )
    await message.answer(template, protect_content=True)

@router.message(AdminStates.waiting_for_about)
async def process_about(message: types.Message, state: FSMContext):
    await state.update_data(about=clean_input(message.text, r'^💛\s*О рецепте:?\s*'))
    await state.set_state(AdminStates.waiting_for_ingredients)
    template = (
        "Введите список ингредиентов (каждый с новой строки).\n"
        "Для необязательных используйте пометку '* по желанию:'.\n\n"
        "⚠️ НЕ пишите заголовок '🛒 Ингредиенты', он добавится автоматически."
    )
    await message.answer(template, protect_content=True)

@router.message(AdminStates.waiting_for_ingredients)
async def process_ingredients(message: types.Message, state: FSMContext):
    await state.update_data(ingredients=clean_input(message.text, r'^🛒\s*Ингредиенты:?\s*'))
    await state.set_state(AdminStates.waiting_for_steps)
    template = (
        "Введите шаги приготовления (каждый с новой строки).\n\n"
        "⚠️ НЕ пишите заголовок '👩‍🍳 Приготовление', он добавится автоматически."
    )
    await message.answer(template, protect_content=True)

@router.message(AdminStates.waiting_for_steps)
async def process_steps(message: types.Message, state: FSMContext):
    await state.update_data(steps=clean_input(message.text, r'^👩‍🍳\s*Приготовление:?\s*'))
    await state.set_state(AdminStates.waiting_for_tips)
    template = (
        "Введите лайфхак или уточнение (или '-' если нет).\n\n"
        "⚠️ НЕ пишите заголовок '💡 Подсказка', он добавится автоматически."
    )
    await message.answer(template, protect_content=True)

@router.message(AdminStates.waiting_for_tips)
async def process_tips(message: types.Message, state: FSMContext):
    val = clean_input(message.text, r'^💡\s*Подсказка:?\s*')
    await state.update_data(tips=val if val != "-" else "")
    await state.set_state(AdminStates.waiting_for_serving)
    template = (
        "Введите рекомендации по подаче.\n\n"
        "⚠️ НЕ пишите заголовок '🍽 Подача', он добавится автоматически."
    )
    await message.answer(template, protect_content=True)

@router.message(AdminStates.waiting_for_serving)
async def process_serving(message: types.Message, state: FSMContext):
    await state.update_data(serving=clean_input(message.text, r'^🍽\s*Подача:?\s*'))
    await state.set_state(AdminStates.waiting_for_substitutions)
    template = (
        "Введите возможные замены (например: ингредиент → замена).\n\n"
        "⚠️ НЕ пишите заголовок '🔄 Замены', он добавится автоматически."
    )
    await message.answer(template, protect_content=True)

@router.message(AdminStates.waiting_for_substitutions)
async def process_substitutions(message: types.Message, state: FSMContext):
    await state.update_data(substitutions=clean_input(message.text, r'^🔄\s*Замены:?\s*'))
    await state.set_state(AdminStates.waiting_for_category)
    
    builder = InlineKeyboardBuilder()
    for cat in CATEGORIES:
        if cat != "Все":
            builder.row(InlineKeyboardButton(text=cat, callback_data=f"admin_cat_{cat}"))
    
    builder.row(InlineKeyboardButton(text="➕ Добавить новую категорию", callback_data="admin_add_new_cat_flow"))
    builder.adjust(2)
    await message.answer("Выберите категорию:", reply_markup=builder.as_markup(), protect_content=True)

@router.callback_query(F.data == "admin_add_new_cat_flow")
async def admin_add_new_cat_flow(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_new_category_name)
    # We'll use a flag in state to know where to return
    await state.update_data(return_to_add_recipe=True)
    await callback.message.answer("Введите название новой категории:", protect_content=True)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_cat_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.replace("admin_cat_", "")
    await state.update_data(category=category)
    await state.set_state(AdminStates.waiting_for_time_category)
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="quick (до 15)", callback_data="admin_time_quick"))
    builder.row(InlineKeyboardButton(text="medium (15-30)", callback_data="admin_time_medium"))
    builder.row(InlineKeyboardButton(text="long (есть время)", callback_data="admin_time_long"))
    await callback.message.edit_text("Выберите категорию времени:", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("admin_time_"))
async def process_time_category(callback: types.CallbackQuery, state: FSMContext):
    time_cat = callback.data.replace("admin_time_", "")
    await state.update_data(time_category=time_cat)
    await state.set_state(AdminStates.waiting_for_cook_time)
    await callback.message.answer("⏱ Время:\nВведите время приготовления цифрой (в минутах):", protect_content=True)
    await callback.answer()

@router.message(AdminStates.waiting_for_cook_time)
async def process_cook_time(message: types.Message, state: FSMContext):
    try:
        cook_time = int(message.text)
        await state.update_data(cook_time=cook_time)
        await state.set_state(AdminStates.waiting_for_suitable)
        template = (
            "Введите теги через запятую. Рекомендуемые теги:\n"
            "для детей, десерт, завтрак, перекус, для всей семьи, без глютена, без молока.\n\n"
            "⚠️ НЕ пишите заголовок '📌 Подходит', он добавится автоматически."
        )
        await message.answer(template, protect_content=True)
    except ValueError:
        await message.answer("Пожалуйста, введите число.", protect_content=True)

@router.message(AdminStates.waiting_for_suitable)
async def process_suitable(message: types.Message, state: FSMContext):
    text = clean_input(message.text, r'^📌\s*Подходит:?\s*')
    suitable = [s.strip() for s in text.replace('\n', ',').split(",")] if text != "-" else []
    # Filter out empty strings and template placeholders
    suitable = [s for s in suitable if s and s != "…"]
    await state.update_data(tags=suitable)
    await state.set_state(AdminStates.waiting_for_photo)
    await message.answer("Отправьте фото блюда или '-' если фото нет:", protect_content=True)

@router.message(AdminStates.waiting_for_photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text == "-":
        photo_id = None
    else:
        await message.answer("Пожалуйста, отправьте фото или '-'", protect_content=True)
        return

    await state.update_data(photo_id=photo_id)
    data = await state.get_data()
    
    # Автоматически определяем meal_type на основе выбранной категории
    meal_map = {
        "Каши": "Завтрак", "Завтраки из яиц": "Завтрак", "Оладушки и блины": "Завтрак", 
        "Творог и молочка": "Завтрак", "Брускеты и круассаны": "Завтрак",
        "Супы": "Обед", "Мясо": "Ужин", "Рыба": "Ужин", "Блюда из овощей": "Ужин",
        "Блюда из печени и сердца": "Ужин", "Гарниры": "Ужин", "Запеканки": "Ужин",
        "Салаты": "Ужин", "Десерты": "Десерт", "Напитки": "Напиток", 
        "Смузи для детей": "Напиток", "Горячие напитки": "Напиток", 
        "Лимонады": "Напиток", "Детокс": "Напиток", "Перекус": "Перекус",
        "Сезонные смузи": "Напиток",
        "👶 Для детей": "Обед", "👨‍👩‍👧 Для всей семьи": "Обед", "🌿 Без глютена": "Обед", 
        "🥛 Без молока": "Обед", "🥚 Без яиц": "Обед", "⚡️ Быстрые рецепты": "Обед", "💚 Лёгкие блюда": "Обед"
    }
    data['meal_type'] = meal_map.get(data.get('category'), 'Обед')
    
    await db.add_recipe(data, bot=message.bot)
    await message.answer("✅ Рецепт успешно добавлен и разослан пользователям!", reply_markup=get_admin_main(), protect_content=True)
    await state.clear()

@router.callback_query(F.data == "admin_delete_list")
async def admin_delete_list(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    recipes = await db.get_recipes_by_category("Все")
    if not recipes:
        await callback.answer("База данных пуста.", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    for r in recipes:
        builder.row(InlineKeyboardButton(text=f"❌ {r['title']}", callback_data=f"admin_del_{r['id']}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel"))
    
    await callback.message.edit_text("Выберите рецепт для УДАЛЕНИЯ:", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("admin_del_"))
async def admin_delete_recipe(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    recipe_id = int(callback.data.replace("admin_del_", ""))
    await db.delete_recipe(recipe_id)
    await callback.answer("Рецепт удален!", show_alert=True)
    # Don't call admin_delete_list(callback) directly to avoid double answer
    recipes = await db.get_recipes_by_category("Все")
    if not recipes:
        await callback.message.edit_text("База данных пуста.", reply_markup=get_admin_main())
        return
    
    builder = InlineKeyboardBuilder()
    for r in recipes:
        builder.row(InlineKeyboardButton(text=f"❌ {r['title']}", callback_data=f"admin_del_{r['id']}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel"))
    
    await callback.message.edit_text("Выберите рецепт для УДАЛЕНИЯ:", reply_markup=builder.as_markup())

# --- РЕДАКТИРОВАНИЕ ---

@router.callback_query(F.data == "admin_edit_sections")
async def admin_edit_sections_menu(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.clear() # Clear state when entering sections menu
    await callback.message.edit_text("Выберите раздел для редактирования:", reply_markup=get_admin_edit_sections())
    await callback.answer()

@router.callback_query(F.data == "admin_edit_select")
async def admin_edit_select_meal_type(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌅 Завтраки", callback_data="aemeal_Завтрак"))
    builder.row(InlineKeyboardButton(text="🍲 Обеды", callback_data="aemeal_Обед"))
    builder.row(InlineKeyboardButton(text="🌙 Ужины", callback_data="aemeal_Ужин"))
    builder.row(InlineKeyboardButton(text="🥪 Перекусы", callback_data="aemeal_Перекус"))
    builder.row(InlineKeyboardButton(text="🥗 Салаты", callback_data="aemeal_Салаты"))
    builder.row(InlineKeyboardButton(text="🥧 Запеканки", callback_data="aemeal_Запеканки"))
    builder.row(InlineKeyboardButton(text="🍰 Десерты", callback_data="aemeal_Десерт"))
    builder.row(InlineKeyboardButton(text="🍹 Напитки", callback_data="aemeal_Напиток"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_sections"))
    builder.adjust(2)
    
    await callback.message.edit_text("Выберите прием пищи для редактирования:", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("aemeal_"))
async def admin_edit_meal_subcats(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    meal_type = callback.data.replace("aemeal_", "")
    
    # Check if it's already a final category (Desserts)
    if meal_type == "Десерт":
        recipes = await db.get_recipes_by_meal_type(meal_type)
        if not recipes:
            await callback.answer(f"В разделе '{meal_type}' нет рецептов.", show_alert=True)
            return
        
        builder = InlineKeyboardBuilder()
        for r in recipes:
            builder.row(InlineKeyboardButton(text=f"📝 {r['title']}", callback_data=f"admin_edit_rec_{r['id']}"))
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_select"))
        
        await callback.message.edit_text(f"Рецепты в разделе '{meal_type}':", reply_markup=builder.as_markup())
        await callback.answer()
        return

    subcats = {
        "Завтрак": ["Каши", "Завтраки из яиц", "Оладушки и блины", "Творог и молочка", "Брускеты и круассаны"],
        "Обед": ["Супы", "Мясо", "Рыба", "Блюда из овощей", "Блюда из печени и сердца"],
        "Ужин": ["Мясо", "Рыба", "Блюда из овощей", "Блюда из печени и сердца", "Гарниры"],
        "Напиток": ["Горячие напитки", "Лимонады", "Детокс", "Смузи для детей", "Сезонные смузи"]
    }
    
    # Handle direct categories (Salads, Casseroles, Snacks)
    if meal_type in ["Салаты", "Запеканки", "Перекус"]:
        recipes = await db.get_recipes_by_category(meal_type)
        if not recipes:
            await callback.answer(f"В разделе '{meal_type}' нет рецептов.", show_alert=True)
            return
        
        builder = InlineKeyboardBuilder()
        for r in recipes:
            builder.row(InlineKeyboardButton(text=f"📝 {r['title']}", callback_data=f"admin_edit_rec_{r['id']}"))
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_select"))
        
        await callback.message.edit_text(f"Рецепты в разделе '{meal_type}':", reply_markup=builder.as_markup())
        await callback.answer()
        return
    
    current_subcats = subcats.get(meal_type, [])
    builder = InlineKeyboardBuilder()
    for cat in current_subcats:
        builder.row(InlineKeyboardButton(text=cat, callback_data=f"aemcat_{meal_type}_{cat}"))
    
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_select"))
    builder.adjust(2)
    
    await callback.message.edit_text(f"Выберите подкатегорию для {meal_type.lower()}:", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("aemcat_"))
async def admin_edit_recipe_list_by_meal(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    # Format: aemcat_{meal_type}_{category}
    parts = callback.data.split("_")
    meal_type = parts[1]
    category = "_".join(parts[2:])
    
    # Special case for Seasonal Smoothies
    if category == "Сезонные смузи":
        # Get all subcategories for seasonal smoothies
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
            ("🍌 Для спортсменов – хорош активным деткам", "ss_sport"),
            ("🍯 Для сладкоежек", "ss_sweet")
        ]
        builder = InlineKeyboardBuilder()
        for text, sub_code in subs:
            builder.row(InlineKeyboardButton(text=text, callback_data=f"aess_{sub_code}"))
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"aemeal_{meal_type}"))
        builder.adjust(2)
        await callback.message.edit_text("Выберите подраздел сезонных смузи для редактирования:", reply_markup=builder.as_markup())
        await callback.answer()
        return

    recipes = await db.get_recipes_by_meal_and_cat(meal_type, category)
        
    if not recipes:
        await callback.answer(f"В категории '{category}' для {meal_type.lower()} нет рецептов.", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    for r in recipes:
        builder.row(InlineKeyboardButton(text=f"📝 {r['title']}", callback_data=f"admin_edit_rec_{r['id']}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"aemeal_{meal_type}"))
    
    await callback.message.edit_text(f"Рецепты: {category} на {meal_type.lower()}:", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("aess_"))
async def admin_edit_seasonal_smoothie_list(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    subcat = callback.data.replace("aess_", "")
    
    tag_map = {
        "spring_summer": "весенне-летние",
        "autumn_winter": "осенне-зимние",
        "dessert": "десертные",
        "hearty": "сытное",
        "detox": "детокс",
        "immunity": "иммунитет",
        "exotic": "экзотические",
        "warm": "теплое",
        "heart": "сердце",
        "sport": "спорт",
        "sweet": "сладкое"
    }
    
    search_tag = tag_map.get(subcat)
    all_tagged = await db.get_recipes_by_tag(search_tag)
    recipes = [r for r in all_tagged if r['category'] == "Сезонные смузи"]
    
    if not recipes:
        await callback.answer("В этом подразделе нет рецептов.", show_alert=True)
        return
        
    builder = InlineKeyboardBuilder()
    for r in recipes:
        builder.row(InlineKeyboardButton(text=f"📝 {r['title']}", callback_data=f"admin_edit_rec_{r['id']}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="aemcat_Напиток_Сезонные смузи"))
    
    await callback.message.edit_text(f"Рецепты в подразделе:", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "admin_edit_tips")
async def admin_edit_tips_list(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.clear()
    
    # Tips are stored in constructors table with basis/principle as NULL
    hacks, _ = await db.get_all_tips_and_hacks()
    
    if not hacks:
        await callback.answer("Советы не найдены.", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    for h in hacks:
        builder.row(InlineKeyboardButton(text=f"💡 {h['title']}", callback_data=f"admin_econst_{h['id']}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_sections"))
    
    await callback.message.edit_text("Выберите совет для редактирования:", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "admin_edit_pdf")
async def admin_edit_pdf_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    current_val = await db.get_setting("pdf_text")
    await state.update_data(edit_setting_key="pdf_text")
    await state.set_state(AdminStates.waiting_for_setting_value)
    await callback.message.answer(f"Текущий текст PDF:\n\n{current_val}\n\nВведите новый текст (поддерживается HTML):", protect_content=True)
    await callback.answer()

@router.callback_query(F.data == "admin_edit_about")
async def admin_edit_about_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    current_val = await db.get_setting("about_text")
    await state.update_data(edit_setting_key="about_text")
    await state.set_state(AdminStates.waiting_for_setting_value)
    await callback.message.answer(f"Текущий текст 'О проекте':\n\n{current_val}\n\nВведите новый текст (поддерживается HTML):", protect_content=True)
    await callback.answer()

@router.message(AdminStates.waiting_for_setting_value)
async def process_setting_update(message: types.Message, state: FSMContext):
    data = await state.get_data()
    key = data['edit_setting_key']
    await db.update_setting(key, message.text)
    await message.answer(f"✅ Настройка '{key}' успешно обновлена!", reply_markup=get_admin_main(), protect_content=True)
    await state.clear()

@router.callback_query(F.data == "admin_edit_constructors")
async def admin_edit_constructors_list(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.clear()
    constructors = await db.get_constructors()
    if not constructors:
        await callback.answer("Конструкторы не найдены.")
        return
    
    builder = InlineKeyboardBuilder()
    for c in constructors:
        builder.row(InlineKeyboardButton(text=f"🧩 {c['title']}", callback_data=f"admin_econst_{c['id']}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_sections"))
    
    await callback.message.edit_text("Выберите конструктор для редактирования:", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("admin_edit_rec_"))
async def admin_edit_recipe_menu(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    recipe_id = int(callback.data.replace("admin_edit_rec_", ""))
    recipe = await db.get_recipe_by_id(recipe_id)
    
    if not recipe:
        await callback.answer("Рецепт не найден.")
        return
        
    await state.update_data(edit_recipe_id=recipe_id, edit_recipe_data=recipe)
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Название", callback_data="edit_field_title"))
    builder.row(InlineKeyboardButton(text="О рецепте", callback_data="edit_field_about"))
    builder.row(InlineKeyboardButton(text="Ингредиенты", callback_data="edit_field_ingredients"))
    builder.row(InlineKeyboardButton(text="Приготовление", callback_data="edit_field_steps"))
    builder.row(InlineKeyboardButton(text="Подсказка", callback_data="edit_field_tips"))
    builder.row(InlineKeyboardButton(text="Подача", callback_data="edit_field_serving"))
    builder.row(InlineKeyboardButton(text="Замены", callback_data="edit_field_substitutions"))
    builder.row(InlineKeyboardButton(text="Категория", callback_data="edit_field_category"))
    builder.row(InlineKeyboardButton(text="Фото", callback_data="edit_field_photo"))
    builder.row(InlineKeyboardButton(text="✅ Сохранить и выйти", callback_data="edit_save"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_select"))
    builder.adjust(2)
    
    await callback.message.edit_text(f"Редактирование: {recipe['title']}\nВыберите поле:", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("edit_field_"))
async def admin_edit_field_start(callback: types.CallbackQuery, state: FSMContext):
    field = callback.data.replace("edit_field_", "")
    await state.update_data(edit_field=field)
    
    templates = {
        "about": "Введите 1–2 коротких предложения.\n⚠️ НЕ пишите заголовок '💛 О рецепте'.",
        "ingredients": "Введите список ингредиентов.\n⚠️ НЕ пишите заголовок '🛒 Ингредиенты'.",
        "steps": "Введите шаги приготовления.\n⚠️ НЕ пишите заголовок '👩‍🍳 Приготовление'.",
        "tips": "Введите лайфхак или уточнение.\n⚠️ НЕ пишите заголовок '💡 Подсказка'.",
        "serving": "Введите рекомендации по подаче.\n⚠️ НЕ пишите заголовок '🍽 Подача'.",
        "substitutions": "Введите возможные замены.\n⚠️ НЕ пишите заголовок '🔄 Замены'.",
        "tags": "Введите теги через запятую (для детей, десерт, завтрак, перекус, для всей семьи).\n⚠️ НЕ пишите заголовок '📌 Подходит'."
    }
    
    template = templates.get(field, "")
    
    if field == "photo":
        await state.set_state(EditStates.waiting_for_photo)
        await callback.message.answer("Отправьте новое фото или '-' чтобы удалить фото:", protect_content=True)
    elif field == "category":
        builder = InlineKeyboardBuilder()
        for cat in CATEGORIES:
            if cat != "Все":
                builder.row(InlineKeyboardButton(text=cat, callback_data=f"edit_cat_val_{cat}"))
        builder.adjust(2)
        await callback.message.edit_text("Выберите новую категорию:", reply_markup=builder.as_markup())
    else:
        await state.set_state(EditStates.waiting_for_new_value)
        msg = f"Введите новое значение для поля '{field}':"
        if template:
            msg = f"Введите значение по шаблону:\n\n{template}"
        await callback.message.answer(msg, protect_content=True)
    await callback.answer()

@router.callback_query(F.data.startswith("edit_cat_val_"))
async def process_edit_category_value(callback: types.CallbackQuery, state: FSMContext):
    new_cat = callback.data.replace("edit_cat_val_", "")
    data = await state.get_data()
    recipe_data = data['edit_recipe_data']
    
    recipe_data['category'] = new_cat
    # Автоматически обновляем meal_type на основе категории для корректной навигации
    meal_map = {
        "Каши": "Завтрак", "Завтраки из яиц": "Завтрак", "Оладушки и блины": "Завтрак", 
        "Творог и молочка": "Завтрак", "Брускеты и круассаны": "Завтрак",
        "Супы": "Обед", "Мясо": "Ужин", "Рыба": "Ужин", "Блюда из овощей": "Ужин",
        "Блюда из печени и сердца": "Ужин", "Гарниры": "Ужин", "Запеканки": "Ужин",
        "Салаты": "Ужин", "Десерты": "Десерт", "Напитки": "Напиток", 
        "Смузи для детей": "Напиток", "Горячие напитки": "Напиток", 
        "Лимонады": "Напиток", "Детокс": "Напиток", "Перекус": "Перекус",
        "Сезонные смузи": "Напиток",
        "👶 Для детей": "Обед", "👨‍👩‍👧 Для всей семьи": "Обед", "🌿 Без глютена": "Обед", 
        "🥛 Без молока": "Обед", "🥚 Без яиц": "Обед", "⚡️ Быстрые рецепты": "Обед", "💚 Лёгкие блюда": "Обед"
    }
    recipe_data['meal_type'] = meal_map.get(new_cat, recipe_data.get('meal_type', ''))
    
    await state.update_data(edit_recipe_data=recipe_data)
    await callback.message.answer(f"Категория изменена на '{new_cat}'. Не забудьте нажать 'Сохранить'.", protect_content=True)
    
    # Возвращаемся в меню редактирования
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Название", callback_data="edit_field_title"))
    builder.row(InlineKeyboardButton(text="О рецепте", callback_data="edit_field_about"))
    builder.row(InlineKeyboardButton(text="Ингредиенты", callback_data="edit_field_ingredients"))
    builder.row(InlineKeyboardButton(text="Приготовление", callback_data="edit_field_steps"))
    builder.row(InlineKeyboardButton(text="Подсказка", callback_data="edit_field_tips"))
    builder.row(InlineKeyboardButton(text="Подача", callback_data="edit_field_serving"))
    builder.row(InlineKeyboardButton(text="Замены", callback_data="edit_field_substitutions"))
    builder.row(InlineKeyboardButton(text="Категория", callback_data="edit_field_category"))
    builder.row(InlineKeyboardButton(text="Фото", callback_data="edit_field_photo"))
    builder.row(InlineKeyboardButton(text="✅ Сохранить и выйти", callback_data="edit_save"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_select"))
    builder.adjust(2)
    
    await callback.message.answer(f"Редактирование: {recipe_data['title']}\nВыберите поле:", reply_markup=builder.as_markup(), protect_content=True)
    await callback.answer()

@router.message(EditStates.waiting_for_new_value)
async def process_edit_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data['edit_field']
    recipe_data = data['edit_recipe_data']
    
    recipe_data[field] = message.text
    await state.update_data(edit_recipe_data=recipe_data)
    
    await message.answer(f"Поле '{field}' обновлено в памяти. Не забудьте нажать 'Сохранить'.", protect_content=True)
    # Возвращаемся в меню редактирования
    recipe_id = data['edit_recipe_id']
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Название", callback_data="edit_field_title"))
    builder.row(InlineKeyboardButton(text="О рецепте", callback_data="edit_field_about"))
    builder.row(InlineKeyboardButton(text="Ингредиенты", callback_data="edit_field_ingredients"))
    builder.row(InlineKeyboardButton(text="Приготовление", callback_data="edit_field_steps"))
    builder.row(InlineKeyboardButton(text="Подсказка", callback_data="edit_field_tips"))
    builder.row(InlineKeyboardButton(text="Подача", callback_data="edit_field_serving"))
    builder.row(InlineKeyboardButton(text="Замены", callback_data="edit_field_substitutions"))
    builder.row(InlineKeyboardButton(text="Фото", callback_data="edit_field_photo"))
    builder.row(InlineKeyboardButton(text="✅ Сохранить и выйти", callback_data="edit_save"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_select"))
    builder.adjust(2)
    
    await message.answer(f"Редактирование: {recipe_data['title']}\nВыберите поле:", reply_markup=builder.as_markup(), protect_content=True)
    await state.set_state(None)

@router.message(EditStates.waiting_for_photo)
async def process_edit_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Check if we are editing a recipe or a constructor
    is_const = 'edit_const_data' in data
    item_data = data.get('edit_const_data' if is_const else 'edit_recipe_data')
    
    if message.photo:
        item_data['photo_id'] = message.photo[-1].file_id
    elif message.text == "-":
        item_data['photo_id'] = None
    else:
        await message.answer("Пожалуйста, отправьте фото или '-'", protect_content=True)
        return
        
    if is_const:
        await state.update_data(edit_const_data=item_data)
    else:
        await state.update_data(edit_recipe_data=item_data)
        
    await message.answer("Фото обновлено в памяти. Не забудьте нажать 'Сохранить'.", protect_content=True)
    
    # Возвращаемся в соответствующее меню редактирования
    builder = InlineKeyboardBuilder()
    if is_const:
        is_tip = item_data.get('basis') is None and item_data.get('principle') is None
        if is_tip:
            builder.row(InlineKeyboardButton(text="Название", callback_data="econst_field_title"))
            builder.row(InlineKeyboardButton(text="Текст совета (Лайфхаки)", callback_data="econst_field_lifehacks"))
            builder.row(InlineKeyboardButton(text="Фото", callback_data="econst_field_photo"))
        else:
            builder.row(InlineKeyboardButton(text="Название", callback_data="econst_field_title"))
            builder.row(InlineKeyboardButton(text="Подходит для", callback_data="econst_field_suitable_for"))
            builder.row(InlineKeyboardButton(text="Суть", callback_data="econst_field_principle"))
            builder.row(InlineKeyboardButton(text="Основа", callback_data="econst_field_basis"))
            builder.row(InlineKeyboardButton(text="Белок", callback_data="econst_field_protein"))
            builder.row(InlineKeyboardButton(text="Жиры", callback_data="econst_field_fats"))
            builder.row(InlineKeyboardButton(text="Клетчатка", callback_data="econst_field_fiber"))
            builder.row(InlineKeyboardButton(text="Как собрать", callback_data="econst_field_how_to_assemble"))
            builder.row(InlineKeyboardButton(text="Гибкость / Замены", callback_data="econst_field_flexibility"))
            builder.row(InlineKeyboardButton(text="Лайфхаки", callback_data="econst_field_lifehacks"))
            builder.row(InlineKeyboardButton(text="Для детей", callback_data="econst_field_kids_recommendation"))
            builder.row(InlineKeyboardButton(text="Фото", callback_data="econst_field_photo"))
        
        builder.row(InlineKeyboardButton(text="✅ Сохранить и выйти", callback_data="econst_save"))
        back_data = "admin_edit_tips" if is_tip else "admin_edit_constructors"
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=back_data))
    else:
        builder.row(InlineKeyboardButton(text="Название", callback_data="edit_field_title"))
        builder.row(InlineKeyboardButton(text="О рецепте", callback_data="edit_field_about"))
        builder.row(InlineKeyboardButton(text="Ингредиенты", callback_data="edit_field_ingredients"))
        builder.row(InlineKeyboardButton(text="Приготовление", callback_data="edit_field_steps"))
        builder.row(InlineKeyboardButton(text="Подсказка", callback_data="edit_field_tips"))
        builder.row(InlineKeyboardButton(text="Подача", callback_data="edit_field_serving"))
        builder.row(InlineKeyboardButton(text="Замены", callback_data="edit_field_substitutions"))
        builder.row(InlineKeyboardButton(text="Фото", callback_data="edit_field_photo"))
        builder.row(InlineKeyboardButton(text="✅ Сохранить и выйти", callback_data="edit_save"))
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_select"))
    
    builder.adjust(2)
    title = item_data.get('title', 'Без названия')
    await message.answer(f"Редактирование: {title}\nВыберите поле:", reply_markup=builder.as_markup(), protect_content=True)
    await state.set_state(None)

@router.callback_query(F.data == "edit_save")
async def admin_edit_save(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    recipe_id = data['edit_recipe_id']
    recipe_data = data['edit_recipe_data']
    
    # Ensure tags are a list, not double-encoded string
    if isinstance(recipe_data.get('tags'), str):
        tags_str = recipe_data['tags']
        # Try to decode if it's already JSON
        try:
            while isinstance(tags_str, str) and (tags_str.startswith('[') or tags_str.startswith('"')):
                new_val = json.loads(tags_str)
                if new_val == tags_str: break
                tags_str = new_val
        except:
            pass
            
        if isinstance(tags_str, list):
            recipe_data['tags'] = tags_str
        else:
            # If it's a plain string, split by commas or newlines
            recipe_data['tags'] = [t.strip() for t in tags_str.replace('\n', ',').split(',') if t.strip() and t != "…"]

    await db.update_recipe(recipe_id, recipe_data)
    await callback.answer("✅ Изменения сохранены!", show_alert=True)
    await state.clear()
    await callback.message.edit_text("🛠 Панель администратора", reply_markup=get_admin_main())

@router.callback_query(F.data.startswith("admin_econst_"))
async def admin_edit_const_menu(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    const_id = int(callback.data.replace("admin_econst_", ""))
    constructor = await db.get_constructor_by_id(const_id)
    
    if not constructor:
        await callback.answer("Конструктор не найден.")
        return
        
    await state.update_data(edit_const_id=const_id, edit_const_data=constructor)
    
    # Check if it's a tip (no basis and no principle)
    is_tip = constructor.get('basis') is None and constructor.get('principle') is None
    
    builder = InlineKeyboardBuilder()
    if is_tip:
        builder.row(InlineKeyboardButton(text="Название", callback_data="econst_field_title"))
        builder.row(InlineKeyboardButton(text="Текст совета (Лайфхаки)", callback_data="econst_field_lifehacks"))
        builder.row(InlineKeyboardButton(text="Фото", callback_data="econst_field_photo"))
    else:
        builder.row(InlineKeyboardButton(text="Название", callback_data="econst_field_title"))
        builder.row(InlineKeyboardButton(text="Подходит для", callback_data="econst_field_suitable_for"))
        builder.row(InlineKeyboardButton(text="Суть", callback_data="econst_field_principle"))
        builder.row(InlineKeyboardButton(text="Основа", callback_data="econst_field_basis"))
        builder.row(InlineKeyboardButton(text="Белок", callback_data="econst_field_protein"))
        builder.row(InlineKeyboardButton(text="Жиры", callback_data="econst_field_fats"))
        builder.row(InlineKeyboardButton(text="Овощи / клетчатка", callback_data="econst_field_fiber"))
        builder.row(InlineKeyboardButton(text="Как собрать", callback_data="econst_field_how_to_assemble"))
        builder.row(InlineKeyboardButton(text="Гибкость / Замены", callback_data="econst_field_flexibility"))
        builder.row(InlineKeyboardButton(text="Лайфхаки", callback_data="econst_field_lifehacks"))
        builder.row(InlineKeyboardButton(text="Для детей", callback_data="econst_field_kids_recommendation"))
        builder.row(InlineKeyboardButton(text="Фото", callback_data="econst_field_photo"))
    
    builder.row(InlineKeyboardButton(text="✅ Сохранить и выйти", callback_data="econst_save"))
    
    back_data = "admin_edit_tips" if is_tip else "admin_edit_constructors"
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=back_data))
    builder.adjust(2)
    
    item_type = "совета" if is_tip else "конструктора"
    await callback.message.edit_text(f"Редактирование {item_type}: {constructor['title']}\nВыберите поле:", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("econst_field_"))
async def admin_edit_const_field_start(callback: types.CallbackQuery, state: FSMContext):
    field = callback.data.replace("econst_field_", "")
    await state.update_data(edit_const_field=field)
    
    templates = {
        "suitable_for": "Введите, кому подходит.\n⚠️ НЕ пишите заголовок '⏱ Подходит для'.",
        "principle": "Введите суть принципа.\n⚠️ НЕ пишите заголовок '💛 Суть'.",
        "basis": "Введите основу.\n⚠️ НЕ пишите заголовок '📦 Основа'.",
        "protein": "Введите белок.\n⚠️ НЕ пишите заголовок '🍗 Белок'.",
        "fats": "Введите жиры.\n⚠️ НЕ пишите заголовок '🥑 Жиры'.",
        "fiber": "Введите овощи / клетчатку.\n⚠️ НЕ пишите заголовок '🥬 Овощи / клетчатка'.",
        "how_to_assemble": "Введите, как собрать.\n⚠️ НЕ пишите заголовок '👨‍🍳 Как собрать'.",
        "flexibility": "Введите замены.\n⚠️ НЕ пишите заголовок '🔄 Замены'.",
        "lifehacks": "Введите лайфхаки.\n⚠️ НЕ пишите заголовок '✨ Лайфхаки'.",
        "kids_recommendation": "Введите рекомендации для детей.\n⚠️ НЕ пишите заголовок '👶 Для детей'."
    }
    
    template = templates.get(field, "")
    
    if field == "photo":
        await state.set_state(EditStates.waiting_for_photo) # Reuse photo state
        await callback.message.answer("Отправьте новое фото для конструктора или '-' чтобы удалить фото:", protect_content=True)
    else:
        await state.set_state(EditStates.waiting_for_const_new_value)
        msg = f"Введите новое значение для поля '{field}':"
        if template:
            msg = f"Введите значение по шаблону:\n\n{template}"
        await callback.message.answer(msg, protect_content=True)
    await callback.answer()

@router.message(EditStates.waiting_for_const_new_value)
async def process_edit_const_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data['edit_const_field']
    const_data = data['edit_const_data']
    
    const_data[field] = message.text
    await state.update_data(edit_const_data=const_data)
    
    await message.answer(f"Поле '{field}' обновлено в памяти. Не забудьте нажать 'Сохранить'.", protect_content=True)
    
    # Возвращаемся в меню редактирования конструктора
    is_tip = const_data.get('basis') is None and const_data.get('principle') is None
    builder = InlineKeyboardBuilder()
    if is_tip:
        builder.row(InlineKeyboardButton(text="Название", callback_data="econst_field_title"))
        builder.row(InlineKeyboardButton(text="Текст совета (Лайфхаки)", callback_data="econst_field_lifehacks"))
        builder.row(InlineKeyboardButton(text="Фото", callback_data="econst_field_photo"))
    else:
        builder.row(InlineKeyboardButton(text="Название", callback_data="econst_field_title"))
        builder.row(InlineKeyboardButton(text="Подходит для", callback_data="econst_field_suitable_for"))
        builder.row(InlineKeyboardButton(text="Суть", callback_data="econst_field_principle"))
        builder.row(InlineKeyboardButton(text="Основа", callback_data="econst_field_basis"))
        builder.row(InlineKeyboardButton(text="Белок", callback_data="econst_field_protein"))
        builder.row(InlineKeyboardButton(text="Жиры", callback_data="econst_field_fats"))
        builder.row(InlineKeyboardButton(text="Клетчатка", callback_data="econst_field_fiber"))
        builder.row(InlineKeyboardButton(text="Как собрать", callback_data="econst_field_how_to_assemble"))
        builder.row(InlineKeyboardButton(text="Гибкость / Замены", callback_data="econst_field_flexibility"))
        builder.row(InlineKeyboardButton(text="Лайфхаки", callback_data="econst_field_lifehacks"))
        builder.row(InlineKeyboardButton(text="Для детей", callback_data="econst_field_kids_recommendation"))
        builder.row(InlineKeyboardButton(text="Фото", callback_data="econst_field_photo"))
    
    builder.row(InlineKeyboardButton(text="✅ Сохранить и выйти", callback_data="econst_save"))
    back_data = "admin_edit_tips" if is_tip else "admin_edit_constructors"
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=back_data))
    builder.adjust(2)
    
    item_type = "совета" if is_tip else "конструктора"
    await message.answer(f"Редактирование {item_type}: {const_data['title']}\nВыберите поле:", reply_markup=builder.as_markup(), protect_content=True)
    await state.set_state(None)

@router.callback_query(F.data == "econst_save")
async def admin_edit_const_save(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    const_id = data['edit_const_id']
    const_data = data['edit_const_data']
    
    await db.update_constructor(const_id, const_data)
    await callback.answer("✅ Конструктор сохранен!", show_alert=True)
    await state.clear()
    await callback.message.edit_text("Выберите раздел для редактирования:", reply_markup=get_admin_edit_sections())

@router.callback_query(F.data == "admin_edit_categories")
async def admin_categories_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Добавить категорию", callback_data="admin_cat_add"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_sections"))
    
    text = "📁 <b>Управление категориями</b>\n\nТекущие категории:\n" + "\n".join([f"• {c}" for c in CATEGORIES if c != "Все"])
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_cat_add")
async def admin_cat_add_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.set_state(AdminStates.waiting_for_new_category_name)
    await callback.message.answer("Введите название новой категории:", protect_content=True)
    await callback.answer()

@router.message(AdminStates.waiting_for_new_category_name)
async def process_new_category(message: types.Message, state: FSMContext):
    new_cat = message.text.strip()
    data = await state.get_data()
    return_to_add = data.get('return_to_add_recipe', False)
    
    if new_cat and new_cat not in CATEGORIES:
        CATEGORIES.append(new_cat)
        # Сохраняем в файл, чтобы не пропало после перезагрузки
        try:
            with open("bot/keyboards/inline.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Находим список CATEGORIES и добавляем туда новую категорию
            # Используем более надежный способ замены
            cat_list_str = "CATEGORIES = [\n    " + ",\n    ".join([f'"{c}"' for c in CATEGORIES]) + "\n]"
            new_content = re.sub(r'CATEGORIES = \[.*?\]', cat_list_str, content, flags=re.DOTALL)
            
            with open("bot/keyboards/inline.py", "w", encoding="utf-8") as f:
                f.write(new_content)
                
            await message.answer(f"✅ Категория '{new_cat}' успешно добавлена!", protect_content=True)
            
            if return_to_add:
                # Возвращаемся к выбору категории в процессе добавления рецепта
                await state.set_state(AdminStates.waiting_for_category)
                builder = InlineKeyboardBuilder()
                for cat in CATEGORIES:
                    if cat != "Все":
                        builder.row(InlineKeyboardButton(text=cat, callback_data=f"admin_cat_{cat}"))
                builder.row(InlineKeyboardButton(text="➕ Добавить новую категорию", callback_data="admin_add_new_cat_flow"))
                builder.adjust(2)
                await message.answer("Теперь выберите категорию для рецепта:", reply_markup=builder.as_markup(), protect_content=True)
            else:
                await message.answer("🛠 Панель администратора", reply_markup=get_admin_main(), protect_content=True)
                await state.clear()
        except Exception as e:
            await message.answer(f"❌ Ошибка при сохранении категории: {e}", protect_content=True)
            if not return_to_add:
                await state.clear()
    else:
        await message.answer("Такая категория уже существует или название пустое.", protect_content=True)
        if not return_to_add:
            await state.clear()
        else:
            # Show the category selection again even if adding failed
            await state.set_state(AdminStates.waiting_for_category)
            builder = InlineKeyboardBuilder()
            for cat in CATEGORIES:
                if cat != "Все":
                    builder.row(InlineKeyboardButton(text=cat, callback_data=f"admin_cat_{cat}"))
            builder.row(InlineKeyboardButton(text="➕ Добавить новую категорию", callback_data="admin_add_new_cat_flow"))
            builder.adjust(2)
            await message.answer("Выберите категорию из списка:", reply_markup=builder.as_markup(), protect_content=True)

@router.callback_query(F.data == "admin_panel")
async def back_to_admin_panel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🛠 Панель администратора", reply_markup=get_admin_main())
    await callback.answer()
