import json

def find_k_culture_roads(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Keywords for K-Culture
    keywords = ["한류", "촬영지", "드라마", "영화", "K-POP", "문화", "예술", "축제", "먹거리", "맛집", "비빔밥", "김치", "태권도", "전통", "명소"]
    
    found = []
    seen_names = set()
    
    for row in data:
        road_name = row.get('도로명', '')
        reason = row.get('부여사유', '')
        city = row.get('시군구', '')
        
        if any(road_name.endswith(sub) for sub in ["길", "안길", "번길"]):
            # Continue if it's a sub-road but check its parent?
            # Actually for K-Culture, specific 'Gil' names are often famous (e.g., Gyeongnidan-gil)
            pass
            
        contains_keyword = any(kw in reason for kw in keywords) or any(kw in road_name for kw in keywords)
        
        if contains_keyword and road_name not in seen_names and len(reason) > 5:
            # Look for specific K-Culture mentions
            # e.g., "겨울연가", "기생충", "월드컵", "아이돌"
            found.append({
                "도로명": road_name,
                "시군구": city,
                "부여사유": reason
            })
            seen_names.add(road_name)
                
    return found[:30]

if __name__ == "__main__":
    results = find_k_culture_roads('d:/AI_Class/주소AI도슨트/road_names.json')
    for res in results:
        print(f"[{res['시군구']} {res['도로명']}] {res['부여사유']}")
