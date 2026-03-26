import pandas as pd
import json
import os

EXCEL_FILE = r'D:\AI_Class\주소AI도슨트\전국 도로명 부여사유 조회_2025.11.30 기준.xls'
JSON_FILE = r'D:\AI_Class\주소AI도슨트\road_names.json'

def convert_excel_to_json():
    print("엑셀 파일을 읽고 있습니다. 모든 시트(탭)를 통합합니다...")
    try:
        # 모든 시트 읽기 (sheet_name=None 은 모든 시트를 OrderedDict로 가져옴)
        all_sheets = pd.read_excel(EXCEL_FILE, sheet_name=None)
        
        combined_data = []
        for sheet_name, df in all_sheets.items():
            print(f"시트 처리 중: {sheet_name} (행 수: {len(df)})")
            # 결측치 처리
            df = df.fillna("")
            # 레코드 형태로 변환하여 리스트에 추가
            combined_data.extend(df.to_dict(orient='records'))
        
        print(f"총 {len(combined_data)}건의 데이터를 통합했습니다.")
        
        # JSON 저장
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 변환 완료! JSON 파일이 생성되었습니다: {JSON_FILE}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    convert_excel_to_json()
