import json

def get_k_culture_list(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Representative K-Culture roads
    k_targets = {
        "한류": "한류월드",
        "미디어": "미래를 상징하는 미디어",
        "월드컵": "2002 월드컵",
        "예술": "예술인들이 모이는",
        "드라마": "드라마 촬영지",
        "시네마": "시네마 거리",
        "K-": "K-",
        "문화": "전통문화"
    }
    
    found = []
    seen = set()
    
    for row in data:
        road = row.get('도로명', '')
        reason = row.get('부여사유', '')
        city = row.get('시군구', '')
        
        # Skip sub-roads
        if any(road.endswith(sub) for sub in ["길", "안길", "번길"]): continue
        
        for k, v in k_targets.items():
            if k in road or v in reason:
                if road not in seen and len(reason) > 5:
                    found.append({"name": road, "city": city, "desc": reason[:30] + "..."})
                    seen.add(road)
                    break
    return found[:20]

if __name__ == "__main__":
    results = get_k_culture_list('d:/AI_Class/주소AI도슨트/road_names.json')
    for r in results:
        print(r)
