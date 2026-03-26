import json

def find_famous_people_roads(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    keywords = ["인물", "기념", "성명", "생가", "존칭", "활동지", "유적", "유허", "역사적"]
    famous_names = ["세종", "이순신", "김유신", "강감찬", "정약용", "이황", "이이", "신사임당", "백범", "안중근", "안창호", "유관순", "박경리", "소나기"]
    
    found = []
    for row in data:
        reason = row.get('부여사유', '')
        road_name = row.get('도로명', '')
        city = row.get('시군구', '')
        
        # Check for keywords or names
        is_famous = any(kw in reason for kw in keywords) or any(name in road_name for name in famous_names)
        
        if is_famous and len(reason) > 5:
            found.append({
                "도로명": road_name,
                "시군구": city,
                "부여사유": reason
            })
            
    # Sort and return top examples
    return found[:20]

if __name__ == "__main__":
    results = find_famous_people_roads('d:/AI_Class/주소AI도슨트/road_names.json')
    for res in results:
        print(f"[{res['시군구']} {res['도로명']}] {res['부여사유']}")
