import json

def find_primary_famous_roads(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Famous names to search for in road names or reasons
    names = ["세종", "이순신", "강감찬", "유관순", "신사임당", "백범", "한용운", "윤동주", "정약용", "단종", "이황", "이이", "장영실", "서희", "광개토", "성삼문", "토정", "허준", "사임당", "충무", "퇴계", "율곡", "하정", "다산", "추사", "해공", "송강", "만해"]
    
    found = []
    seen_names = set()
    
    for row in data:
        road_name = row.get('도로명', '')
        reason = row.get('부여사유', '')
        city = row.get('시군구', '')
        
        # Skip sub-roads like "백범로10길"
        if any(road_name.endswith(sub) for sub in ["길", "안길", "번길"]):
            continue
            
        is_famous = any(name in road_name for name in names) or any(name in reason for name in names)
        
        if is_famous and road_name not in seen_names and len(reason) > 5:
            # Check for "historical figure" keywords to weed out coincident names
            if any(kw in reason for kw in ["인물", "성명", "호 ", "호인용", "기념", "활동", "유적", "유허"]):
                found.append({
                    "도로명": road_name,
                    "시군구": city,
                    "부여사유": reason
                })
                seen_names.add(road_name)
                
    return found[:20]

if __name__ == "__main__":
    results = find_primary_famous_roads('d:/AI_Class/주소AI도슨트/road_names.json')
    for res in results:
        print(f"[{res['시군구']} {res['도로명']}] {res['부여사유']}")
