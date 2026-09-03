import FreeSimpleGUI as sg
import subprocess
import os
import sys
import time
import threading
from cryptography.fernet import Fernet, InvalidToken
from pathlib import Path
import hashlib
import json


#Раскраска
BG          = "#0a0a14"      # deep dark background
BG2         = "#0f0f1e"      # slightly lighter panels
PANEL       = "#12122a"      # card/panel bg
BORDER      = "#1e1e4a"      # subtle borders
ACCENT1     = "#4040ff"      # electric blue
ACCENT2     = "#8800ff"      # neon violet
ACCENT3     = "#00cfff"      # cyan highlight
TEXT        = "#c8c8ff"      # soft white-blue text
TEXT_DIM    = "#5555aa"      # muted text
TEXT_BRIGHT = "#ffffff"      # pure white
SUCCESS     = "#00ff99"      # terminal green
DANGER      = "#ff3366"      # alert red
WARN        = "#ffaa00"      # warning amber

sg.theme_add_new("Monolith", {
    "BACKGROUND":           BG,
    "TEXT":                 TEXT,
    "INPUT":                BG2,
    "TEXT_INPUT":           TEXT_BRIGHT,
    "SCROLL":               PANEL,
    "BUTTON":               (TEXT_BRIGHT, ACCENT1),
    "PROGRESS":             (ACCENT2, BORDER),
    "BORDER":               1,
    "SLIDER_DEPTH":         0,
    "PROGRESS_DEPTH":       0,
})
sg.theme("Monolith")

FONT_TITLE  = ("Courier New", 11, "bold")
FONT_MONO   = ("Courier New", 9)
FONT_MONO_S = ("Courier New", 8)
FONT_LABEL  = ("Courier New", 9, "bold")

BANNER = """
  ███╗   ███╗ ██████╗ ███╗   ██╗ ██████╗ ██╗  ██╗   ██╗████████╗██╗  ██╗
  ████╗ ████║██╔═══██╗████╗  ██║██╔═══██╗██║  ╚██╗ ██╔╝╚══██╔══╝██║  ██║
  ██╔████╔██║██║   ██║██╔██╗ ██║██║   ██║██║   ╚████╔╝    ██║   ███████║
  ██║╚██╔╝██║██║   ██║██║╚██╗██║██║   ██║██║    ╚██╔╝     ██║   ██╔══██║
  ██║ ╚═╝ ██║╚██████╔╝██║ ╚████║╚██████╔╝███████╗██║      ██║   ██║  ██║
  ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝      ╚═╝   ╚═╝  ╚═╝ 
                  [ O P E N   S O U R C E   I N T E L L I G E N C E ]
"""

MODULES = [
    ("01", "LOCAL DATABASES",    "db.py",            "Query local breach & data sources"),
    ("02", "DOMAIN / IP CHECK",  "Ip.py",            "Reverse DNS, WHOIS, geo-lookup"),
    ("03", "EMAIL RECON",        "mail.py",           "Mail validation, breach search"),
    ("04", "PHONE LOOKUP",       "phone_number.py",   "Carrier, region, social footprint"),
    ("05", "USERNAME HUNT",      "Username.py",       "Cross-platform username discovery"),
    ("06", "SEARCH_ENGINE",      "Search_engine.py",  "Universal search engine for osint"),
    ("07", "Interactive Board beta",   "InterActiveBoard.py",   " Ineractive board for Investigation")
]

WEB_TOOLS = [
    ("ZoomEye",      "https://www.zoomeye.ai",                   "Internet asset search engine"),
    ("DNSDumpster",  "https://dnsdumpster.com",                  "DNS recon & record lookup"),
    ("Google Dig",   "https://toolbox.googleapps.com/apps/dig/", "Authoritative DNS queries"),
    ("OSINT Guide",  "https://github.com/OffcierCia/non-typical-OSINT-guide", "Non-typical OSINT guide"),
]

NORMAL_MOD = ["db.py", "Ip.py", "mail.py", "phone_number.py", "Username.py", "Search_engine.py"]
# ──────────────────────────────────────────────
def glitch_sep(width=70):
    chars = "▓░▒█▓░▒"
    return "".join(chars[i % len(chars)] for i in range(width))

def _sep(color=BORDER, pad=(0, 4)):
    return sg.HorizontalSeparator(color=color, pad=pad)


#   комната или header 
def make_header():
    return sg.Column([
        [sg.Text(BANNER, font=("Courier New", 7, "bold"),
                 text_color=ACCENT1, background_color=BG,
                 pad=((0,0),(8,0)))],
        [sg.Text(glitch_sep(90), font=("Courier New", 7),
                 text_color=ACCENT2, background_color=BG)],
        [sg.Text(" MONOLYTH OSINT v2.0  |  Select module or run sequence",
                 font=FONT_MONO_S, text_color=TEXT_DIM, background_color=BG)],
        [_sep(ACCENT2, (0,4))],
    ], background_color=BG, expand_x=True)


#   модуль карт  MODULE CARDS
def module_card(num, name, script, desc):
    key_run   = f"-RUN-{num}-"
    return [
        sg.Frame("", [
            [
                sg.Text(f" [{num}]", font=("Courier New", 11, "bold"),
                        text_color=ACCENT2, background_color=PANEL, size=(5,1)),
                sg.Column([
                    [sg.Text(name, font=FONT_LABEL,
                             text_color=ACCENT3, background_color=PANEL)],
                    [sg.Text(desc, font=FONT_MONO_S,
                             text_color=TEXT_DIM, background_color=PANEL)],
                ], background_color=PANEL, expand_x=True, pad=(0,0)),
                sg.Button("▶  RUN", key=key_run,
                          font=FONT_MONO, size=(10,1),
                          button_color=(TEXT_BRIGHT, ACCENT1),
                          border_width=0, pad=(6,4)),
            ]
        ], background_color=PANEL, border_width=1,
           relief=sg.RELIEF_FLAT, pad=((0,0),(2,2)),
           title_color=BORDER, expand_x=True)
    ]

#  web tools panel
def make_web_tools():
    rows = [[
        sg.Text(f"  ◈  {name}", font=FONT_LABEL, text_color=ACCENT3,
                background_color=PANEL, size=(16,1)),
        sg.Text(desc, font=FONT_MONO_S, text_color=TEXT_DIM,
                background_color=PANEL, expand_x=True),
        sg.Button("↗ OPEN", key=f"-WEB-{name}-", font=FONT_MONO_S,
                  button_color=(ACCENT3, PANEL), border_width=1, pad=(4,2)),
    ] for name, url, desc in WEB_TOOLS]

    return sg.Frame("  ◈ WEB INSTRUMENTS ", rows,
                    font=FONT_LABEL, title_color=ACCENT2,
                    background_color=PANEL, border_width=1,
                    relief=sg.RELIEF_FLAT, expand_x=True, pad=(0,4))


#   output console
def make_console():
    return sg.Frame("  ◈ CONSOLE OUTPUT ", [
        [sg.Multiline(
            default_text=(
                f"[{time.strftime('%H:%M:%S')}] MONOLYTH OS▓NT — system ready\n"
                f"[{time.strftime('%H:%M:%S')}] Awaiting operator command...\n"
            ),
            key="-LOG-",
            font=("Courier New", 8),
            text_color=SUCCESS,
            background_color="#04040d",
            size=(None, 10),
            expand_x=True,
            expand_y=True,
            autoscroll=True,
            disabled=True,
            no_scrollbar=False,
            pad=(4,4),
        )],
        [
            sg.Button("CLEAR LOG", key="-CLEAR-", font=FONT_MONO_S,
                      button_color=(TEXT_DIM, BORDER), border_width=0,
                      pad=(4,4)),
            sg.Push(background_color=PANEL),
            sg.Button("▶▶  RUN ALL MODULES", key="-RUNALL-",
                      font=FONT_LABEL, size=(22,1),
                      button_color=(TEXT_BRIGHT, ACCENT2),
                      border_width=0, pad=(4,4)),
        ],
    ], font=FONT_LABEL, title_color=ACCENT2,
       background_color=PANEL, border_width=1,
       relief=sg.RELIEF_FLAT, expand_x=True, expand_y=True, pad=(0,4))

#   status bar
def make_statusbar():
    return [
        sg.Text("◈", text_color=ACCENT2, background_color=BG, font=FONT_MONO_S),
        sg.Text("STATUS:", text_color=TEXT_DIM, background_color=BG, font=FONT_MONO_S),
        sg.Text("IDLE", key="-STATUS-", text_color=SUCCESS,
                background_color=BG, font=FONT_MONO_S, size=(20,1)),
        sg.Push(background_color=BG),
        sg.Text(f"OPERATOR SESSION  {time.strftime('%Y-%m-%d  %H:%M')}",
                text_color=TEXT_DIM, background_color=BG, font=FONT_MONO_S),
        sg.Text(" ◈ ", text_color=ACCENT2, background_color=BG, font=FONT_MONO_S),
        sg.Button("EXIT", key="-EXIT-", font=FONT_MONO_S, size=(6,1),
                  button_color=(DANGER, BG2), border_width=1, pad=(2,2)),
    ]


#   layout
def build_layout():
    left_col = sg.Column([
        [make_header()],
        *[module_card(*m) for m in MODULES],
        [_sep(BORDER, (0,6))],
        [make_web_tools()],
    ], background_color=BG, vertical_alignment="top",
       expand_x=True, expand_y=True,
       scrollable=False, pad=((10,6),(8,8)))

    right_col = sg.Column([
        [make_console()],
    ], background_color=BG, expand_x=True, expand_y=True,
       pad=((6,10),(8,8)))

    layout = [
        [left_col, right_col],
        [_sep(ACCENT2, (0,2))],
        make_statusbar(),
    ]
    return layout


#   helpes
def log(window, message: str):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] {message}", text_color=TEXT, end="\n")

def log_ok(window, message: str):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] ✓ {message}", text_color=SUCCESS, end="\n")

def log_err(window, message: str):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] ✗ {message}", text_color=DANGER, end="\n")

def set_status(window, text, color=SUCCESS):
    window["-STATUS-"].update(value=text, text_color=color)

#debri____________________________________________________________________
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()

def check_module(window):

    KEY = b"5QSKPN-YJWW3NIe5kPmOnTOxw8RYM_UHFoj3QbiEW7o="

    def sha256_file(path: Path) -> str:                # function connected to verify_module
        h = hashlib.sha256()

        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)

        return h.hexdigest()

    def load_manifest_from_memory(path: Path):
        try:
            fernet = Fernet(KEY)

            # reading encrypted file
            encrypted_data = path.read_bytes()

            # decrypting file in memory(not hardware)
            decrypted_data = fernet.decrypt(encrypted_data)

            # JSON also returning into memory
            manifest = json.loads(decrypted_data.decode("utf-8"))

            return manifest

        except FileNotFoundError:
            print(f"Manifest not found: {path}")
            return None

        except InvalidToken:
            print("Manifest is corrupted or key is incorrect")
            return None

        except json.JSONDecodeError:
            print("Decrypted manifest is not valid JSON")
            return None

    def verify_module(window, module_dir: Path, module_manifest: dict):
        for filename, info in module_manifest.items():
            path = module_dir / filename

            if not path.is_file():
                log(window, f"File not found: {filename}")
                return False

            expected_size = info["size"]
            actual_size = path.stat().st_size

            if actual_size != expected_size:
                return False

            expected_hash = info["sha256"]
            actual_hash = sha256_file(path)

            if actual_hash != expected_hash:
                return False
        return True
    def check_module(window):
        root_dir = Path(__file__).resolve().parent
        module_dir = root_dir / "Methods"

        encrypted_manifest = module_dir / "manifest.dat"

        # manifest only like python dict in memory
        manifest = load_manifest_from_memory(encrypted_manifest)

        if manifest is None:
            log(window, "Manifest verification failed")
            return False

        if not verify_module(window, module_dir, manifest):
            log(window, "Module verification failed")
            return False

        log(window, "Module verification successful")
        return True
#debri____________________________________________________________________
def run_script(script, window):
    
    path = os.path.join("Methods", script)
    if not os.path.exists(path):
        log_err(window, f"Module not found: {path}")
        set_status(window, "MODULE NOT FOUND", DANGER)
        return
    log(window, f"Launching module: {script}")
    set_status(window, f"RUNNING {script}...", WARN)
    try:
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True
        )
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                window["-LOG-"].print(f"  ▸ {line}", text_color=TEXT, end="\n")
        if result.returncode == 0:
            log_ok(window, f"{script} — completed successfully")
            set_status(window, "COMPLETED", SUCCESS)
        else:
            log_err(window, f"{script} — exit code {result.returncode}")
            if result.stderr:
                window["-LOG-"].print(f"  {result.stderr[:200]}", text_color=DANGER, end="\n")
            set_status(window, "ERROR", DANGER)
    except subprocess.TimeoutExpired:
        log_err(window, f"{script} — timed out (120s)")
        set_status(window, "TIMEOUT", DANGER)
    except Exception as e:
        log_err(window, f"{script} — exception: {e}")
        set_status(window, "EXCEPTION", DANGER)

def open_url(url):
    import webbrowser
    webbrowser.open(url)

#   main loop
def main():
    sg.set_options(
        element_padding=(0, 0),
        margins=(0, 0),
    )
    window = sg.Window(
        "MONOLYTH :: OSINT Framework",
        build_layout(),
        background_color=BG,
        size=(1280, 820),
        resizable=True,
        finalize=True,
        titlebar_background_color=BG,
        titlebar_text_color=ACCENT3,
        use_custom_titlebar=False,
    )

    # Script key → filename map
    run_map = {f"-RUN-{num}-": script for num, _, script, _ in MODULES}
    url_map  = {f"-WEB-{name}-": url   for name, url, _ in WEB_TOOLS}

    while True:
        check_module(window)
        event, _ = window.read()

        if event in (sg.WIN_CLOSED, "-EXIT-", "q"):
            break

        elif event in run_map:
            script = run_map[event]
            t = threading.Thread(target=run_script, args=(script, window), daemon=True)
            t.start()

        elif event in url_map:
            open_url(url_map[event])
            log(window, f"Opening: {url_map[event]}")

        elif event == "-RUNALL-":
            def run_all():
                set_status(window, "RUNNING ALL...", WARN)
                log(window, "═" * 50)
                log(window, "SEQUENCE START — running all modules")
                for _, name, script, _ in MODULES:
                    log(window, f"── {name}")
                    run_script(script, window)
                log(window, "SEQUENCE COMPLETE")
                log(window, "═" * 50)
                set_status(window, "ALL DONE", SUCCESS)
            threading.Thread(target=run_all, daemon=True).start()

        elif event == "-CLEAR-":
            window["-LOG-"].update(value="")
            log(window, "Console cleared.")

    window.close()

if __name__ == "__main__":
    main()


    