# Monolyth OSINT

> ⚠️ **Disclaimer.** This tool is intended solely for lawful activities: conducting your own OSINT research, security testing of resources you own, journalistic investigations, education, and similar legitimate purposes, with the data owner's consent where required by law. The user bears full responsibility for complying with the laws of their country when using this program. Do not use this tool for stalking, surveillance, or any other violation of people's privacy without a lawful basis.

## Features

| № | Module | File | Description |
|----|--------|------|------------------------------------------------------------------|
| 01 | Local databases | Methods/db.py - Search across CSV/XLSX files in a selected directory |
| 02 | IP/Domain | Methods/Ip.py - Reverse DNS, WHOIS, geolocation |
| 03 | Email | Methods/mail.py - Email validation, related lookup |
| 05 | Phone | Methods/phone_number.py - Carrier, region, time zone of the number |
| 06 | Username | Methods/Username.py - Username search across multiple platforms (uses a database similar to Sherlock/WhatsMyName) |
| 07 | Search engine | Methods/Search_engine.py - Quick access to search dorks and external OSINT services |
| 08 | Interactive Board | Methods/InterActiveBoard.py - Link board for visualizing an investigation |
| 09 | + Netryx Vision. Integrated local service for GeoOsint

Plus a panel of quick links to external web tools (ZoomEye, DNSDumpster, Google Dorking, etc.).

## Requirements

- Python **3.9+** (3.10–3.12 recommended)
- Windows 10/11, macOS 12+, or Linux (Ubuntu/Debian/Fedora/Arch, etc.)
- The Interactive Board module (Tkinter) may require an additional system package on Linux:
  ```bash
  # Debian/Ubuntu
  sudo apt install python3-tk
  # Fedora
  sudo dnf install python3-tkinter
  # Arch
  sudo pacman -S tk
  ```

## Installation

### Windows

1. Install [Python 3.9+](https://www.python.org/downloads/), making sure to check **Add python.exe to PATH**.
2. Download/clone the repository and open the project folder.
3. Double-click `install.bat` **or** run it from the console:
   ```bat
   install.bat
   ```
4. To launch: double-click `run.bat` or run `run.bat` from the console.

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
python OSINT.py
```


## Running a single module

Each module can also be launched directly, bypassing the main menu:

```bash
source .venv/bin/activate
python Methods/Ip.py
```


## Common issues

- 1. **ModuleNotFoundError: No module named 'FreeSimpleGUI'** the virtual environment is not activated, or `pip install -r requirements.txt` was not run.
- 3. **The Interactive Board module doesn't open on Linux** install the `python3-tk` system package (see the "Requirements" section).
- 4. **Antivirus software blocks the launch on Windows** some antivirus programs are wary of OSINT tools with networking features; add the project folder to exclusions if needed.
