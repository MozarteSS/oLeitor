@echo off
cd /d "%~dp0"

:: First, check if the virtual environment exists
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

:: Verify if the chosen Python is accessible
"%PYTHON_EXE%" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado. Verifique se ele esta instalado no PATH do sistema, ou reinstale o .venv.
    pause
    exit /b
)

start "oLeitor Server" "%PYTHON_EXE%" server.py
timeout /t 3 /nobreak >nul
start "" "http://localhost:5000"
