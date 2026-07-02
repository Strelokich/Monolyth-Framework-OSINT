# Monolyth OSINT

A desktop GUI tool for OSINT (Open Source Intelligence) reconnaissance: IP/domain checks, email lookup, phone number lookup, username search across multiple platforms, local database (CSV/XLSX) search, web page scanning, and an interactive board for visualizing investigation links.

> ⚠️ **Disclaimer.** This tool is intended for lawful use only: your own OSINT research, security testing of your own resources, journalistic investigations, education, and similar legal purposes, with the data owner's consent where required by law. The user bears full responsibility for complying with the laws of their country when using this software. Do not use this tool to stalk, surveil, or otherwise violate people's privacy without a lawful basis.

## Features

| # | Module | File | Description |
|---|--------|------|----------|
| 01 | Local Databases | `Methods/db.py` | Search CSV/XLSX files in a chosen directory |
| 02 | IP / Domain | `Methods/Ip.py` | Reverse DNS, WHOIS, geolocation |
| 03 | Email | `Methods/mail.py` | Email validation, related search |
| 04 | MDWE | `Methods/mdwe.py` | Metadata and entity extraction from web pages (uses Playwright) |
| 05 | Phone | `Methods/phone_number.py` | Carrier, region, timezone lookup |
| 06 | Username | `Methods/Username.py` | Username search across multiple platforms (uses a Sherlock/WhatsMyName-style database) |
| 07 | Search Engine | `Methods/Search_engine.py` | Quick access to search dorks and external OSINT services |
| 08 | Interactive Board | `Methods/InterActiveBoard.py` | Link-analysis board for visualizing an investigation (Tkinter) |

Plus a quick-links panel to external web tools (ZoomEye, DNSDumpster, Google Dig, etc.).

## Requirements

- Python **3.9+** (3.10–3.12 recommended)
- Windows 10/11, macOS 12+, or Linux (Ubuntu/Debian/Fedora/Arch, etc.)
- The Interactive Board module (Tkinter) may require a system package on Linux:
  ```bash
  # Debian/Ubuntu
  sudo apt install python3-tk
  # Fedora
  sudo dnf install python3-tkinter
  # Arch
  sudo pacman -S tk
  ```
- The MDWE module requires a Chromium browser, installed via Playwright (see installation below — done automatically).

## Installation

### Windows

1. Install [Python 3.9+](https://www.python.org/downloads/), checking **Add python.exe to PATH**.
2. Download/clone the repository and open the project folder.
3. Double-click `install.bat` **or** run in a console:
   ```bat
   install.bat
   ```
4. To run: double-click `run.bat` or run `run.bat` in a console.

### macOS / Linux

```bash
git clone <your_repository_URL>
cd <repository_folder>
chmod +x install.sh run.sh
./install.sh
./run.sh
```

### Manual installation (any OS)

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium   # required for the MDWE module
python OSINT.py
```

## Project Structure

```
.
├── OSINT.py                  # Main window / launcher for all modules
├── requirements.txt
├── install.sh / install.bat  # Installation scripts
├── run.sh / run.bat          # Run scripts
├── LICENSE
└── Methods/
    ├── db.py                 # Module 01
    ├── Ip.py                 # Module 02
    ├── mail.py                # Module 03
    ├── mdwe.py                # Module 04
    ├── phone_number.py        # Module 05
    ├── Username.py            # Module 06
    ├── Search_engine.py       # Module 07
    ├── InterActiveBoard.py    # Module 08
    ├── ua.txt                 # User-Agent list
    ├── proxies_http.txt       # HTTP proxy list (optional)
    ├── Logs/                  # Module run logs/results (created automatically)
    └── resources/
        ├── data.json          # Site database for username search
        ├── data.schema.json   # Schema for data.json
        └── wmn.json           # Additional database (WhatsMyName-style)
```

## Running a Single Module

Each module can also be run directly, bypassing the main menu:

```bash
source .venv/bin/activate
python Methods/Ip.py
```

## Publishing to GitHub

The repository is already ready for publishing:

```bash
cd <project_folder>
git init
git add .
git commit -m "Initial commit: Monolyth OSINT"
git branch -M main
git remote add origin <your_GitHub_repository_URL>
git push -u origin main
```

The `.gitignore` and `.gitattributes` files are already configured so that:
- virtual environments, caches, `__pycache__`, and logs from `Methods/Logs/` are not committed to the repository;
- user CSV/XLSX databases (used by the `db.py` module) are not committed by default;
- line endings are correctly normalized between Windows and Unix systems.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'FreeSimpleGUI'`** — the virtual environment isn't activated, or `pip install -r requirements.txt` hasn't been run.
- **Playwright doesn't launch the browser** — run `python -m playwright install chromium` inside the activated `.venv`.
- **The Interactive Board module won't open on Linux** — install the `python3-tk` system package (see the Requirements section).
- **Antivirus blocks the app on Windows** — some antivirus software flags OSINT tools with networking features; add the project folder to exclusions if needed.

## License

This project is distributed under the [MIT License](LICENSE). Replace the `LICENSE` file with a license of your choice before publishing, if needed.
