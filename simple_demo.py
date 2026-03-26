import pandas as pd
import edge_tts
import asyncio
import os

# 파일 경로 설정
EXCEL_FILE = r'D:\AI_Class\주소AI도슨트\전국 도로명 부여사유 조회_2025.11.30 기준.xls'

async def text_to_speech(text, output_file):
    """MS Edge TTS를 사용하여 음성 파일을 생성합니다."""
    voice = "ko-KR-SunHiNeural"  # 여성 목소리
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    print(f"\n🔊 음성 파일이 생성되었습니다: {output_file}")

def simple_docent():
    print("=== 주소 AI 도슨트 (Simple Demo) ===")
    
    # 1. 엑셀 데이터 로드
    try:
        print("데이터를 불러오는 중입니다...")
        df = pd.read_excel(EXCEL_FILE)
    except Exception as e:
        print(f"오류: 엑셀 파일을 읽을 수 없습니다. ({e})")
        return

    # 2. 도로명 입력 받기
    search_name = input("\n🔍 유래가 궁금한 도로명을 입력하세요 (예: 가로수길, 광명로): ").strip()

    if not search_name:
        print("도로명을 입력해주세요.")
        return

    # 3. 데이터 검색
    results = df[df['도로명'] == search_name]

    if results.empty:
        print(f"'{search_name}'에 대한 정보를 찾을 수 없습니다.")
        return

    # 4. 결과 출력 및 선택
    selected_reason = ""
    if len(results) > 1:
        print(f"\n📍 '{search_name}' 검색 결과가 {len(results)}건 있습니다. 지역을 선택하세요:")
        for i, (idx, row) in enumerate(results.iterrows()):
            print(f"[{i+1}] {row['시군구']}")
        
        try:
            choice = int(input("\n번호를 입력하세요: ")) - 1
            if 0 <= choice < len(results):
                selected_row = results.iloc[choice]
                selected_reason = selected_row['부여사유']
                print(f"\n📖 선택된 지역 ({selected_row['시군구']}) 유래: {selected_reason}")
            else:
                print("잘못된 번호입니다.")
                return
        except ValueError:
            print("숫자를 입력해주세요.")
            return
    else:
        selected_row = results.iloc[0]
        selected_reason = selected_row['부여사유']
        print(f"\n📖 {selected_row['시군구']}의 {search_name} 유래: {selected_reason}")

    # 5. TTS로 읽어주기
    if selected_reason:
        output_mp3 = "docent_voice.mp3"
        # 대본을 조금 더 부드럽게 만들기
        script = f"안녕하세요. 요청하신 {search_name}의 유래를 알려드릴게요. {selected_reason} 입니다. 즐거운 여행 되세요."
        
        # 비동기 함수 실행
        asyncio.run(text_to_speech(script, output_mp3))
        
        # 파일 실행 (Windows 환경)
        os.startfile(output_mp3)

if __name__ == "__main__":
    simple_docent()
