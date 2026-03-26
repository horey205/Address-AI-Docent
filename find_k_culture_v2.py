import json

def find_k_culture_roads(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Specific Hallyu or Cultural terms
    terms = ["한류", "케이팝", "K-POP", "드라마", "영화", "예능", "사극", "촬영", "연예", "스타", "갤러리", "전통음식", "비빔밥", "김치", "아리랑", "풍류", "태권도", "도예", "국악", "전통무용", "궁궐", "서원", "낙안읍성", "경리단", "망리단", "송리단", "해리단"]
    
    found = []
    seen = set()
    
    for row in data:
        road = row.get('도로명', '')
        reason = row.get('부여사유', '')
        city = row.get('시군구', '')
        
        if any(term in road or term in reason for term in terms):
            if road not in seen and len(reason) > 5:
                found.append({"name": road, "city": city, "reason": reason})
                seen.add(road)
                
    return found[:20]

if __name__ == "__main__":
    results = find_k_culture_roads('d:/AI_Class/주소AI도슨트/road_names.json')
    for res in results:
        print(f"[{res['city']} {res['name']}] {res['reason']}")
