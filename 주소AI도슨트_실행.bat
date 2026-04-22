@echo off
title 주소 AI 도슨트 실행기
cd /d "%~dp0"

echo [1/2] 의존성 확인 중...
:: 가상 환경이 있으면 활성화
if exist venv\Scripts\activate (
    call venv\Scripts\activate
)

echo [2/2] 주소 AI 도슨트 대시보드 시작...
streamlit run law_dashboard.py

pause
