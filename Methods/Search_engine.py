import os
import sys
import time
import threading
import subprocess
import webbrowser
from pathlib import Path

import FreeSimpleGUI as sg


#раскраска
BG          = "#0a0a14"
BG2         = "#0f0f1e"
PANEL       = "#12122a"
BORDER      = "#1e1e4a"
ACCENT1     = "#4040ff"
ACCENT2     = "#8800ff"
ACCENT3     = "#00cfff"
TEXT        = "#c8c8ff"
TEXT_DIM    = "#5555aa"
TEXT_BRIGHT = "#ffffff"
SUCCESS     = "#00ff99"
DANGER      = "#ff3366"
WARN        = "#ffaa00"

sg.theme_add_new("Monolith", {
    "BACKGROUND":     BG,
    "TEXT":           TEXT,
    "INPUT":          BG2,
    "TEXT_INPUT":     TEXT_BRIGHT,
    "SCROLL":         PANEL,
    "BUTTON":         (TEXT_BRIGHT, ACCENT1),
    "PROGRESS":       (ACCENT2, BORDER),
    "BORDER":         1,
    "SLIDER_DEPTH":   0,
    "PROGRESS_DEPTH": 0,
})
sg.theme("Monolith")

FONT_TITLE  = ("Courier New", 11, "bold")
FONT_MONO   = ("Courier New", 9)
FONT_MONO_S = ("Courier New", 8)
FONT_MONO_L = ("Courier New", 13, "bold")
FONT_LABEL  = ("Courier New", 9, "bold")

BANNER = """
  ███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗    ███████╗███╗   ██╗ ██████╗
  ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║    ██╔════╝████╗  ██║██╔════╝
  ███████╗█████╗  ███████║██████╔╝██║     ███████║    █████╗  ██╔██╗ ██║██║  ███╗
  ╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║    ██╔══╝  ██║╚██╗██║██║   ██║
  ███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║    ███████╗██║ ╚████║╚██████╔╝
  ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═══╝ ╚═════╝
                          [ I N T E L L I G E N C E   S E A R C H ]
"""


#поисковики

ENGINES = [
    # (display_name,  key_suffix,  url_template,                                   category)
    ("Google",        "google",    "https://www.google.com/search?q={q}",           "GENERAL"),
    ("Bing",          "bing",      "https://www.bing.com/search?q={q}",             "GENERAL"),
    ("DuckDuckGo",    "ddg",       "https://duckduckgo.com/?q={q}",                 "GENERAL"),
    ("Startpage",     "startpage", "https://www.startpage.com/search?q={q}",        "GENERAL"),
    ("Shodan",        "shodan",    "https://www.shodan.io/search?query={q}",         "OSINT"),
    ("Censys",        "censys",    "https://search.censys.io/search?resource=hosts&q={q}", "OSINT"),
    ("ZoomEye",       "zoomeye",   "https://www.zoomeye.ai/searchResult?q={q}",     "OSINT"),
    ("GreyNoise",     "greynoise", "https://viz.greynoise.io/query/?gnql={q}",      "OSINT"),
    ("Ahmia",         "ahmia",     "https://ahmia.fi/search/?q={q}&8fcfd8=a29a7f",                "DARKNET"),
    ("Grep.app",      "grep",      "https://grep.app/search?q={q}",                 "CODE"),
    ("GitHub",        "github",    "https://github.com/search?q={q}",               "CODE"),
    ("Pastebin",      "pastebin",  "https://pastebin.com/search?q={q}",             "LEAKS"),
    ("IntelX",        "intelx",    "https://intelx.io/?s={q}",                      "LEAKS"),
    ("Have I Pwned",  "hibp",      "https://haveibeenpwned.com/account/{q}",        "LEAKS"),
    ("Wayback",       "wayback",   "https://web.archive.org/web/*/{q}",             "ARCHIVE"),
    ("CachedView",    "cached",    "https://cachedview.nl/",                         "ARCHIVE"),
    ("Yandex",        "yandex",    "https://yandex.com/search/?text={q}",           "GENERAL"),
]

CATEGORIES = ["ALL", "GENERAL", "OSINT", "CODE", "LEAKS", "ARCHIVE", "DARKNET"]


#автозапуск браузеров

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

BROWSERS = [
    ("Firefox",   "firefox",   str(BASE_DIR / "browser" / "FirefoxPortable" / "FirefoxPortable.exe")),   # fill paths as needed
    ("Chromium",  "chromium",  str(BASE_DIR / "browser" / "GoogleChromePortable" / "GoogleChromePortable.exe")),
    ("Tor",       "tor",       str(BASE_DIR / "browser" / "TorPortable" / "TorPortable" / "firefox.exe")), 
    ("InteractiveBoard", "Board",   str(BASE_DIR / "browser" / "InterActiveBoard.py")), # system default
]


#быстрый запуск
#Add your own programs here:
#("Label",  r"C:\path\to\program.exe",  "Short description")
PROGRAMS = [
    ("Nmap",        r"",   "Port scanner"),
    ("Metasploit",  r"",   "Exploit framework"),
    ("Burp Suite",  r"",   "Web proxy / scanner"),
    ("CyberChef",   r"", "Data transform tool"),
    ("Maltego",     r"",   "OSINT visualiser"),
]


#помощники

def glitch_sep(width=70):
    chars = "▓░▒█▓░▒"
    return "".join(chars[i % len(chars)] for i in range(width))
def _sep(color=BORDER, pad=(0, 4)):
    return sg.HorizontalSeparator(color=color, pad=pad)
def log(window, msg):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] {msg}", text_color=TEXT, end="\n")
def log_ok(window, msg):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] ✓ {msg}", text_color=SUCCESS, end="\n")
def log_err(window, msg):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] ✗ {msg}", text_color=DANGER, end="\n")
def log_result(window, msg):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}]   {msg}", text_color=ACCENT3, end="\n")
def set_status(window, text, color=SUCCESS):
    window["-STATUS-"].update(value=text, text_color=color)


#Поисковая логика
def do_search(query, selected_engines, window):
    if not query:
        log_err(window, "Query is empty.")
        set_status(window, "NO QUERY", DANGER)
        return

    set_status(window, "SEARCHING…", WARN)
    log(window, "─" * 55)
    log(window, f"Query: '{query}'")
    log(window, f"Engines: {len(selected_engines)}")
    log(window, "─" * 55)

    for name, key, url_tpl, _ in ENGINES:
        if key in selected_engines:
            url = url_tpl.replace("{q}", query.replace(" ", "+"))
            log_result(window, f"↗  {name:14} {url}")
            webbrowser.open(url)
            time.sleep(0.3)

    log_ok(window, f"Opened {len(selected_engines)} search tab(s).")
    set_status(window, f"{len(selected_engines)} TABS OPENED", SUCCESS)


def open_single(name, url_tpl, query, window):
    url = url_tpl.replace("{q}", query.replace(" ", "+"))
    log_result(window, f"↗  {name}  →  {url}")
    webbrowser.open(url)
    set_status(window, f"OPENED {name.upper()}", SUCCESS)



#запуск браузера
def launch_browser(label, path, window):
    if label == "Default" or not path:
        log(window, "Opening system default browser…")
        webbrowser.open("about:blank")
        return
    if path.startswith("http"):
        webbrowser.open(path)
        return
    if not os.path.exists(path):
        log_err(window, f"Browser not found: {path}")
        set_status(window, "NOT FOUND", DANGER)
        return
    try:
        subprocess.Popen([path])
        log_ok(window, f"{label} launched.")
        set_status(window, f"{label.upper()} OPEN", SUCCESS)
    except Exception as e:
        log_err(window, f"{label}: {e}")
        set_status(window, "ERROR", DANGER)


def launch_program(label, path, window):
    if not path:
        log_err(window, f"Path not configured for {label}.")
        set_status(window, "NO PATH SET", WARN)
        return
    if path.startswith("http"):
        webbrowser.open(path)
        log_ok(window, f"{label} opened in browser.")
        return
    if not os.path.exists(path):
        log_err(window, f"Not found: {path}")
        set_status(window, "NOT FOUND", DANGER)
        return
    try:
        subprocess.Popen([path])
        log_ok(window, f"{label} launched.")
        set_status(window, f"{label.upper()} RUNNING", SUCCESS)
    except Exception as e:
        log_err(window, f"{label}: {e}")
        set_status(window, "ERROR", DANGER)



#engine card row(checkbox + button)
def engine_row(name, key, url_tpl, category):
    cat_colors = {
        "GENERAL": ACCENT1, "OSINT": ACCENT2, "CODE": ACCENT3,
        "LEAKS": DANGER, "ARCHIVE": WARN, "DARKNET": TEXT_DIM,
    }
    cat_color = cat_colors.get(category, TEXT_DIM)
    return [
        sg.Checkbox("", key=f"-CHK-{key}-", default=False,
                    background_color=PANEL, text_color=TEXT,
                    checkbox_color=BG2, pad=((4, 2), 2)),
        sg.Text(f"{name:<16}", font=FONT_MONO, text_color=TEXT_BRIGHT,
                background_color=PANEL, size=(14, 1)),
        sg.Text(f"[{category}]", font=FONT_MONO_S, text_color=cat_color,
                background_color=PANEL, size=(9, 1)),
        sg.Button("↗", key=f"-OPEN-{key}-", font=FONT_MONO_S,
                  button_color=(ACCENT3, PANEL), border_width=1,
                  size=(3, 1), pad=(2, 2),
                  tooltip=f"Open {name} now"),
    ]

#layout
def build_layout():
    #Header 
    header = sg.Column([
        [sg.Text(BANNER, font=("Courier New", 7, "bold"),
                 text_color=ACCENT1, background_color=BG, pad=((0,0),(8,0)))],
        [sg.Text(glitch_sep(90), font=("Courier New", 7),
                 text_color=ACCENT2, background_color=BG)],
        [sg.Text(" MONOLYTH OSINT v2.0  |  Search Engine Module",
                 font=FONT_MONO_S, text_color=TEXT_DIM, background_color=BG)],
        [_sep(ACCENT2, (0, 4))],
    ], background_color=BG, expand_x=True)

    #Search bar
    search_bar = sg.Frame("  ◈ QUERY ", [
        [
            sg.Text("▶", font=FONT_MONO_L, text_color=ACCENT2,
                    background_color=PANEL),
            sg.Input(key="-QUERY-", font=("Courier New", 12),
                     size=(40, 1), background_color=BG2,
                     text_color=TEXT_BRIGHT, border_width=1,
                     pad=((6, 6), 4)),
            sg.Button("  SEARCH  ", key="-SEARCH-",
                      font=("Courier New", 10, "bold"),
                      size=(10, 1), button_color=(TEXT_BRIGHT, ACCENT1),
                      border_width=0, pad=(6, 4)),
            sg.Button("SELECT ALL", key="-SEL_ALL-", font=FONT_MONO_S,
                      button_color=(ACCENT3, PANEL), border_width=1,
                      pad=(4, 4)),
            sg.Button("CLEAR ALL",  key="-CLR_ALL-", font=FONT_MONO_S,
                      button_color=(TEXT_DIM, BORDER), border_width=0,
                      pad=(4, 4)),
        ],
        [
            sg.Text("FILTER:", font=FONT_LABEL, text_color=ACCENT3,
                    background_color=PANEL),
            *[
                sg.Button(cat, key=f"-CAT-{cat}-", font=FONT_MONO_S,
                          button_color=(TEXT_DIM, BORDER), border_width=1,
                          pad=(3, 2))
                for cat in CATEGORIES
            ],
        ],
    ], font=FONT_LABEL, title_color=ACCENT2, background_color=PANEL,
       border_width=1, relief=sg.RELIEF_FLAT, expand_x=True, pad=(0, 4))

    #Engine list
    engine_rows = [engine_row(n, k, u, c) for n, k, u, c in ENGINES]

    engine_panel = sg.Frame("  ◈ SEARCH ENGINES ", [
        *engine_rows,
    ], font=FONT_LABEL, title_color=ACCENT2, background_color=PANEL,
       border_width=1, relief=sg.RELIEF_FLAT,
       expand_x=True, pad=(0, 4))

    #Browser launchers
    browser_rows = [[
        sg.Text(f"  ◈  {label}", font=FONT_LABEL, text_color=ACCENT3,
                background_color=PANEL, size=(12, 1)),
        sg.Input(default_text=path, key=f"-BRPATH-{key}-",
                 font=FONT_MONO_S, size=(32, 1),
                 background_color=BG2, text_color=TEXT_BRIGHT,
                 border_width=1),
        sg.FileBrowse("…", font=FONT_MONO_S,
                      button_color=(TEXT_DIM, BORDER),
                      target=f"-BRPATH-{key}-",
                      file_types=(("Executables", "*.exe"),("All","*.*")),
                      pad=(2, 2)),
        sg.Button("▶ OPEN", key=f"-BR-{key}-", font=FONT_MONO_S,
                  button_color=(TEXT_BRIGHT, ACCENT1), border_width=0,
                  pad=(6, 2)),
    ] for label, key, path in BROWSERS]

    browser_panel = sg.Frame("  ◈ BROWSER LAUNCHERS ", browser_rows,
                             font=FONT_LABEL, title_color=ACCENT2,
                             background_color=PANEL, border_width=1,
                             relief=sg.RELIEF_FLAT, expand_x=True, pad=(0, 4))

    #Programs panel
    prog_rows = [[
        sg.Text(f"  ◈  {label}", font=FONT_LABEL, text_color=ACCENT3,
                background_color=PANEL, size=(12, 1)),
        sg.Text(desc, font=FONT_MONO_S, text_color=TEXT_DIM,
                background_color=PANEL, size=(22, 1)),
        sg.Input(default_text=path, key=f"-PROGPATH-{label}-",
                 font=FONT_MONO_S, size=(20, 1),
                 background_color=BG2, text_color=TEXT_BRIGHT,
                 border_width=1),
        sg.FileBrowse("…", font=FONT_MONO_S,
                      button_color=(TEXT_DIM, BORDER),
                      target=f"-PROGPATH-{label}-",
                      file_types=(("Executables","*.exe"),("All","*.*")),
                      pad=(2, 2)),
        sg.Button("▶", key=f"-PROG-{label}-", font=FONT_MONO_S,
                  button_color=(TEXT_BRIGHT, ACCENT2), border_width=0,
                  size=(3, 1), pad=(4, 2)),
    ] for label, path, desc in PROGRAMS]

    prog_panel = sg.Frame("  ◈ QUICK LAUNCH ", prog_rows,
                          font=FONT_LABEL, title_color=ACCENT2,
                          background_color=PANEL, border_width=1,
                          relief=sg.RELIEF_FLAT, expand_x=True, pad=(0, 4))

    #Console
    console = sg.Frame("  ◈ CONSOLE OUTPUT ", [
        [sg.Multiline(
            default_text=(
                f"[{time.strftime('%H:%M:%S')}] Search Engine module — ready\n"
                f"[{time.strftime('%H:%M:%S')}] Select engines, type a query and press SEARCH.\n"
            ),
            key="-LOG-",
            font=("Courier New", 8),
            text_color=SUCCESS,
            background_color="#04040d",
            size=(None, 14),
            expand_x=True, expand_y=True,
            autoscroll=True, disabled=True,
            no_scrollbar=False, pad=(4, 4),
        )],
        [
            sg.Button("CLEAR LOG", key="-CLEAR-", font=FONT_MONO_S,
                      button_color=(TEXT_DIM, BORDER), border_width=0,
                      pad=(4, 4)),
        ],
    ], font=FONT_LABEL, title_color=ACCENT2, background_color=PANEL,
       border_width=1, relief=sg.RELIEF_FLAT,
       expand_x=True, expand_y=True, pad=(0, 4))

    #Status bar
    statusbar = [
        sg.Text("◈", text_color=ACCENT2, background_color=BG, font=FONT_MONO_S),
        sg.Text("STATUS:", text_color=TEXT_DIM, background_color=BG, font=FONT_MONO_S),
        sg.Text("IDLE", key="-STATUS-", text_color=SUCCESS,
                background_color=BG, font=FONT_MONO_S, size=(22, 1)),
        sg.Push(background_color=BG),
        sg.Text(f"OPERATOR SESSION  {time.strftime('%Y-%m-%d  %H:%M')}",
                text_color=TEXT_DIM, background_color=BG, font=FONT_MONO_S),
        sg.Text(" ◈ ", text_color=ACCENT2, background_color=BG, font=FONT_MONO_S),
        sg.Button("EXIT", key="-EXIT-", font=FONT_MONO_S, size=(6, 1),
                  button_color=(DANGER, BG2), border_width=1, pad=(2, 2)),
    ]

    #Two-column layout
    left = sg.Column([
        [header],
        [search_bar],
        [engine_panel],
    ], background_color=BG, vertical_alignment="top",
       expand_x=True, expand_y=True,
       pad=((10, 6), (8, 8)), scrollable=True,
       vertical_scroll_only=True, size=(None, 720))

    right = sg.Column([
        [browser_panel],
        [prog_panel],
        [console],
    ], background_color=BG, expand_x=True, expand_y=True,
       pad=((6, 10), (8, 8)))

    layout = [
        [left, right],
        [_sep(ACCENT2, (0, 2))],
        statusbar,
    ]
    return layout



#main loop
def main():
    sg.set_options(element_padding=(0, 0), margins=(0, 0))
    window = sg.Window(
        "MONOLYTH :: Search Engine",
        build_layout(),
        background_color=BG,
        size=(1400, 820),
        resizable=True,
        finalize=True,
        use_custom_titlebar=False,
        return_keyboard_events=True,
    )
    # maps
    open_map   = {f"-OPEN-{k}-":  (n, u) for n, k, u, _ in ENGINES}
    br_map     = {f"-BR-{k}-":    (l, k)  for l, k, _ in BROWSERS}
    prog_map   = {f"-PROG-{l}-":  (l,)    for l, _, _ in PROGRAMS}

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "-EXIT-"):
            break
        #Enter key in search box
        elif event in ("\r", "Return:36", "Return:13") or event == "-SEARCH-":
            query = values.get("-QUERY-", "").strip()
            selected = [k for _, k, _, _ in ENGINES
                        if values.get(f"-CHK-{k}-", False)]
            if not selected:
                log_err(window, "No engines selected. Use checkboxes or SELECT ALL.")
                set_status(window, "NO ENGINES", WARN)
                continue
            threading.Thread(
                target=do_search,
                args=(query, selected, window),
                daemon=True,
            ).start()

        #Single engine open
        elif event in open_map:
            name, url_tpl = open_map[event]
            query = values.get("-QUERY-", "").strip()
            threading.Thread(
                target=open_single,
                args=(name, url_tpl, query, window),
                daemon=True,
            ).start()

        #Category filter
        elif event.startswith("-CAT-"):
            cat = event.replace("-CAT-", "").replace("-", "")
            for name, key, _, engine_cat in ENGINES:
                match = (cat == "ALL") or (engine_cat == cat)
                window[f"-CHK-{key}-"].update(value=match)
            log(window, f"Filter applied: {cat}")

        #Select/Clear all
        elif event == "-SEL_ALL-":
            for _, key, _, _ in ENGINES:
                window[f"-CHK-{key}-"].update(value=True)

        elif event == "-CLR_ALL-":
            for _, key, _, _ in ENGINES:
                window[f"-CHK-{key}-"].update(value=False)

        #Browser launchers
        elif event in br_map:
            label, key = br_map[event]
            path = values.get(f"-BRPATH-{key}-", "").strip()
            threading.Thread(
                target=launch_browser,
                args=(label, path, window),
                daemon=True,
            ).start()

        #Program launchers
        elif event in prog_map:
            label = prog_map[event][0]
            path = values.get(f"-PROGPATH-{label}-", "").strip()
            threading.Thread(
                target=launch_program,
                args=(label, path, window),
                daemon=True,
            ).start()

        #Clear log
        elif event == "-CLEAR-":
            window["-LOG-"].update(value="")
            log(window, "Console cleared.")

    window.close()


if __name__ == "__main__":
    main()
