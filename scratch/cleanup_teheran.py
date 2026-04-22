import sqlite3
import os

db_path = 'docent_cache.db'
mp3_dir = 'mp3'

def cleanup_teheran():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. DB 삭제 (중국어 제외 모든 언어)
    cursor.execute("DELETE FROM story_cache WHERE road LIKE '%테헤란로%' AND lang != '중국어'")
    deleted_rows = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"DB entries deleted for Teheran-ro: {deleted_rows}")
    
    # 2. MP3 파일 삭제
    files_to_delete = [
        '강남구_테헤란로_Korean.mp3',
        '강남구_테헤란로_English.mp3',
        '강남구_테헤란로_Japanese.mp3'
    ]
    
    for filename in files_to_delete:
        file_path = os.path.join(mp3_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted MP3: {filename}")
        else:
            print(f"MP3 not found: {filename}")

if __name__ == "__main__":
    cleanup_teheran()
