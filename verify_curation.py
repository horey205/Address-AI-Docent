import json

def verify_curation_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Target roads to verify
    targets = [
        {"name": "백범로", "city": "마포구"},
        {"name": "다산로", "city": "중구"},
        {"name": "퇴계로", "city": "중구"},
        {"name": "율곡로", "city": "종로구"},
        {"name": "도산대로", "city": "강남구"},
        {"name": "동의보감로", "city": "산청군"},
        {"name": "세종로", "city": "종로구"},
        {"name": "충무로", "city": "중구"},
        {"name": "사임당로", "city": "서초구"},
        {"name": "하정로", "city": "동대문구"}
    ]
    
    results = []
    for t in targets:
        match = next((row for row in data if row['도로명'] == t['name'] and t['city'] in row['시군구']), None)
        if match:
            results.append({"name": t['name'], "city": match['시군구'], "desc": ""})
        else:
            # Try to find any occurrence if exact match fails
            match = next((row for row in data if row['도로명'] == t['name']), None)
            if match:
                results.append({"name": t['name'], "city": match['시군구'], "desc": ""})
                
    return results

if __name__ == "__main__":
    print(verify_curation_data('d:/AI_Class/주소AI도슨트/road_names.json'))
