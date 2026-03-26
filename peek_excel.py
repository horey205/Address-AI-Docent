import pandas as pd
import sys

try:
    file_path = r'D:\AI_Class\주소AI도슨트\전국 도로명 부여사유 조회_2025.11.30 기준.xls'
    # Try reading the first few rows
    df = pd.read_excel(file_path, nrows=10)
    print("--- HEADERS ---")
    print(df.columns.tolist())
    print("\n--- DATA ---")
    print(df.to_string())
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
