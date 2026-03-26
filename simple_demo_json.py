import json
import edge_tts
import asyncio
import os

# JSON 파일 경로
JSON_FILE = r'D:\AI_Class\주소AI도슨트\road_names.json'

async def text_to_speech(text, output_file):
    voice = "ko-KR-SunHiNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    print(f"\n🔊 음성 파일 생성 완료: {output_file}")

def json_docent():
    print("=== 주소 AI 도슨트 (JSON DB Demo) ===")
    
    # 1. JSON 데이터 로드 (매우 빠름!)
    try:
        if not os.path.exists(JSON_FILE):
            print("데이터 파일(JSON)이 없습니다. 변환 스크립트를 먼저 실행해주세요.")
            return
            
        print("데이터를 최적화하여 불러오는 중...")
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"오류: JSON 파일을 읽을 수 없습니다. ({e})")
        return

    # 2. 도로명 입력
    search_name = input("\n🔍 유래가 궁금한 도로명을 입력하세요: ").strip()
    if not search_name: return

    # 3. 데이터 검색 (Python 리스트 컴프리헨션으로 탐색)
    results = [row for row in data if row['도로명'] == search_name]

    if not results:
        print(f"'{search_name}' 정보를 찾을 수 없습니다.")
        return

    # 4. 결과 출력 및 선택
    selected_reason = ""
    if len(results) > 1:
        print(f"\n📍 검색 결과 {len(results)}건:")
        for i, row in enumerate(results):
            print(f"[{i+1}] {row['시군구']}")
        
        choice = int(input("\n번호 선택: ")) - 1
        selected_reason = results[choice]['부여사유']
        selected_city = results[choice]['시군구']
    else:
        selected_reason = results[0]['부여사유']
        selected_city = results[0]['시군구']

    print(f"\n📖 [{selected_city}] 유래: {selected_reason}")

    # 5. TTS 실행
    script = f"{selected_city}의 {search_name} 유래입니다. {selected_reason}"
    asyncio.run(text_to_speech(script, "docent_voice.mp3"))
    os.startfile("docent_voice.mp3")

if __name__ == "__main__":
    json_docent()
