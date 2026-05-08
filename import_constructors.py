import docx
import sqlite3
import json

def import_constructors():
    src = "constructors_local.docx"
    doc = docx.Document(src)
    
    # Simple state machine to parse
    constructors = []
    current = None
    
    full_text = []
    for p in doc.paragraphs:
        if p.text.strip():
            full_text.append(p.text.strip())
            
    # Define sections
    sections = []
    current_section = []
    for line in full_text:
        if line.lower().startswith("конструктор"):
            if current_section:
                sections.append(current_section)
            current_section = [line]
        else:
            current_section.append(line)
    if current_section:
        sections.append(current_section)
        
    for sec in sections:
        title = sec[0]
        # Clean title: remove "Конструктор", strip whitespace and emojis, add colon
        clean_title = title.replace("Конструктор", "").strip()
        # Remove common emojis and trailing symbols
        import re
        clean_title = re.sub(r'[^\w\sа-яА-ЯёЁ]', '', clean_title).strip()
        clean_title = clean_title.capitalize() + ":"
        
        data = {
            'title': clean_title,
            'suitable_for': 'завтрак / обед / ужин / перекус', # Default
            'principle': '',
            'basis': '',
            'protein': '',
            'fats': '',
            'fiber': '',
            'how_to_assemble': '',
            'flexibility': '',
            'lifehacks': '',
            'kids_recommendation': ''
        }
        
        # Heuristics for each type
        if "каш" in title.lower():
            data['suitable_for'] = "завтрак"
            data['basis'] = "Любая крупа"
            data['principle'] = "По этому принципу вы соберете любую кашу и она будет максимально полноценным блюдом для завтрака всей семьи."
            lifehacks = []
            for line in sec:
                if "📌Крупа" in line: data['basis'] = line.split("–")[1].strip()
                if "📌Белок" in line: data['protein'] = line.split("–")[1].strip()
                if "📌Жиры" in line: data['fats'] = line.split("–")[1].strip()
                if "📌Клетчатка" in line: data['fiber'] = line.split("–")[1].strip()
                if "Лайфхаки" in line: continue
                if line.startswith("📌") and "Крупа" not in line and "Белок" not in line and "Жиры" not in line and "Клетчатка" not in line:
                    lifehacks.append(line.replace("📌", "").strip())
                if "Растительное молоко можно заменять" in line:
                    data['flexibility'] = line
                if "если ребенок не любит яйца" in line:
                    data['kids_recommendation'] = line
            data['lifehacks'] = "\n".join(lifehacks)
            
        elif "омлет" in title.lower():
            data['suitable_for'] = "завтрак / ужин"
            data['basis'] = "Яйца"
            data['principle'] = "Яйца – сами по себе прекрасный источник белка, жиров и лецитина."
            lifehacks = []
            for line in sec:
                if "📌Яйца" in line: data['protein'] = line.split("–")[1].strip()
                if "📌Клетчатка" in line: data['fiber'] = line.split(":")[1].strip()
                if "📌Углеводы" in line: data['basis'] = line.split(" ")[0].replace("📌", "").strip() + " + " + line.split(" ")[-1].strip()
                if line.startswith("📌") and "Яйца" not in line and "Клетчатка" not in line and "Углеводы" not in line:
                    lifehacks.append(line.replace("📌", "").strip())
            data['lifehacks'] = "\n".join(lifehacks)

        elif "оладьев" in title.lower():
            data['suitable_for'] = "перекус / завтрак"
            data['principle'] = "Такие блюда всегда хороши на перекус, так как готовятся быстро и просто."
            lifehacks = []
            for line in sec:
                if "📌Основа" in line: data['basis'] = line.split(":")[1].strip()
                if "📌Связующий элемент" in line: data['protein'] = line.split(":")[1].strip()
                if "📌Часть основы – мука" in line: data['flexibility'] = line.split(".")[1].strip()
                if "📌Суперфуды" in line: data['fiber'] = line.split(":")[1].strip()
                if "Чтобы не пригорали" in line or "Муку за основу берите" in line:
                    lifehacks.append(line)
            data['lifehacks'] = "\n".join(lifehacks)

        elif "сырников" in title.lower():
            data['suitable_for'] = "завтрак / перекус"
            data['principle'] = "Идеальный способ сделать творог вкусным и сытным."
            lifehacks = []
            for line in sec:
                if "📌Основа" in line: data['basis'] = line.split(":")[1].strip()
                if "📌Дополнительно" in line: data['fiber'] = line.split(":")[1].strip()
                if "📌Мука" in line: data['flexibility'] = line.split(":")[1].strip()
                if "📌обогащение" in line: data['protein'] = line.split(":")[1].strip()
                if line.startswith("- "):
                    lifehacks.append(line[2:])
            data['lifehacks'] = "\n".join(lifehacks)

        elif "котлет" in title.lower():
            data['suitable_for'] = "обед / ужин"
            data['principle'] = "Вариантов приготовления котлет — не пересчитать! Это отличный способ накормить семью."
            lifehacks = []
            for line in sec:
                if "📌читайте состав" in line: lifehacks.append(line.replace("📌", ""))
                if "📌готовый покупной фарш" in line: lifehacks.append(line.replace("📌", ""))
                if "📌чем дольше мясо лежит" in line: lifehacks.append(line.replace("📌", ""))
                if "❣️" in line:
                    if "если ребенок не ест субпродукты" in line:
                        data['kids_recommendation'] = line.replace("❣️", "").strip()
                    else:
                        lifehacks.append(line.replace("❣️", "").strip())
            data['basis'] = "Фарш (любое мясо или рыба)"
            data['protein'] = "Мясо / Рыба / Яйцо (опционально)"
            data['fiber'] = "Овощи (картофель, кабачок и др.)"
            data['lifehacks'] = "\n".join(lifehacks)

        elif "смузи" in title.lower():
            data['suitable_for'] = "завтрак / перекус"
            data['principle'] = "Быстрый и удобный способ получить максимум пользы в одном стакане."
            lifehacks = ["Использовать различные ингредиенты, добавлять семена в каждое и экспериментировать"]
            for line in sec:
                if "1. Основа:" in line: continue
                if "Фрукты:" in line or "Овощи:" in line or "Жидкость:" in line:
                    data['basis'] += line + " "
                if "2. Белки:" in line: continue
                if "Орехи:" in line or "Семена:" in line or "Протеиновый порошок:" in line:
                    data['protein'] += line + " "
                if "3. Жиры:" in line: continue
                if "Авокадо" in line or "Омега-3" in line:
                    data['fats'] += line + " "
                if "4. Приправы" in line: continue
                if "Корица" in line or "Мед" in line:
                    data['fiber'] += line + " "
            data['lifehacks'] = "\n".join(lifehacks)

        constructors.append(data)

    # Insert into DB
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    
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
            kids_recommendation TEXT
        )
    """)
    
    # Clear old constructors if any
    cursor.execute("DELETE FROM constructors")
    
    for c in constructors:
        cursor.execute("""
            INSERT INTO constructors (
                title, suitable_for, principle, basis, protein, fats, fiber, 
                how_to_assemble, flexibility, lifehacks, kids_recommendation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c['title'], c['suitable_for'], c['principle'], c['basis'],
            c['protein'], c['fats'], c['fiber'], c['how_to_assemble'],
            c['flexibility'], c['lifehacks'], c['kids_recommendation']
        ))
    
    conn.commit()
    conn.close()
    print(f"Imported {len(constructors)} constructors.")

if __name__ == "__main__":
    import_constructors()
