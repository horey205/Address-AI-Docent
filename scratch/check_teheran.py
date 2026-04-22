import sqlite3

db_path = 'docent_cache.db'

def check_teheran():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT rowid, city, road, lang FROM story_cache WHERE road LIKE '%테헤란로%'")
    rows = cursor.fetchall()
    for row in rows:
        print(repr(row))
    conn.close()

if __name__ == "__main__":
    check_teheran()
