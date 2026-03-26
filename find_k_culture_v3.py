import json

def find_k_culture_roads(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Specific Hallyu or Cultural terms
    terms = ["한류", "케이팝", "K-POP", "드라마", "영화", "영상", "콘텐츠", "스타", "갤러리", "예술", "풍류", "도예", "국악", "전통", "미디", "월드컵", "명소"]
    
    found = []
    seen = set()
    
    for row in data:
        road = row.get('도로명', '')
        reason = row.get('부여사유', '')
        city = row.get('시군구', '')
        
        if any(term in road or term in reason for term in terms):
            if road not in seen and len(reason) > 5:
                # Exclude simple number roads like "영화사로10길"
                if any(road.endswith(sub) for sub in ["길", "안길", "번길"]):
                    continue
                found.append({"name": road, "city": city, "reason": reason})
                seen.add(road)
                
    return found[:20]

if __name__ == "__main__":
    results = find_k_culture_roads('d:/AI_Class/주소AI도슨트/road_names.json')
    for res in results:
        print(f"[{res['city']} {res['name']}] {res['reason']}")
