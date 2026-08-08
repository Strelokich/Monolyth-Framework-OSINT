@echo off
REM Установка Monolyth OSINT для Windows
setlocal

cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Ошибка: Python не найден в PATH. Установите Python 3.9+ с python.org
    echo и отметьте опцию "Add Python to PATH" при установке.
    pause
    exit /b 1
)

echo ==^> Создаю виртуальное окружение ^(.venv^)...
python -m venv .venv

echo ==^> Активирую виртуальное окружение...
call .venv\Scripts\activate.bat

echo ==^> Обновляю pip...
python -m pip install --upgrade pip

echo ==^> Устанавливаю зависимости из requirements.txt...
pip install -r requirements.txt


echo.
echo Установка завершена.
echo Запуск: run.bat
pause
