from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, FSInputFile
from bot.keyboards.inline import (
    get_main_menu, get_categories_main_keyboard, get_product_categories_keyboard, get_recipe_list_keyboard,
    get_time_selection, get_tag_selection, get_tips_keyboard, get_final_options, get_back_button,
    get_meal_type_keyboard, get_subcategories_keyboard, get_constructor_list_keyboard,
    get_cooking_tips_keyboard, get_seasonal_smoothies_keyboard, get_related_recipes_keyboard,

)
from bot.database.db import db
from config import is_admin, is_new_bot
import json
import re

router = Router()

class UserStates(StatesGroup):
    waiting_for_search = State()
    waiting_for_time = State()
    waiting_for_tag = State()
    waiting_for_plan_time = State()
    waiting_for_plan_tag = State()

def _deduplicate_by_title(recipes: list) -> list:
    """Дедупликация списка рецептов по названию (приоритет рецептам с фото)."""
    best: Dict[str, dict] = {}
    for r in recipes:
        title = (r.get("title") or "").strip().lower()
        if not title:
            continue
        has_photo = r.get("photo_id") is not None
        prev = best.get(title)
        if prev is None:
            best[title] = r
        else:
            prev_has_photo = prev.get("photo_id") is not None
            # Заменяем, если у текущего есть фото, а у старого нет
            if has_photo and not prev_has_photo:
                best[title] = r
            # Если наличие фото одинаковое, оставляем старый (с меньшим ID)
    
    # Сохраняем оригинальный порядок (насколько это возможно)
    return list(best.values())

def _parse_recipe_tags(tags_val):
    """Разбирает теги рецепта, скрывая служебные (related:123)."""
    display_tags = []
    if not tags_val:
        return display_tags

    parsed = tags_val
    while isinstance(parsed, str) and (parsed.startswith('[') or parsed.startswith('"')):
        try:
            new_val = json.loads(parsed)
            if new_val == parsed:
                break
            parsed = new_val
        except json.JSONDecodeError:
            break

    if isinstance(parsed, list):
        raw_tags = parsed
    elif isinstance(parsed, str):
        raw_tags = [t.strip() for t in parsed.split('\n') if t.strip()]
    else:
        raw_tags = []

    for tag in raw_tags:
        if not isinstance(tag, str):
            continue
        clean = tag.strip()
        if re.match(r"^related:\d+$", clean, re.IGNORECASE):
            continue
        display_tags.append(clean)
    return display_tags

def _extract_related_recipes(r) -> list:
    """Связанные рецепты из тегов related:N и известных пар в базе."""
    related = []
    raw_tags = r.get("tags")
    if raw_tags:
        parsed = raw_tags
        while isinstance(parsed, str) and (parsed.startswith("[") or parsed.startswith('"')):
            try:
                new_val = json.loads(parsed)
                if new_val == parsed:
                    break
                parsed = new_val
            except json.JSONDecodeError:
                break
        tag_items = parsed if isinstance(parsed, list) else []
        for tag in tag_items:
            if isinstance(tag, str) and re.match(r"^related:(\d+)$", tag.strip(), re.IGNORECASE):
                related.append({"id": int(tag.split(":")[1]), "label": None})

    return _dedupe_related(related, exclude_id=r.get("id"))

# (ключевые слова в названии рецепта) → название связанного рецепта в базе
RECIPE_RELATED_RULES = (
    (("конвертик", "говядин"), "Запечённая рваная говядина"),
    (("тост", "хумус"), "Хумус"),
)

async def build_related_for_recipe(r: dict) -> list:
    """Связанные рецепты с подписями и кнопки по правилам RECIPE_RELATED_RULES."""
    _, related = format_recipe(r)
    resolved = await _resolve_related_labels(related)

    title = (r.get("title") or "").lower()
    already = {x["id"] for x in resolved}
    for keywords, linked_title in RECIPE_RELATED_RULES:
        if not all(k in title for k in keywords):
            continue
        linked = await db.find_recipe_by_title(linked_title)
        if linked and linked["id"] != r.get("id") and linked["id"] not in already:
            resolved.append({"id": linked["id"], "label": linked["title"]})
            already.add(linked["id"])
    return resolved

def _clean_recipe_label(label: str) -> str:
    return label.strip().strip('«»" ')

def _parse_recipe_refs(text: str) -> tuple[str, list]:
    """[[recipe:ID:название]] и старые <a href=...start=recipe_ID> → текст + список связей."""
    related = []

    def add_related(rid: int, label: str):
        related.append({"id": rid, "label": _clean_recipe_label(label)})

    def repl_bracket(match):
        add_related(int(match.group(1)), match.group(2))
        return f"«{_clean_recipe_label(match.group(2))}»"

    text = re.sub(r'\[\[recipe:(\d+):([^\]]+)\]\]', repl_bracket, text)

    def repl_html(match):
        url_match = re.search(r'start=recipe_(\d+)', match.group(1))
        label = match.group(2)
        if url_match:
            add_related(int(url_match.group(1)), label)
        return f"«{_clean_recipe_label(label)}»"

    text = re.sub(r'<a href="([^"]+)">([^<]+)</a>', repl_html, text, flags=re.IGNORECASE)
    return text, related

def _dedupe_related(related: list, exclude_id: int = None) -> list:
    seen = set()
    result = []
    for item in related:
        rid = item["id"]
        if rid == exclude_id or rid in seen:
            continue
        seen.add(rid)
        result.append(item)
    return result

def format_recipe(r, bot_username: str = None):
    text = f"🍽 <b>{r['title']}</b>\n\n"
    related = []
    
    if r.get('cook_time'):
        text += f"⏱ Время:\n- {r['cook_time']} минут\n\n"
    
    text += "---\n\n"

    if r.get('about'):
        text += f"💛 О рецепте:\n"
        about_text = r['about'].strip()
        # Remove header if user included it
        about_text = re.sub(r'^💛\s*О рецепте:?\s*', '', about_text, flags=re.IGNORECASE | re.MULTILINE)
        about_text, about_related = _parse_recipe_refs(about_text)
        related.extend(about_related)
        for line in about_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('📌'):
                text += f"{line}\n"
            elif line.startswith('«') or line.startswith('"'):
                text += f"{line}\n"
            else:
                text += f"- {line}\n"
        text += "\n---\n\n"
        
    if r.get('ingredients'):
        text += f"🛒 Ингредиенты:\n"
        ing_text = r['ingredients'].strip()
        # Remove header if user included it
        ing_text = re.sub(r'^🛒\s*Ингредиенты:?\s*', '', ing_text, flags=re.IGNORECASE | re.MULTILINE)
        ings = ing_text.split('\n')
        main_ings = []
        optional_ings = []
        is_optional = False
        
        for line in ings:
            line = line.strip()
            if not line: continue
            if "по желанию" in line.lower() or line.startswith("*"):
                is_optional = True
                clean_line = re.sub(r'^\*?\s*по желанию:?\s*', '', line, flags=re.IGNORECASE)
                if clean_line:
                    optional_ings.append(clean_line)
                continue
            
            if is_optional:
                optional_ings.append(line)
            else:
                main_ings.append(line)
        
        for ing in main_ings:
            clean_ing = re.sub(r'^[📌—\-•]\s*', '', ing)
            text += f"- {clean_ing}\n"
            
        if optional_ings:
            text += "\n*по желанию:\n"
            for ing in optional_ings:
                clean_ing = re.sub(r'^[📌—\-•]\s*', '', ing)
                text += f"- {clean_ing}\n"
        text += "\n---\n\n"
        
    if r.get('steps'):
        text += f"👩‍🍳 Приготовление:\n"
        steps_text = r['steps'].strip()
        # Remove header if user included it
        steps_text = re.sub(r'^👩‍🍳\s*Приготовление:?\s*', '', steps_text, flags=re.IGNORECASE | re.MULTILINE)
        steps = steps_text.split('\n')
        for line in steps:
            line = line.strip()
            if not line: continue
            clean_step = re.sub(r'^(\d+\.|\-|•)\s*', '', line)
            text += f"- {clean_step}\n"
        text += "\n---\n\n"
        
    if r.get('tips'):
        text += f"💡 Подсказка:\n"
        tips_text = r['tips'].strip()
        # Remove header if user included it
        tips_text = re.sub(r'^💡\s*Подсказка:?\s*', '', tips_text, flags=re.IGNORECASE | re.MULTILINE)
        for line in tips_text.split('\n'):
            if line.strip():
                text += f"- {line.strip()}\n"
        text += "\n---\n\n"
        
    if r.get('serving'):
        text += f"🍽 Подача:\n"
        serving_text = r['serving'].strip()
        # Remove header if user included it
        serving_text = re.sub(r'^🍽\s*Подача:?\s*', '', serving_text, flags=re.IGNORECASE | re.MULTILINE)
        for line in serving_text.split('\n'):
            if line.strip():
                text += f"- {line.strip()}\n"
        text += "\n---\n\n"
        
    if r.get('substitutions'):
        text += f"🔄 Замены:\n"
        subs_text = r['substitutions'].strip()
        # Remove header if user included it
        subs_text = re.sub(r'^🔄\s*Замены:?\s*', '', subs_text, flags=re.IGNORECASE | re.MULTILINE)
        subs = subs_text.split('\n')
        for line in subs:
            line = line.strip()
            if not line: continue
            clean_sub = re.sub(r'^[—\-•]\s*', '', line)
            clean_sub = clean_sub.replace("->", "→").replace("—", "→")
            if "→" not in clean_sub and ":" in clean_sub:
                clean_sub = clean_sub.replace(":", " →", 1)
            text += f"- {clean_sub}\n"
        text += "\n---\n\n"
        
    suitable_tags = _parse_recipe_tags(r.get('tags'))
    related.extend(_extract_related_recipes(r))
    
    if suitable_tags:
        text += "📌 Подходит:\n"
        for tag in suitable_tags:
            # Remove header if it leaked into tags
            tag = re.sub(r'^📌\s*Подходит:?\s*', '', tag, flags=re.IGNORECASE)
            clean_tag = re.sub(r'^[—\-•]\s*', '', tag.strip())
            if clean_tag and not re.match(r"^related:\d+$", clean_tag, re.IGNORECASE):
                text += f"- {clean_tag}\n"
            
    return text.strip().rstrip('-').strip(), _dedupe_related(related, exclude_id=r.get('id'))

async def _resolve_related_labels(related: list) -> list:
    """Подписи кнопок — полное название из базы или уже заданная подпись."""
    resolved = []
    for item in related:
        if item.get("label"):
            resolved.append({"id": item["id"], "label": item["label"]})
            continue
        recipe = await db.get_recipe_by_id(item["id"])
        if recipe:
            resolved.append({"id": item["id"], "label": recipe["title"]})
    return resolved

async def _send_recipe(message: types.Message, recipe: dict, user_id: int, related: list = None):
    text, parsed_related = format_recipe(recipe)
    if related is None:
        related = await _resolve_related_labels(parsed_related)
    markup = get_related_recipes_keyboard(related)
    protect = not is_admin(user_id)

    if recipe.get('photo_id'):
        if len(text) <= 1024:
            await message.answer_photo(
                recipe['photo_id'],
                caption=text,
                parse_mode="HTML",
                protect_content=protect,
                reply_markup=markup,
            )
        else:
            await message.answer_photo(recipe['photo_id'], protect_content=protect)
            await message.answer(text, parse_mode="HTML", protect_content=protect, reply_markup=markup)
    else:
        await message.answer(text, parse_mode="HTML", protect_content=protect, reply_markup=markup)

def format_constructor(c):
    title = c['title'].strip().rstrip(':')
    text = f"🧩 <b>Конструктор: {title}</b>\n\n"
    
    def format_list(val, header_pattern=None):
        if not val: return ""
        val_str = str(val).strip()
        if header_pattern:
            val_str = re.sub(header_pattern, '', val_str, flags=re.IGNORECASE | re.MULTILINE)
            
        lines = val_str.strip().split('\n')
        formatted = []
        for line in lines:
            line = line.strip()
            if not line: continue
            # Split by / or ; if it's a single line list
            if len(lines) == 1 and ('/' in line or ';' in line):
                parts = re.split(r'[/;]', line)
                for p in parts:
                    p = p.strip()
                    if p:
                        # Remove existing bullets
                        p = re.sub(r'^[📌—\-•]\s*', '', p)
                        formatted.append(f"- {p}")
            else:
                # Remove existing bullets or numbers
                line = re.sub(r'^(\d+\.|\-|📌|—|•)\s*', '', line)
                if line:
                    formatted.append(f"- {line}")
        return "\n".join(formatted)

    if c.get('suitable_for') and str(c['suitable_for']).lower() != 'none':
        res = format_list(c['suitable_for'], r'^⏱\s*Подходит для:?\s*')
        text += f"⏱ Подходит для:\n{res}\n\n"
        
    if c.get('principle') and str(c['principle']).lower() != 'none':
        res = format_list(c['principle'], r'^💛\s*Суть:?\s*')
        text += f"💛 Суть:\n{res}\n\n"
        
    text += "---\n\n"
    
    is_lemonade = "лимонад" in title.lower()
    
    if c.get('basis') and str(c['basis']).lower() != 'none':
        res = format_list(c['basis'], r'^📦\s*Основа:?\s*')
        text += f"📦 Основа:\n{res}\n\n"
        
    # For lemonade, protein is fruits, fats is sweetener, fiber is herbs
    if is_lemonade:
        if c.get('protein') and str(c['protein']).lower() != 'none':
            res = format_list(c['protein'], r'^🥗\s*Основные ингредиенты:?\s*')
            text += f"🥗 Основные ингредиенты:\n{res}\n\n"
        if c.get('fats') and str(c['fats']).lower() != 'none':
            res = format_list(c['fats'], r'^🌿\s*Дополнительно\s*\(сладкое\):?\s*')
            text += f"🌿 Дополнительно (сладкое):\n{res}\n\n"
        if c.get('fiber') and str(c['fiber']).lower() != 'none':
            res = format_list(c['fiber'], r'^🌿\s*Дополнительно\s*\(травы\):?\s*')
            text += f"🌿 Дополнительно (травы):\n{res}\n\n"
    else:
        if c.get('protein') and str(c['protein']).lower() != 'none':
            res = format_list(c['protein'], r'^🍗\s*Белок:?\s*')
            text += f"🍗 Белок:\n{res}\n\n"
        if c.get('fats') and str(c['fats']).lower() != 'none':
            res = format_list(c['fats'], r'^🥑\s*Жиры:?\s*')
            text += f"🥑 Жиры:\n{res}\n\n"
        if c.get('fiber') and str(c['fiber']).lower() != 'none':
            res = format_list(c['fiber'], r'^🥬\s*Овощи\s*/\s*клетчатка:?\s*')
            text += f"🥬 Овощи / клетчатка:\n{res}\n\n"
            
    if c.get('flexibility') and str(c['flexibility']).lower() != 'none':
        flex = str(c['flexibility'])
        # Remove header if exists
        flex = re.sub(r'^🔄\s*Замены:?\s*|^🌿\s*Дополнительно:?\s*', '', flex, flags=re.IGNORECASE | re.MULTILINE)
        if "замен" in flex.lower() or "→" in flex or "->" in flex:
            res = format_list(flex.replace('->', '→'))
            text += f"🔄 Замены:\n{res}\n\n"
        else:
            res = format_list(flex)
            text += f"🌿 Дополнительно:\n{res}\n\n"
            
    text += "---\n\n"
    
    if c.get('how_to_assemble') and str(c['how_to_assemble']).lower() != 'none':
        assemble = str(c['how_to_assemble'])
        # Remove header
        assemble = re.sub(r'^👨‍🍳\s*Как собрать:?\s*', '', assemble, flags=re.IGNORECASE | re.MULTILINE)
        if "например" in assemble.lower():
            # Split into "How to assemble" and "Example"
            parts = re.split(r'(?i)например:?', assemble)
            if parts[0].strip():
                res = format_list(parts[0])
                text += f"👨‍🍳 Как собрать:\n{res}\n\n---\n\n"
            if len(parts) > 1 and parts[1].strip():
                res = format_list(parts[1], r'^💡\s*Пример сочетания:?\s*')
                text += f"💡 Пример сочетания:\n{res}\n\n---\n\n"
        else:
            res = format_list(assemble)
            text += f"👨‍🍳 Как собрать:\n{res}\n\n---\n\n"
            
    if c.get('lifehacks') and str(c['lifehacks']).lower() != 'none':
        res = format_list(c['lifehacks'], r'^✨\s*Лайфхаки:?\s*')
        text += f"✨ Лайфхаки:\n{res}\n\n---\n\n"
        
    if c.get('kids_recommendation') and str(c['kids_recommendation']).lower() != 'none':
        res = format_list(c['kids_recommendation'], r'^👶\s*Для детей:?\s*')
        text += f"👶 Для детей:\n{res}\n\n"
        
    return text.strip().rstrip('-').strip()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    # Check for invite code in /start command
    args = message.text.split()
    invite_code = args[1] if len(args) > 1 else None
    
    # Get current secret from settings
    secret = await db.get_setting("join_secret", "lite_kitchen_2026")
    
    if invite_code == secret:
        if not user:
            await db.add_user(user_id, has_access=True)
        else:
            await db.grant_access(user_id)
        user = await db.get_user(user_id) # Refresh user data
    
    # If still no access and not admin, show access denied
    if not is_admin(user_id) and (not user or not user.get('has_access')):
        text = (
            "⚠️ <b>Доступ ограничен</b>\n\n"
            "Этот бот является закрытым. Доступ предоставляется только по специальной ссылке администратора.\n\n"
            "Если вы приобрели доступ, пожалуйста, воспользуйтесь ссылкой, которую вам прислали."
        )
        await message.answer(text, parse_mode="HTML")
        return

    if invite_code and invite_code.startswith("recipe_"):
        try:
            linked_id = int(invite_code.split("_", 1)[1])
            linked = await db.get_recipe_by_id(linked_id)
            if linked:
                await _send_recipe(message, linked, user_id)
                return
        except (ValueError, IndexError):
            pass

    if not user or not user['is_onboarded']:
        welcome_text = (
            "Привет!\n"
            "Создатель идеи создать «легкую кухню» для каждой мамы Чекунова Диана!\n\n"
            "Чем этот бот вам полезен:\n\n"
            "🌱 задача показать разные варианты приготовления одного и того же блюда через конструктор, а не привязать вас к определенному рецепту! Выбирайте вкус и текстуру, которую ценит ваша семья\n\n"
            "🌱 я подберу вам рецепт под прием пищи, чтобы вы заранее могли его спланировать\n\n"
            "🌱 не знаете, что приготовить? Введите имеющиеся продукты или время, которым вы располагаете на готовку\n\n"
            "🌱 в некоторых рецептах вы можете менять продукты, альтернативы указаны в самом рецепте\n\n"
            "🌱 отдельно вынесены лайфхаки по группам продуктов (каши, омлеты, гарниры) для вашего удобства\n\n"
            "🌱 есть гайды, которые вы можете скачать и использовать их в любой удобный вам момент"
        )
        await message.answer(welcome_text, protect_content=not is_admin(message.from_user.id))
        if not user:
            # Only add if doesn't exist, to avoid overwriting has_access
            await db.add_user(message.from_user.id)
        await db.set_onboarded(message.from_user.id)
    
    await message.answer(
        "🤖 Добро пожаловать!\nПомогу быстро подобрать рецепт или воспользоваться конструктором 🙂",
        reply_markup=get_main_menu(is_new=is_new_bot(message.bot)),
        protect_content=not is_admin(message.from_user.id)
    )

@router.callback_query(F.data == "start")
async def back_to_start(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🤖 Добро пожаловать!\nПомогу быстро подобрать рецепт или воспользоваться конструктором 🙂",
        reply_markup=get_main_menu(is_new=is_new_bot(callback.bot))
    )
    await callback.answer()

# NEW SECTIONS FOR BOT 2
@router.callback_query(F.data == "new_photo")
async def show_new_photo(callback: types.CallbackQuery):
    text = (
        "📸 <b>ФОТО до встречи</b>\n\n"
        "До встречи мне важно оценить и внешний вид, поэтому направьте мне пожалуйста фото:\n\n"
        "1. В полный рост в нижнем белье: взгляд в камеру, фото сбоку, со спины\n"
        "2. Лица при дневном освещении крупным планом без косметики\n"
        "3. Фото ногтей на руках и на ногах при дневном освещении (если не покрыты лаком)\n"
        "4. Фото языка сразу после пробуждения до чистки зубов и завтрака (меня интересует налет и следы от зубов)\n"
        "5. Фото тех мест, которые на теле беспокоят (высыпания / сухие пятна и тд)"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Отправить Диане в TG", url="https://t.me/diaChe"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="start"))
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "new_analysis")
async def show_new_analysis(callback: types.CallbackQuery):
    text = (
        "🧪 <b>АНАЛИЗЫ</b>\n\n"
        "После того, как вы заполните анкету, я направлю вам в личные сообщения список анализов и заказ в приложении HelloDoc на них со скидкой.\n\n"
        "<b>Вы можете выбрать, как вам удобно пройти лабораторную диагностику, есть несколько способов:</b>\n"
        "1. Пойти официальным путем через направление от педиатра / терапевта\n"
        "2. Сдать в привычной лаборатории по моему списку\n"
        "3. Вызвать специалиста лаборатории на дом и опять же по списку от меня выбрать необходимые обследования\n"
        "4. Получить от меня заказ в приложении, ничего не выбирать и не искать, кроме удобной лаборатории.\n\n"
        "Ниже по кнопкам вы найдете:\n"
        "1. Гайд для подготовки к анализам НЮАНСЫ некоторых анализов, но все же рекомендую зайти на сайт лаборатории и ознакомиться и там тоже для чистоты результатов\n"
        "2. Аудиопояснение про приложение\n"
        "3. Анкеты"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📄 ГАЙД и нюансы", callback_data="new_guide"))
    builder.row(InlineKeyboardButton(text="📲 Приложение HelloDoc", url="https://hellodoc.app/s/6pt4e/"))
    builder.row(InlineKeyboardButton(text="📋 Анкеты", callback_data="new_forms"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="start"))
    builder.adjust(1)
    
    # Send voice message about HelloDoc
    voice_path = "assets/bot_media/prilojenie_HelloDoc.ogg"
    try:
        await callback.message.answer_voice(FSInputFile(voice_path), caption="🎙 Аудиопояснение про приложение HelloDoc")
    except Exception as e:
        print(f"Error sending voice: {e}")

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "new_guide")
async def show_new_guide(callback: types.CallbackQuery):
    text = (
        "📄 <b>Гайд по подготовке к анализам</b>\n\n"
        "Забирайте Гайд по подготовке к анализам ниже и уделите время прослушиванию аудио про 💩"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад к анализам", callback_data="new_analysis"))
    
    # Send PDF file
    pdf_path = "assets/bot_media/gayd_ANALIZY.pdf"
    try:
        await callback.message.answer_document(
            FSInputFile(pdf_path), 
            caption="📄 Гайд АНАЛИЗЫ Чекунова Диана"
        )
    except Exception as e:
        print(f"Error sending PDF: {e}")

    # Send voice message about analysis nuances
    voice_path = "assets/bot_media/kal_-_nyuansyi_analiza.ogg"
    try:
        await callback.message.answer_voice(FSInputFile(voice_path), caption="🎙 Аудио про нюансы анализов")
    except Exception as e:
        print(f"Error sending voice: {e}")

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "new_diary")
async def show_new_diary(callback: types.CallbackQuery):
    text = (
        "📝 <b>ДНЕВНИК ПИТАНИЯ</b>\n\n"
        "Вам нужно записывать всю еду в течение 3-5 дней.\n"
        "- Проще все фотографировать и потом по галерее вечером записывать со временем приема пищи\n"
        "- Несколько фото с тарелкой мне так же потребуются (пример на картинке выше)\n"
        "- Не забывайте записывать жидкости, которые вы пьете\n"
        "ДЕТКИ:\n"
        "- Если речь о питании в учебном заведении - попросите там меню на эти дни и желательно обратную связь педагога, что ребенок ест\n\n"
        "Не забудьте послушать аудио 😉"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 ПРИМЕР дневника питания", callback_data="new_diary_example"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="start"))
    
    # Send plate example photo
    photo_path = "assets/bot_media/diary_plate.png"
    try:
        await callback.message.answer_photo(FSInputFile(photo_path), caption="📸 Пример фото тарелки для дневника")
    except Exception as e:
        print(f"Error sending photo: {e}")
        
    # Send voice messages
    v1 = "assets/bot_media/Zachem_zapisyivat__edu.ogg"
    v2 = "assets/bot_media/dnevnik_pitaniya_na_GV.ogg"
    try:
        await callback.message.answer_voice(FSInputFile(v1), caption="🎙 Зачем записывать еду")
        await callback.message.answer_voice(FSInputFile(v2), caption="🎙 Дневник питания на ГВ")
    except Exception as e:
        print(f"Error sending voice: {e}")

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "new_diary_example")
async def show_new_diary_example(callback: types.CallbackQuery):
    text = (
        "📋 <b>Шаблон дневника питания</b>\n\n"
        "Просто скопируйте текст ниже себе в заметки на телефоне, вносите питание и отправляйте мне как удобно - ежедневно или все сразу.\n\n"
        "День N\n\n"
        "Завтрак\nВремя\nСимптомы сразу после еды:\nСимптомы через 2 часа после еды:\n\n"
        "Перекус\nВремя\nСимптомы сразу после еды:\nСимптомы через 2 часа после еды:\n\n"
        "Обед\nВремя\nСимптомы сразу после еды:\nСимптомы через 2 часа после еды:\n\n"
        "Полдник\nВремя\nСимптомы сразу после еды:\nСимптомы через 2 часа после еды:\n\n"
        "Ужин\nВремя\nСимптомы сразу после еды:\nСимптомы через 2 часа после еды:\n\n"
        "Количество воды за день:\n\n"
        "Во сколько проснулись утром:\n\n"
        "Во сколько уснули вечером:"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="new_diary"))
    
    # Send voice message about symptoms
    voice_path = "assets/bot_media/simptomyi__-_kakie__.ogg"
    try:
        await callback.message.answer_voice(FSInputFile(voice_path), caption="🎙 Про симптомы после еды")
    except Exception as e:
        print(f"Error sending voice: {e}")

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "new_forms")
async def show_new_forms(callback: types.CallbackQuery):
    text = "📋 <b>Анкеты</b>\n\nВыберите нужную анкету для заполнения:"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👶 Анкета ДЕТСКАЯ", url="https://forms.yandex.ru/cloud/6697836aeb6146284c8ac8af/"))
    builder.row(InlineKeyboardButton(text="👩 Анкета ВЗРОСЛЫЕ", url="https://forms.yandex.ru/cloud/669682d22530c212b560a8eb/"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="start"))
    builder.adjust(1)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "categories")
async def show_categories(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите категорию:", reply_markup=get_categories_main_keyboard())
    await callback.answer()

@router.callback_query(F.data == "all_recipes_cats")
async def show_all_recipes_categories(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите раздел из всех рецептов:", reply_markup=get_product_categories_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("cat_"))
async def process_category_selection(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.replace("cat_", "")
    
    # Save last list for "Back" button
    await state.update_data(last_list=callback.data)
    
    tag_cats = ["👶 Для детей", "👨‍👩‍👧 Для всей семьи", "🌿 Без глютена", "🥛 Без молока", "🥚 Без яиц", "⚡️ Быстрые рецепты", "💚 Лёгкие блюда"]
    
    if category in tag_cats:
        recipes = await db.get_recipes_by_tag(category)
        back_data = "categories"
    else:
        recipes = await db.get_recipes_by_category(category)
        back_data = "all_recipes_cats"
        
    if not recipes:
        await callback.answer(f"В разделе '{category}' пока нет рецептов.", show_alert=True)
        return
    
    # Дедупликация по названию для отображения в списке категорий
    recipes = _deduplicate_by_title(recipes)
    
    await callback.message.edit_text(f"Раздел: {category}", 
                                     reply_markup=get_recipe_list_keyboard(recipes, back_data))
    await callback.answer()

@router.callback_query(F.data.startswith("recipe_"))
async def show_recipe(callback: types.CallbackQuery, state: FSMContext):
    recipe_id = int(callback.data.replace("recipe_", ""))
    r = await db.get_recipe_by_id(recipe_id)
    if not r:
        await callback.answer("Рецепт не найден.")
        return

    related = await build_related_for_recipe(r)
    await _send_recipe(callback.message, r, callback.from_user.id, related=related)

    data = await state.get_data()
    back_data = data.get('last_list')
    
    # Определяем, какую кнопку "Показать еще" выводить
    show_more = "dont_know"
    if back_data == "plan_day" or data.get('plan_time'):
        show_more = "plan_day"

    protect = not is_admin(callback.from_user.id)
    if related:
        await callback.message.answer(
            "📎 Связанный рецепт:",
            reply_markup=get_related_recipes_keyboard(related),
            protect_content=protect,
        )
    
    await callback.message.answer(
        "Хотите еще варианты?",
        reply_markup=get_final_options(back_data, show_more, related=related),
        protect_content=protect,
    )
    await callback.answer()

# SEARCH
@router.callback_query(F.data == "search")
async def search_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_search)
    await callback.message.edit_text("Введите название блюда или ингредиент для поиска:", 
                                     reply_markup=get_back_button("start"))
    await callback.answer()

@router.message(UserStates.waiting_for_search)
async def process_search(message: types.Message, state: FSMContext):
    recipes = await db.search_recipes(message.text)
    protect = not is_admin(message.from_user.id)
    if not recipes:
        await message.answer("Ничего не нашлось. Попробуйте другой запрос или вернитесь в меню.", 
                             reply_markup=get_main_menu(), protect_content=protect)
    else:
        await message.answer(f"Найдено {len(recipes)} рецептов:", 
                             reply_markup=get_recipe_list_keyboard(recipes), protect_content=protect)
    await state.clear()

# SMART FLOW
@router.callback_query(F.data == "dont_know")
async def smart_flow_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_time)
    await callback.message.edit_text("Сколько у вас есть времени?", reply_markup=get_time_selection())
    await callback.answer()

@router.callback_query(F.data.startswith("time_"), UserStates.waiting_for_time)
async def process_time_sel(callback: types.CallbackQuery, state: FSMContext):
    time_cat = callback.data.replace("time_", "")
    await state.update_data(time_cat=time_cat)
    await state.set_state(UserStates.waiting_for_tag)
    await callback.message.edit_text("Что хочется сейчас?", reply_markup=get_tag_selection())
    await callback.answer()

@router.callback_query(F.data.startswith("tag_"), UserStates.waiting_for_tag)
async def process_tag_sel(callback: types.CallbackQuery, state: FSMContext):
    tag = callback.data.replace("tag_", "")
    data = await state.get_data()
    recipes = await db.filter_recipes(data['time_cat'], tag)
    
    if not recipes:
        await callback.message.edit_text("К сожалению, по вашему запросу ничего не нашлось 😔\nПопробуйте изменить параметры поиска.", 
                                         reply_markup=get_final_options())
    else:
        await callback.message.edit_text(f"Вот несколько вариантов под ваш запрос ({len(recipes)}):", 
                                         reply_markup=get_recipe_list_keyboard(recipes[:5], "dont_know"))
    await state.clear()
    await callback.answer()

# PLAN DAY
@router.callback_query(F.data == "plan_day")
async def plan_day_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_plan_time)
    await callback.message.edit_text("Сколько у вас есть времени на готовку сегодня?", reply_markup=get_time_selection())
    await callback.answer()

@router.callback_query(F.data.startswith("time_"), UserStates.waiting_for_plan_time)
async def process_plan_time(callback: types.CallbackQuery, state: FSMContext):
    time_cat = callback.data.replace("time_", "")
    await state.update_data(plan_time=time_cat)
    await state.set_state(UserStates.waiting_for_plan_tag)
    await callback.message.edit_text("Какие предпочтения по меню?", reply_markup=get_tag_selection())
    await callback.answer()

@router.callback_query(F.data.startswith("tag_"), UserStates.waiting_for_plan_tag)
async def process_plan_tag(callback: types.CallbackQuery, state: FSMContext):
    tag = callback.data.replace("tag_", "")
    data = await state.get_data()
    time_cat = data['plan_time']
    
    # Save for "Back" button and "Show more"
    await state.update_data(last_list="plan_day", plan_tag=tag)
    
    # Get one recipe for each meal type
    breakfast = await db.get_random_recipe_by_filters("Завтрак", time_cat, tag)
    lunch = await db.get_random_recipe_by_filters("Обед", time_cat, tag)
    dinner = await db.get_random_recipe_by_filters("Ужин", time_cat, tag)
    
    if not any([breakfast, lunch, dinner]):
        await callback.message.edit_text("К сожалению, не удалось подобрать меню. Попробуйте другие параметры.", 
                                         reply_markup=get_final_options())
        await state.clear()
    else:
        text = "📅 <b>Ваше меню на день:</b>\n\n"
        recipes = []
        if breakfast:
            text += f"🌅 <b>Завтрак:</b> {breakfast['title']}\n"
            recipes.append(breakfast)
        if lunch:
            text += f"🍲 <b>Обед:</b> {lunch['title']}\n"
            recipes.append(lunch)
        if dinner:
            text += f"🌙 <b>Ужин:</b> {dinner['title']}\n"
            recipes.append(dinner)
            
        await callback.message.edit_text(text, parse_mode="HTML", 
                                         reply_markup=get_recipe_list_keyboard(recipes, "plan_day"))
        # We DON'T clear state here to keep plan_time and plan_tag for "Show more"
    
    await callback.answer()

# TIPS
@router.callback_query(F.data == "tips")
async def show_tips(callback: types.CallbackQuery):
    hacks, _ = await db.get_all_tips_and_hacks()
    
    has_hacks = len(hacks) > 0
        
    await callback.message.edit_text("💡 Полезные советы и лайфхаки:", 
                                     reply_markup=get_tips_keyboard(has_hacks))
    await callback.answer()

@router.callback_query(F.data == "cooking_tips")
async def show_cooking_tips(callback: types.CallbackQuery):
    hacks, _ = await db.get_all_tips_and_hacks()
    await callback.message.edit_text("✨ Советы по приготовлению:", 
                                     reply_markup=get_cooking_tips_keyboard(hacks))
    await callback.answer()

@router.callback_query(F.data.startswith("dtip_"))
async def show_dynamic_tip(callback: types.CallbackQuery):
    data = callback.data.replace("dtip_", "")
    hacks, recipe_tips = await db.get_all_tips_and_hacks()
    
    content = "Совет скоро появится!"
    back_target = "tips"
    
    if data.startswith("h_"):
        h_id = int(data.split("_")[1])
        back_target = "cooking_tips"
        for h in hacks:
            if h['id'] == h_id:
                title = h['title'].strip()
                content_text = h['lifehacks'].strip()
                
                # Simplified display: title as header + content as is
                # No more extra prefixes or redundant headers
                content = f"✨ <b>Лайфхаки: {title}</b>\n\n{content_text}"
                break
    elif data.startswith("c_"):
        cat = data.split("_")[1]
        tips_list = []
        for r in recipe_tips:
            if r['category'] == cat:
                tips_list.append(f"• <b>{r['title']}</b>: {r['tips']}")
        
        if tips_list:
            content = f"👨‍🍳 <b>Советы по разделу {cat}:</b>\n\n" + "\n\n".join(tips_list)

    await callback.message.answer(content, parse_mode="HTML", reply_markup=get_back_button(back_target), protect_content=not is_admin(callback.from_user.id))
    await callback.answer()

@router.callback_query(F.data.startswith("tip_"))
async def show_tip_content(callback: types.CallbackQuery):
    tips = {
        "tip_plate": "🍽 <b>Как собрать тарелку</b>\n\n1/2 тарелки — овощи и зелень\n1/4 — белок (мясо, рыба, бобовые)\n1/4 — сложные углеводы (крупы, цельнозерновой хлеб)",
        "tip_kids": "👶 <b>Питание для детей</b>\n\nГлавное — разнообразие и отсутствие давления. Предлагайте новый продукт до 10-15 раз в разных видах.",
        "tip_10percent": "📈 <b>Правило 10%</b>\n\nПри введении новых продуктов добавляйте их постепенно — около 10% от общего объема знакомой пищи.",
        "tip_errors": "❌ <b>Частые ошибки</b>\n\n⁃ избыток сахара и ненужных добавок в продуктах - читайте состав внимательнее 🙏",
        "tip_greens": (
            "🌿 <b>Как добавить зелень в рацион для снижения веса</b> (даже если вы её не любите)\n\n"
            "✅ Решение для тех, кто не ест салаты, но хочет получить пользу зелени!\n\n"
            "🍏 <b>Почему зелень важна для похудения?</b>\n"
            "Зелень – это низкокалорийный источник клетчатки, витаминов и минералов, которые:\n"
            "• Снижают инсулинорезистентность (шпинат, руккола).\n"
            "• Улучшают детокс (петрушка, кинза).\n"
            "• Подавляют тягу к сладкому (листовая капуста).\n"
            "• Ускоряют метаболизм (сельдерей, укроп).\n\n"
            "Но если вы не любите салаты, вот незаметные способы добавить зелень в меню.\n\n"
            "🥤 <b>7 способов «спрятать» зелень в еде</b>\n\n"
            "<b>1. Смузи (базовый рецепт + вариации)</b>\n"
            "Базовый состав:\n"
            "- 1 горсть шпината/кале (не чувствуется на вкус!).\n"
            "- 1 банан/груша (для сладости).\n"
            "- 1 ч.л. льняного семени (омега-3 для сытости).\n"
            "- 200 мл воды/миндального молока.\n\n"
            "Варианты:\n"
            "• Зелёный ананас: шпинат + ананас + мята.\n"
            "• Шоколадный: кале + какао + банан + арахисовая паста.\n"
            "• Огуречный: петрушка + огурец + яблоко + лимон.\n\n"
            "<i>Почему работает: Клетчатка зелени снижает аппетит и замедляет усвоение углеводов</i>\n\n"
            "<b>2. Зелёные соусы и песто</b>\n"
            "• Песто из рукколы: руккола + кедровые орехи + оливковое масло + чеснок (подавать к пасте или курице).\n"
            "• Соус «глуакамоле»: авокадо + кинза + лимонный сок (мазать на тосты).\n"
            "• Йогуртовый соус: греческий йогурт + укроп + чеснок (к мясу или овощам).\n\n"
            "<i>Польза: Жиры из орехов/авокадо усиливают усвоение витаминов зелени.</i>\n\n"
            "<b>3. Омлеты и котлеты с зеленью</b>\n"
            "• Омлет «Невидимка»: взбить яйца с мелко нарезанным шпинатом (после готовности зелень не чувствуется).\n"
            "• Куриные котлеты: фарш + тушёная капуста + петрушка.\n\n"
            "💡 <b>Лайфхак:</b> Замороженный шпинат легче добавить в любое блюдо (супы, рагу).\n\n"
            "<b>4. Зелёные супы-пюре</b>\n"
            "• Суп из брокколи: брокколи + картофель + сливки (вкус нейтральный, цвет незаметный).\n"
            "• Крем-суп с кабачком и шпинатом: варить, затем взбить блендером.\n\n"
            "<i>Почему: Термическая обработка смягчает вкус зелени.</i>\n\n"
            "<b>5. Зелёные чипсы (альтернатива снекам)</b>\n"
            "• Кале-чипсы: листья кале + оливковое масло + соль, запечь при 180°C до хруста.\n"
            "• Сельдерейные палочки с хумусом.\n\n"
            "✨ <b>Фишка:</b> Хрустящая текстура отвлекает от «травяного» вкуса.\n\n"
            "<b>6. Соки и смузи-боулы</b>\n"
            "• Сок «Детокс»: огурец + сельдерей + яблоко + петрушка (пропорция 3:1:1:0,5).\n"
            "• Смузи-боул: зелёный смузи + сверху семена чиа, ягоды, кокосовая стружка (визуально аппетитнее).\n\n"
            "<b>7. Добавки в готовые блюда</b>\n"
            "• В фарш: мелко нарезанная кинза/укроп (в котлеты, тефтели).\n"
            "• В творог: смешать с зелёным луком и огурцом.\n"
            "• В сэндвичи: листья салата между ингредиентами (не на виду).\n\n"
            "📌 <b>Пример дня с «невидимой» зеленью</b>\n"
            "Завтрак: Омлет со шпинатом + зелёный смузи.\n"
            "Обед: Суп-пюре из брокколи + куриные котлеты с петрушкой.\n"
            "Ужин: Лосось с соусом песто + стручковая фасоль.\n"
            "Перекус: Зелёные чипсы из кале.\n\n"
            "💡 <b>Важно!</b>\n"
            "1. Начинайте с малых количеств (1/4 пучка в смузи), постепенно увеличивая.\n"
            "2. Замороженная зелень удобна и сохраняет пользу.\n"
            "3. Если вкус всё равно мешает – добавляйте лимонный сок или имбирь (перебивают горечь).\n\n"
            "Через 2 недели таких экспериментов вы заметите:\n"
            "- Снижение тяги к сладкому.\n"
            "- Улучшение пищеварения.\n"
            "- Более стабильный энергетический уровень."
        )
    }
    content = tips.get(callback.data, "Совет скоро появится!")
    await callback.message.answer(content, parse_mode="HTML", reply_markup=get_back_button("tips"), protect_content=not is_admin(callback.from_user.id))
    await callback.answer()

# MEAL TYPE FLOW
@router.callback_query(F.data == "get_recipe")
async def meal_type_start(callback: types.CallbackQuery):
    await callback.message.edit_text("Какой прием пищи вы планируете?", 
                                     reply_markup=get_meal_type_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("meal_"))
async def process_meal_selection(callback: types.CallbackQuery, state: FSMContext):
    meal_type = callback.data.replace("meal_", "")
    
    # Skip subcategories for Desserts, Salads, and Casseroles
    if meal_type in ["Десерт", "Салаты", "Запеканки"]:
        category = meal_type if meal_type != "Десерт" else "Десерты"
        
        await state.update_data(last_list=f"mealcat_{meal_type}_{category}")
        
        if meal_type == "Десерт":
            recipes = await db.get_recipes_by_meal_and_cat(meal_type, category)
        else:
            # For Salads and Casseroles, we just get by category
            recipes = await db.get_recipes_by_category(category)
        
        if not recipes:
            await callback.answer(f"В разделе '{category}' пока нет рецептов.", show_alert=True)
            return
            
        # Дедупликация по названию
        recipes = _deduplicate_by_title(recipes)
            
        await callback.message.edit_text(f"Рецепты: {category}:", 
                                         reply_markup=get_recipe_list_keyboard(recipes, "get_recipe"))
        await callback.answer()
        return

    await callback.message.edit_text(f"Выберите категорию для {meal_type.lower()}:", 
                                     reply_markup=get_subcategories_keyboard(meal_type))
    await callback.answer()

@router.callback_query(F.data.startswith("mealcat_"))
async def process_meal_category_selection(callback: types.CallbackQuery, state: FSMContext):
    # Format: mealcat_{meal_type}_{category}
    parts = callback.data.split("_")
    meal_type = parts[1]
    category = "_".join(parts[2:])
    
    # Special case for Seasonal Smoothies
    if category == "Сезонные смузи":
        await callback.message.edit_text("Выберите подраздел сезонных смузи:", 
                                         reply_markup=get_seasonal_smoothies_keyboard())
        await callback.answer()
        return

    # Save last list for "Back" button
    await state.update_data(last_list=callback.data)
    
    recipes = await db.get_recipes_by_meal_and_cat(meal_type, category)
    
    if not recipes:
        await callback.answer(f"В категории '{category}' для {meal_type.lower()} пока нет рецептов.", show_alert=True)
        return
        
    # Дедупликация по названию
    recipes = _deduplicate_by_title(recipes)
        
    await callback.message.edit_text(f"Рецепты: {category} на {meal_type.lower()}:", 
                                     reply_markup=get_recipe_list_keyboard(recipes, f"meal_{meal_type}"))
    await callback.answer()

@router.callback_query(F.data.startswith("ss_"))
async def process_seasonal_smoothie_subcat(callback: types.CallbackQuery, state: FSMContext):
    subcat = callback.data.replace("ss_", "")
    
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
    if not search_tag:
        await callback.answer("Подкатегория не найдена.")
        return
        
    # Get recipes by tag AND category "Сезонные смузи"
    # We'll use get_recipes_by_tag and filter manually for simplicity or add a DB method
    all_tagged = await db.get_recipes_by_tag(search_tag)
    recipes = [r for r in all_tagged if r['category'] == "Сезонные смузи"]
    
    if not recipes:
        await callback.answer("В этом подразделе пока нет рецептов.", show_alert=True)
        return
        
    # Save state for back button
    await state.update_data(last_list=callback.data)
    
    title_map = {
        "spring_summer": "Весенне-летние смузи (май-сентябрь)",
        "autumn_winter": "Осенне-зимние смузи (октябрь-апрель)",
        "dessert": "Десертные (без чувства вины)",
        "hearty": "Сытные (замена перекуса)",
        "detox": "Смузи для детокса",
        "immunity": "Смузи для иммунитета",
        "exotic": "Экзотические смузи",
        "warm": "Тёплые смузи (зима)",
        "heart": "Смузи для здоровья сердца",
        "sport": "Для спортсменов – хорош активным деткам",
        "sweet": "Смузи для сладкоежек"
    }
    
    await callback.message.edit_text(f"Подраздел: {title_map.get(subcat)}", 
                                     reply_markup=get_recipe_list_keyboard(recipes, "mealcat_Напиток_Сезонные смузи"))
    await callback.answer()

# ABOUT
@router.callback_query(F.data == "about")
async def show_about(callback: types.CallbackQuery):
    about_text = await db.get_setting("about_text")
    protect = not is_admin(callback.from_user.id)
    await callback.message.answer(about_text, parse_mode="HTML", reply_markup=get_back_button("start"), protect_content=protect)
    try:
        await callback.message.delete()
    except:
        pass
    await callback.answer()

# CONSTRUCTOR
@router.callback_query(F.data == "constructor")
async def constructor_list(callback: types.CallbackQuery):
    constructors = await db.get_constructors()
    if not constructors:
        await callback.answer("Конструкторы пока не добавлены.", show_alert=True)
        return
    
    text = "Выберите конструктор:"
    reply_markup = get_constructor_list_keyboard(constructors)
    
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        # If we can't edit (e.g. it's a photo message), delete old and send new
        try:
            await callback.message.delete()
        except:
            pass
        await callback.message.answer(text, reply_markup=reply_markup, protect_content=not is_admin(callback.from_user.id))
    
    await callback.answer()

@router.callback_query(F.data.startswith("const_"))
async def show_constructor(callback: types.CallbackQuery):
    const_id = int(callback.data.replace("const_", ""))
    c = await db.get_constructor_by_id(const_id)
    if not c:
        await callback.answer("Конструктор не найден.")
        return
    
    text = format_constructor(c)
    reply_markup = get_back_button("constructor")
    
    # Telegram caption limit is 1024 characters
    protect = not is_admin(callback.from_user.id)
    if c.get('photo_id'):
        if len(text) <= 1024:
            await callback.message.answer_photo(
                c['photo_id'], 
                caption=text, 
                parse_mode="HTML", 
                reply_markup=reply_markup, 
                protect_content=protect
            )
            try:
                await callback.message.delete()
            except:
                pass
        else:
            # If text is too long for caption, send photo then text
            await callback.message.answer_photo(c['photo_id'], protect_content=protect)
            await callback.message.answer(text, parse_mode="HTML", reply_markup=reply_markup, protect_content=protect)
            try:
                await callback.message.delete()
            except:
                pass
    else:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=reply_markup, protect_content=protect)
        try:
            await callback.message.delete()
        except:
            pass
        
    await callback.answer()

# PDF
@router.callback_query(F.data == "get_pdf")
async def show_pdf(callback: types.CallbackQuery):
    pdf_text = await db.get_setting("pdf_text")
    protect = not is_admin(callback.from_user.id)
    await callback.message.answer(pdf_text, parse_mode="HTML", reply_markup=get_back_button("start"), protect_content=protect)
    try:
        await callback.message.delete()
    except:
        pass
    await callback.answer()

# ASK QUESTION
@router.callback_query(F.data == "ask_question")
async def ask_question(callback: types.CallbackQuery):
    text = (
        "💛 Если у вас есть вопросы по рецептам, питанию или сочетанию продуктов — вы можете написать лично.\n\n"
        "Иногда поддержка и возможность задать вопрос помогают не бросать заботу о себе ❤️"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Написать в Telegram", url="https://t.me/diaChe"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="start"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
