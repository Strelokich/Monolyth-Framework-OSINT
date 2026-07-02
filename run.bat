@echo off
REM Запуск Monolyth OSINT для Windows
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Виртуальное окружение не найдено. Сначала запустите install.bat
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python OSINT.py
pause
