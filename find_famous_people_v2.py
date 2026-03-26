import json

def find_famous_people_roads(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Famous names and keywords
    names = ["세종", "이순신", "강감찬", "유관순", "신사임당", "백범", "박경리", "한용운", "윤동주", "정약용", "단종", "이황", "이이", "장영실", "서희", "광개토", "성삼문", "토정", "허준"]
    keywords = ["호 인용", "호 활용", "인물의 성명", "인물명", "성명 인용", "기념하여", "탄생지", "생가", "존칭", "활동지"]
    
    found = []
    seen_names = set()
    
    for row in data:
        reason = row.get('부여사유', '')
        road_name = row.get('도로명', '')
        city = row.get('시군구', '')
        
        is_famous_content = any(name in reason for name in names) or any(name in road_name for name in names)
        is_keyword_match = any(kw in reason for kw in keywords)
        
        if (is_famous_content or is_keyword_match) and len(reason) > 5:
            # Avoid showing the same road from multiple sub-districts if possible
            key = f"{road_name}_{city}"
            if road_name not in seen_names:
                found.append({
                    "도로명": road_name,
                    "시군구": city,
                    "부여사유": reason
                })
                seen_names.add(road_name)
                
    return found[:20]

if __name__ == "__main__":
    results = find_famous_people_roads('d:/AI_Class/주소AI도슨트/road_names.json')
    for res in results:
        print(f"[{res['시군구']} {res['도로명']}] {res['부여사유']}")
