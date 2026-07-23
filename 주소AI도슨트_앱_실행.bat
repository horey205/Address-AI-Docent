@echo off
title Address AI Docent Launcher

cd /d "%~dp0"

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto :run_app
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto :run_app
)

echo [ERROR] Python was not found. Please install Python.
pause
exit /b 1

:run_app
%PYTHON_CMD% -c "import streamlit, google.genai, edge_tts" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing required packages...
    %PYTHON_CMD% -m pip install -r requirements.txt
)

echo [INFO] Starting Streamlit server...
%PYTHON_CMD% -m streamlit run app.py
pause


