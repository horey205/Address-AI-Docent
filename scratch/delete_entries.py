import sqlite3

db_path = 'docent_cache.db'

def query_and_delete():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Delete targets
    cursor.execute("DELETE FROM story_cache WHERE (city LIKE '%노원구%' AND (road LIKE '%동일로%' OR road LIKE '%통이로%')) AND lang = '한국어'")
    nowon_deleted = cursor.rowcount
    
    cursor.execute("DELETE FROM story_cache WHERE city LIKE '%성남시 중원구%' AND road LIKE '%광명로%'")
    seongnam_deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    print(f"Nowon-gu entries deleted: {nowon_deleted}")
    print(f"Seongnam-si entries deleted: {seongnam_deleted}")
    print("Operation completed.")

if __name__ == "__main__":
    query_and_delete()
