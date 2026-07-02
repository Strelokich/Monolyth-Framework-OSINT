import FreeSimpleGUI as sg
import threading
import time
import os
import sys
import json
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    "BACKGROUND":       BG,
    "TEXT":             TEXT,
    "INPUT":            BG2,
    "TEXT_INPUT":       TEXT_BRIGHT,
    "SCROLL":           PANEL,
    "BUTTON":           (TEXT_BRIGHT, ACCENT1),
    "PROGRESS":         (ACCENT2, BORDER),
    "BORDER":           1,
    "SLIDER_DEPTH":     0,
    "PROGRESS_DEPTH":   0,
})
sg.theme("Monolith")

FONT_MONO   = ("Courier New", 9)
FONT_MONO_S = ("Courier New", 8)
FONT_MONO_L = ("Courier New", 11, "bold")
FONT_LABEL  = ("Courier New", 9, "bold")

THREADS = 30
folder_path = Path("Logs")


#   парсер сайтов
STATIC_SITES = [
    ("Instagram",   "https://www.instagram.com/{u}"),
    ("VKontakte",   "https://vk.com/{u}"),
    ("Twitter/X",   "https://twitter.com/{u}"),
    ("Facebook",    "https://facebook.com/{u}"),
    ("LinkedIn",    "https://linkedin.com/in/{u}"),
    ("Reddit",      "https://www.reddit.com/user/{u}"),
    ("Snapchat",    "https://www.snapchat.com/add/{u}"),
    ("Flickr",      "https://flickr.com/people/{u}"),
    ("Vimeo",       "https://vimeo.com/{u}"),
    ("SoundCloud",  "https://soundcloud.com/{u}"),
    ("Medium",      "https://medium.com/@{u}"),
    ("Patreon",     "https://www.patreon.com/{u}"),
    ("Spotify",     "https://open.spotify.com/user/{u}"),
    ("Steam",       "https://steamcommunity.com/id/{u}"),
    ("Tumblr",      "https://{u}.tumblr.com/"),
    ("WordPress",   "https://{u}.wordpress.com/"),
    ("DeviantArt",  "https://{u}.deviantart.com/"),
    ("Pastebin",    "https://pastebin.com/u/{u}"),
    ("Keybase",     "https://keybase.io/{u}"),
    ("Dribbble",    "https://dribbble.com/{u}"),
    ("Pinterest",   "https://www.pinterest.com/{u}"),
    ("GitHub",      "https://github.com/{u}"),
    ("Behance",     "https://www.behance.net/{u}"),
    ("Bandcamp",    "https://bandcamp.com/{u}"),
]

DEFAULT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/119.0.0.0'
    )
}


#   логика сканирования
def check_url(name, url, window):
    try:
        r = requests.get(url, headers=DEFAULT_HEADERS, timeout=8, allow_redirects=True)
        if r.status_code == 200:
            return (name, url, True)
        return (name, url, False)
    except Exception:
        return (name, url, None)  # None = error/timeout


def run_scan(username, window, data_json_path=None, wmn_json_path=None):
    found = []
    errors = 0
    checked = 0
    total = len(STATIC_SITES)

    _log(window, f"TARGET  >>>  {username}", ACCENT3)
    _log(window, f"Platforms in static list: {total}", TEXT_DIM)
    _log(window, "─" * 54, BORDER)

    window["-PROGRESS-"].update(0, max=total)
    window["-STATUS-"].update("SCANNING...", text_color=WARN)

    def check_and_report(args):
        nonlocal checked, errors
        name, tpl = args
        url = tpl.replace("{u}", username)
        result = check_url(name, url, window)
        checked += 1
        pct = int(checked / total * 100)
        window["-PROGRESS-"].update(checked)
        window["-PCT-"].update(f"{pct}%")
        if result[2] is True:
            found.append((name, url))
            window["-LOG-"].print(f"  ◈  FOUND   {name:<14} {url}",
                                  text_color=SUCCESS, end="\n")
        elif result[2] is None:
            errors += 1

    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        list(ex.map(check_and_report, STATIC_SITES))

    _log(window, "─" * 54, BORDER)
    _log(window, f"Scan complete. Found: {len(found)}  |  Errors: {errors}", ACCENT3)

    # ── optional: DataJson scan ──
    if data_json_path and os.path.exists(data_json_path):
        _log(window, f"Loading data.json: {data_json_path}", TEXT_DIM)
        try:
            with open(data_json_path, 'r', encoding='utf-8') as f:
                targets = json.load(f)
                targets.pop('$schema', None)
            _log(window, f"data.json sites: {len(targets)}", TEXT_DIM)
            session = requests.Session()
            session.headers.update(DEFAULT_HEADERS)
            dj_found = 0

            def check_dj(item):
                nonlocal dj_found
                site_name, site_data = item
                url = site_data['url'].format(username)
                error_type = site_data.get('errorType')
                try:
                    r = session.get(url, headers=site_data.get('headers', {}),
                                    timeout=8, allow_redirects=True)
                except Exception:
                    return
                is_found = False
                if error_type == 'status_code':
                    is_found = r.status_code == 200
                elif error_type == 'message':
                    msgs = site_data.get('errorMsg', [])
                    if isinstance(msgs, str): msgs = [msgs]
                    is_found = not any(m in r.text for m in msgs)
                elif error_type == 'response_url':
                    is_found = r.url != site_data.get('errorUrl')
                if is_found:
                    dj_found += 1
                    window["-LOG-"].print(f"  ◈  [DJ]    {site_name:<14} {url}",
                                          text_color=ACCENT3, end="\n")

            with ThreadPoolExecutor(max_workers=THREADS) as ex:
                list(ex.map(check_dj, targets.items()))
            _log(window, f"data.json: {dj_found} accounts found", ACCENT3)
        except Exception as e:
            _log(window, f"data.json error: {e}", DANGER)

    # сохранить логи 
    folder_path.mkdir(parents=True, exist_ok=True)
    log_file = folder_path / f"username_{username}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"MONOLYTH USERNAME RECON — {username}\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            if found:
                for name, url in found:
                    f.write(f"[FOUND] {name}: {url}\n")
            else:
                f.write("No accounts found in static list.\n")
        _log(window, f"Report saved: {log_file}", TEXT_DIM)
    except Exception as e:
        _log(window, f"Save error: {e}", DANGER)

    window["-STATUS-"].update("IDLE", text_color=SUCCESS)
    window["-SCAN-BTN-"].update(disabled=False)
    window["-STOP-BTN-"].update(disabled=True)



#   помощ лог
def _log(window, msg, color=None):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] {msg}",
                          text_color=color or TEXT, end="\n")


#layout
BANNER = """\
  ██╗   ██╗███████╗███████╗██████╗ ███╗   ██╗ █████╗ ███╗   ███╗███████╗
  ██║   ██║██╔════╝██╔════╝██╔══██╗████╗  ██║██╔══██╗████╗ ████║██╔════╝
  ██║   ██║███████╗█████╗  ██████╔╝██╔██╗ ██║███████║██╔████╔██║█████╗  
  ██║   ██║╚════██║██╔══╝  ██╔══██╗██║╚██╗██║██╔══██║██║╚██╔╝██║██╔══╝  
  ╚██████╔╝███████║███████╗██║  ██║██║ ╚████║██║  ██║██║ ╚═╝ ██║███████╗
   ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝
                     [ S E A R C H   M O D U L E ]"""

def build_layout():
    #Header 
    header = [
        [sg.Text(BANNER, font=("Courier New", 7, "bold"),
                 text_color=ACCENT2, background_color=BG, pad=((0,0),(8,2)))],
        [sg.Text("▓░▒█▓░▒█▓░▒█▓░▒█▓░▒█▓░▒█▓░▒█▓░▒█▓░▒█▓░▒█▓░▒█▓░▒█▓░▒█▓░▒█▓░▒",
                 font=("Courier New", 7), text_color=ACCENT1, background_color=BG)],
    ]

    #Input row 
    input_row = sg.Frame("  ◈ TARGET INPUT ", [
        [
            sg.Text("USERNAME :", font=FONT_LABEL, text_color=ACCENT3,
                    background_color=PANEL),
            sg.Input("", key="-USERNAME-", font=FONT_MONO_L, size=(28, 1),
                     background_color=BG2, text_color=TEXT_BRIGHT,
                     border_width=1, pad=((6, 10), 6)),
            sg.Button("▶  SCAN", key="-SCAN-BTN-", font=FONT_LABEL, size=(12, 1),
                      button_color=(TEXT_BRIGHT, ACCENT1), border_width=0, pad=(4, 4)),
            sg.Button("■  STOP", key="-STOP-BTN-", font=FONT_LABEL, size=(10, 1),
                      button_color=(DANGER, BG2), border_width=1, pad=(4, 4),
                      disabled=True),
        ],
        [
            sg.Text("data.json :", font=FONT_MONO_S, text_color=TEXT_DIM,
                    background_color=PANEL),
            sg.Input("resources/data.json", key="-DATA-PATH-", font=FONT_MONO_S,
                     size=(30, 1), background_color=BG2, text_color=TEXT_DIM,
                     border_width=1, pad=((4, 6), 4)),
            sg.FileBrowse("…", font=FONT_MONO_S,
                          button_color=(TEXT_DIM, BORDER),
                          file_types=(("JSON", "*.json"),), pad=(2, 4)),
            sg.Text("wmn.json :", font=FONT_MONO_S, text_color=TEXT_DIM,
                    background_color=PANEL, pad=((12, 4), 4)),
            sg.Input("resources/wmn.json", key="-WMN-PATH-", font=FONT_MONO_S,
                     size=(28, 1), background_color=BG2, text_color=TEXT_DIM,
                     border_width=1, pad=((4, 6), 4)),
            sg.FileBrowse("…", font=FONT_MONO_S,
                          button_color=(TEXT_DIM, BORDER),
                          file_types=(("JSON", "*.json"),), pad=(2, 4)),
        ],
    ], font=FONT_LABEL, title_color=ACCENT2, background_color=PANEL,
       border_width=1, relief=sg.RELIEF_FLAT, expand_x=True, pad=(0, 4))

    #Static site list(left panel)
    site_rows = []
    for name, tpl in STATIC_SITES:
        site_rows.append([
            sg.Text("◈", font=FONT_MONO_S, text_color=ACCENT2,
                    background_color=PANEL, size=(2, 1), pad=(2, 1)),
            sg.Text(name, font=FONT_MONO_S, text_color=TEXT,
                    background_color=PANEL, size=(13, 1), pad=(0, 1)),
        ])

    sites_col = sg.Frame("  ◈ PLATFORMS ", [
        [sg.Column(site_rows, background_color=PANEL,
                   scrollable=True, vertical_scroll_only=True,
                   size=(180, 400), pad=(0, 0))],
    ], font=FONT_LABEL, title_color=ACCENT2, background_color=PANEL,
       border_width=1, relief=sg.RELIEF_FLAT, pad=(0, 4))

    #Console (right panel)
    console_col = sg.Frame("  ◈ RECON OUTPUT ", [
        [sg.Multiline(
            default_text=(
                f"[{time.strftime('%H:%M:%S')}] USERNAME SEARCH MODULE — ready\n"
                f"[{time.strftime('%H:%M:%S')}] Enter target username and press SCAN\n"
            ),
            key="-LOG-",
            font=("Courier New", 8),
            text_color=TEXT,
            background_color="#04040d",
            size=(80, 26),
            expand_x=True,
            expand_y=True,
            autoscroll=True,
            disabled=True,
            pad=(4, 4),
        )],
        [
            sg.ProgressBar(100, orientation='h', size=(50, 12),
                           key="-PROGRESS-", expand_x=True,
                           bar_color=(ACCENT1, BORDER), pad=((4, 4), (2, 0))),
            sg.Text("0%", key="-PCT-", font=FONT_MONO_S,
                    text_color=ACCENT3, background_color=PANEL,
                    size=(5, 1), pad=(4, 0)),
        ],
        [
            sg.Button("CLR", key="-CLEAR-", font=FONT_MONO_S, size=(6, 1),
                      button_color=(TEXT_DIM, BORDER), border_width=0, pad=(4, 4)),
            sg.Button("OPEN LOGS", key="-OPEN-LOGS-", font=FONT_MONO_S, size=(10, 1),
                      button_color=(ACCENT3, BORDER), border_width=1, pad=(4, 4)),
            sg.Push(background_color=PANEL),
            sg.Text("STATUS:", font=FONT_MONO_S, text_color=TEXT_DIM,
                    background_color=PANEL),
            sg.Text("IDLE", key="-STATUS-", font=FONT_MONO_S,
                    text_color=SUCCESS, background_color=PANEL, size=(16, 1)),
        ],
    ], font=FONT_LABEL, title_color=ACCENT2, background_color=PANEL,
       border_width=1, relief=sg.RELIEF_FLAT,
       expand_x=True, expand_y=True, pad=(0, 4))

    #Status bar 
    statusbar = [
        sg.Text("◈ MONOLYTH", text_color=ACCENT2, background_color=BG,
                font=FONT_MONO_S),
        sg.Text("USERNAME MODULE v1.0", text_color=TEXT_DIM,
                background_color=BG, font=FONT_MONO_S),
        sg.Push(background_color=BG),
        sg.Text(time.strftime("%Y-%m-%d  %H:%M"), text_color=TEXT_DIM,
                background_color=BG, font=FONT_MONO_S),
        sg.Text(" ◈ ", text_color=ACCENT2, background_color=BG, font=FONT_MONO_S),
        sg.Button("EXIT", key="-EXIT-", font=FONT_MONO_S, size=(6, 1),
                  button_color=(DANGER, BG2), border_width=1, pad=(2, 2)),
    ]

    layout = [
        *header,
        [input_row],
        [sites_col, console_col],
        [sg.HorizontalSeparator(color=ACCENT2, pad=(0, 2))],
        statusbar,
    ]
    return layout



#main
_scan_thread = None
_stop_flag   = threading.Event()

def main():
    window = sg.Window(
        "MONOLYTH :: USERNAME SEARCH",
        build_layout(),
        background_color=BG,
        size=(1200, 780),
        resizable=True,
        finalize=True,
    )

    global _scan_thread

    while True:
        event, values = window.read(timeout=200)

        if event in (sg.WIN_CLOSED, "-EXIT-"):
            break

        elif event == "-SCAN-BTN-":
            username = values["-USERNAME-"].strip()
            if not username:
                _log(window, "No username entered!", DANGER)
                continue
            data_p = values["-DATA-PATH-"].strip() or None
            wmn_p  = values["-WMN-PATH-"].strip() or None
            _stop_flag.clear()
            window["-SCAN-BTN-"].update(disabled=True)
            window["-STOP-BTN-"].update(disabled=False)
            window["-PCT-"].update("0%")
            window["-PROGRESS-"].update(0)
            _log(window, "═" * 54, ACCENT2)
            _log(window, f"INITIATING SCAN  >>>  {username}", ACCENT3)
            _scan_thread = threading.Thread(
                target=run_scan,
                args=(username, window, data_p, wmn_p),
                daemon=True,
            )
            _scan_thread.start()

        elif event == "-STOP-BTN-":
            _stop_flag.set()
            _log(window, "STOP signal sent — waiting for threads...", WARN)
            window["-STATUS-"].update("STOPPING", text_color=DANGER)
            window["-STOP-BTN-"].update(disabled=True)

        elif event == "-CLEAR-":
            window["-LOG-"].update(value="")
            window["-PCT-"].update("0%")
            window["-PROGRESS-"].update(0)

        elif event == "-OPEN-LOGS-":
            folder_path.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(str(folder_path))
            elif sys.platform == "darwin":
                os.system(f"open {folder_path}")
            else:
                os.system(f"xdg-open {folder_path}")

    window.close()


if __name__ == "__main__":
    main()