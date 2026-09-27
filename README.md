# Monolyth OSINT


> ⚠️ **Дисклеймер.** Инструмент предназначен только для законной деятельности: собственных OSINT-исследований, проверки безопасности своих же ресурсов, журналистских расследований, обучения и аналогичных легальных целей, с согласия владельца данных там, где это требуется по закону. Пользователь несёт полную ответственность за соблюдение законодательства своей страны при использовании программы. Не используйте инструмент для преследования, слежки или иного нарушения приватности людей без законных оснований.

## Возможности

| № | Модуль | Файл | Описание |
|----|--------|------|------------------------------------------------------------------|
| 01 | Локальные базы | Methods/db.py - Поиск по CSV/XLSX файлам в выбранной директории 
| 02 | IP/Домен | Methods/Ip.py - Reverse DNS, WHOIS, гео-локация 
| 03 | Email | Methods/mail.py - Валидация почты, сопутствующий поиск 
| 05 | Телефон | Methods/phone_number.py - Оператор, регион, часовой пояс номера 
| 06 | Username | Methods/Username.py - Поиск ника на множестве платформ (использует базу как в Sherlock/WhatsMyName) 
| 07 | Поисковый движок | Methods/Search_engine.py - Быстрый доступ к поисковым дорками и внешним OSINT-сервисам 
| 08 | Interactive Board | Methods/InterActiveBoard.py - Доска связей для визуализации расследования 
| 09 | Интегрированый мною модуль для гео осинта Netryx Vision(код не мой но я буду в будущем его модифицировать по надобности моего проэкта)

Плюс панель быстрых ссылок на внешние веб-инструменты (ZoomEye, DNSDumpster, Google Dig и т.д.).

## Требования

- Python **3.9+** (рекомендуется 3.10–3.12)
- Windows 10/11, macOS 12+ или Linux (Ubuntu/Debian/Fedora/Arch и т.д.)
- Для модуля Interactive Board (Tkinter) на Linux может понадобиться системный пакет:
  ```bash
  # Debian/Ubuntu
  sudo apt install python3-tk
  # Fedora
  sudo dnf install python3-tkinter
  # Arch
  sudo pacman -S tk
  ```

## Установка

### Windows

1. Установите [Python 3.9+](https://www.python.org/downloads/), отметив галочку **Add python.exe to PATH**.
2. Скачайте/склонируйте репозиторий и откройте папку проекта.
3. Дважды кликните `install.bat` **или** выполните в консоли:
   ```bat
   install.bat
   ```
4. Запуск: дважды кликните `run.bat` или выполните `run.bat` в консоли.

### macOS / Linux

```bash
git clone <URL_вашего_репозитория>
cd <папка_репозитория>
chmod +x install.sh run.sh
./install.sh
./run.sh
```

### Установка вручную (любая ОС)

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python OSINT.py
```



## Запуск отдельного модуля

Каждый модуль можно запустить и напрямую, минуя главное меню:

```bash
source .venv/bin/activate
python Methods/Ip.py
```


## Возможные проблемы

- 1. **ModuleNotFoundError: No module named 'FreeSimpleGUI'** не активировано виртуальное окружение или не выполнен pip install -r requirements.txt.
- 3. **Модуль Interactive Board не открывается на Linux**  установите системный пакет python3-tk (см. раздел «Требования»).
- 4. **Антивирус блокирует запуск на Windows**  некоторые антивирусы настороженно относятся к OSINT-инструментам с сетевыми функциями; добавьте папку проекта в исключения при необходимости.

