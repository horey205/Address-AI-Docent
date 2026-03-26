import os
import sqlite3
import shutil

base = r'd:\AI_Class\주소AI도슨트'
db_path = os.path.join(base, 'docent_cache.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT id, city, road, lang, audio_path FROM story_cache")
rows = c.fetchall()

lang_map = {
    "한국어": "Korean",
    "English": "English",
    "中文": "Chinese",
    "日本語": "Japanese"
}

for row in rows:
    id_, city, road, lang, audio_path = row
    safe_city = city.replace(" ", "")
    safe_road = road.replace(" ", "")
    lang_name = lang_map.get(lang, "Korean")
    
    new_name = f"{safe_city}_{safe_road}_{lang_name}.mp3"
    new_path = os.path.join(base, "mp3", new_name)
    
    if os.path.exists(audio_path) and audio_path != new_path:
        shutil.move(audio_path, new_path)
        c.execute("UPDATE story_cache SET audio_path = ? WHERE id = ?", (new_path, id_))
        print(f"Renamed {os.path.basename(audio_path)} -> {new_name}")

conn.commit()
conn.close()
