import json
from collections import Counter

with open('d:/AI_Class/주소AI도슨트/road_names.json', encoding='utf-8') as f:
    data = json.load(f)

# 도로명 빈도 계산
road_counts = Counter(row.get('도로명', '') for row in data if row.get('도로명'))

top_10 = []
# 숫자가 들어간 길(1길, 2길 등)은 제외하고 고유 명칭 위주로 찾기
for road, count in road_counts.most_common():
    if any(char.isdigit() for char in road): continue 
    if len(road) < 2: continue
    
    representative = next(row for row in data if row.get('도로명') == road)
    top_10.append({'name': road, 'city': representative['시군구'], 'count': count})
    if len(top_10) >= 10:
        break

for i, item in enumerate(top_10, 1):
    print(f"{i}. {item['name']} ({item['count']}회 중복): {item['city']}")
