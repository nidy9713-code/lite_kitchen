import sqlite3
import json
import sys

def collect_all_tips():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect('recipes.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    all_tips = {}
    
    # 1. From Constructors
    cursor.execute("SELECT title, lifehacks FROM constructors WHERE lifehacks IS NOT NULL AND lifehacks != ''")
    for row in cursor.fetchall():
        title = row['title'].replace(":", "")
        hacks = row['lifehacks'].strip().split("\n")
        all_tips[f"const_{row['title']}"] = {
            "title": f"💡 Лайфхаки: {title}",
            "content": f"<b>Лайфхаки для {title.lower()}:</b>\n\n" + "\n".join([f"— {h.strip()}" if not h.strip().startswith("—") else h.strip() for h in hacks])
        }
        
    # 2. From Recipes (filtering for actual tips, not just serving suggestions)
    cursor.execute("SELECT title, tips, category FROM recipes WHERE tips IS NOT NULL AND tips != ''")
    for row in cursor.fetchall():
        tip = row['tips'].strip()
        if len(tip) < 10: continue
        
        cat = row['category'] if row['category'] else "Другое"
        if cat not in all_tips:
            all_tips[cat] = {"title": f"👨‍🍳 Советы: {cat}", "tips": []}
        
        if tip not in all_tips[cat]["tips"]:
            all_tips[cat]["tips"].append(f"• <b>{row['title']}</b>: {tip}")
            
    # Format recipe tips
    for cat, data in list(all_tips.items()):
        if "tips" in data:
            all_tips[cat] = {
                "title": data["title"],
                "content": f"<b>Полезные советы по разделу {cat}:</b>\n\n" + "\n\n".join(data["tips"])
            }
            
    conn.close()
    return all_tips

if __name__ == "__main__":
    tips = collect_all_tips()
    # Let's see some
    for k, v in list(tips.items())[:5]:
        print(f"KEY: {k}")
        print(f"TITLE: {v['title']}")
        # print(f"CONTENT: {v['content'][:100]}...")
        print("-" * 20)
