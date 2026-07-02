#!/usr/bin/env bash
# Установка Monolyth OSINT для Linux / macOS
set -e

cd "$(dirname "$0")"

PYTHON_BIN="python3"
if ! command -v "$PYTHON_BIN" &> /dev/null; then
    echo "Ошибка: python3 не найден. Установите Python 3.9+ и повторите попытку."
    exit 1
fi

echo "==> Используется: $($PYTHON_BIN --version)"

echo "==> Создаю виртуальное окружение (.venv)..."
$PYTHON_BIN -m venv .venv

echo "==> Активирую виртуальное окружение..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Обновляю pip..."
pip install --upgrade pip

echo "==> Устанавливаю зависимости из requirements.txt..."
pip install -r requirements.txt

echo "==> Устанавливаю браузер для модуля MDWE (Playwright/Chromium)..."
python -m playwright install chromium || echo "Предупреждение: не удалось установить браузер Playwright автоматически. Выполните 'python -m playwright install chromium' вручную."

echo ""
echo "Установка завершена."
echo "Запуск: ./run.sh"
