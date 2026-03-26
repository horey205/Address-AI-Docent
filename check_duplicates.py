import json
with open(r'd:\AI_Class\주소AI도슨트\road_names.json', encoding='utf-8') as f:
    data = json.load(f)
results = [row for row in data if row.get('도로명') == '벚꽃로']
print(f'Total matches: {len(results)}')
print([f"{row['시군구']}" for row in results])
