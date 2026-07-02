#!/usr/bin/env bash
# Запуск Monolyth OSINT для Linux / macOS
set -e

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Виртуальное окружение не найдено. Сначала выполните: ./install.sh"
    exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python OSINT.py
