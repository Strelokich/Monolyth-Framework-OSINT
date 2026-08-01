import FreeSimpleGUI as sg
import threading
import time
import os
import sys
import json
import random
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

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/119.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT
}


def load_user_agents(path):
    """Load one User-Agent per line from a local TXT file."""
    if not path:
        return [DEFAULT_USER_AGENT]

    try:
        ua_path = Path(path)
        if not ua_path.exists():
            return [DEFAULT_USER_AGENT]

        with ua_path.open("r", encoding="utf-8", errors="ignore") as f:
            agents = [
                line.strip()
                for line in f
                if line.strip() and not line.lstrip().startswith("#")
            ]

        return agents or [DEFAULT_USER_AGENT]
    except Exception:
        return [DEFAULT_USER_AGENT]


def random_headers(user_agents, extra_headers=None):
    """Build request headers with a random User-Agent for this request."""
    headers = dict(extra_headers or {})
    headers["User-Agent"] = random.choice(user_agents or [DEFAULT_USER_AGENT])
    return headers


def post_ui(window, action, **payload):
    """Thread-safe communication from workers to the GUI event loop."""
    try:
        window.write_event_value("-WORKER-EVENT-", (action, payload))
    except Exception:
        # Window may already be closed.
        pass



#   логика сканирования
def check_url(name, url, user_agents):
    if _stop_flag.is_set():
        return (name, url, None, "stopped")

    try:
        r = requests.get(
            url,
            headers=random_headers(user_agents),
            timeout=8,
            allow_redirects=True,
        )
        if r.status_code == 200:
            return (name, url, True, None)
        return (name, url, False, None)
    except Exception as e:
        return (name, url, None, str(e))


def run_scan(username, window, data_json_path=None, wmn_json_path=None,
             user_agents_path=None):
    found = []
    errors = 0
    checked = 0
    total = len(STATIC_SITES)
    user_agents = load_user_agents(user_agents_path)

    post_ui(window, "log", msg=f"TARGET  >>>  {username}", color=ACCENT3)
    post_ui(window, "log", msg=f"Platforms in static list: {total}", color=TEXT_DIM)
    post_ui(
        window,
        "log",
        msg=f"User-Agents loaded: {len(user_agents)}"
            + (f" from {user_agents_path}" if user_agents_path else " (fallback)"),
        color=TEXT_DIM,
    )
    post_ui(window, "log", msg="─" * 54, color=BORDER)
    post_ui(window, "progress_reset", total=total)
    post_ui(window, "status", text="SCANNING...", color=WARN)

    def check_static(item):
        name, tpl = item
        if _stop_flag.is_set():
            return None
        url = tpl.replace("{u}", username)
        return check_url(name, url, user_agents)

    executor = ThreadPoolExecutor(max_workers=THREADS)
    futures = [executor.submit(check_static, item) for item in STATIC_SITES]

    try:
        for future in as_completed(futures):
            if _stop_flag.is_set():
                break

            result = future.result()
            if result is None:
                continue

            name, url, state, error = result
            checked += 1
            pct = int(checked / total * 100)
            post_ui(window, "progress", value=checked, total=total, pct=pct)

            if state is True:
                found.append((name, url))
                post_ui(
                    window,
                    "raw_log",
                    msg=f"  ◈  FOUND   {name:<14} {url}",
                    color=SUCCESS,
                )
            elif state is None and error != "stopped":
                errors += 1
    finally:
        if _stop_flag.is_set():
            for future in futures:
                future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)

    if _stop_flag.is_set():
        post_ui(window, "log", msg="Scan stopped by user.", color=WARN)
        post_ui(window, "status", text="STOPPED", color=WARN)
        post_ui(window, "scan_finished")
        return

    post_ui(window, "log", msg="─" * 54, color=BORDER)
    post_ui(
        window,
        "log",
        msg=f"Scan complete. Found: {len(found)}  |  Errors: {errors}",
        color=ACCENT3,
    )

    # optional: DataJson scan
    if data_json_path and os.path.exists(data_json_path) and not _stop_flag.is_set():
        post_ui(
            window,
            "log",
            msg=f"Loading data.json: {data_json_path}",
            color=TEXT_DIM,
        )
        try:
            with open(data_json_path, "r", encoding="utf-8") as f:
                targets = json.load(f)
                targets.pop("$schema", None)

            post_ui(
                window,
                "log",
                msg=f"data.json sites: {len(targets)}",
                color=TEXT_DIM,
            )

            dj_found = 0

            def check_dj(item):
                if _stop_flag.is_set():
                    return None

                site_name, site_data = item
                url = site_data["url"].format(username)
                error_type = site_data.get("errorType")

                # Preserve site-specific headers, but choose a fresh UA per request.
                headers = random_headers(
                    user_agents,
                    extra_headers=site_data.get("headers", {}),
                )

                try:
                    r = requests.get(
                        url,
                        headers=headers,
                        timeout=8,
                        allow_redirects=True,
                    )
                except Exception:
                    return None

                is_found = False
                if error_type == "status_code":
                    is_found = r.status_code == 200
                elif error_type == "message":
                    msgs = site_data.get("errorMsg", [])
                    if isinstance(msgs, str):
                        msgs = [msgs]
                    is_found = not any(m in r.text for m in msgs)
                elif error_type == "response_url":
                    is_found = r.url != site_data.get("errorUrl")

                if is_found:
                    return (site_name, url)
                return None

            dj_executor = ThreadPoolExecutor(max_workers=THREADS)
            dj_futures = [
                dj_executor.submit(check_dj, item)
                for item in targets.items()
            ]

            try:
                for future in as_completed(dj_futures):
                    if _stop_flag.is_set():
                        break

                    result = future.result()
                    if result:
                        dj_found += 1
                        site_name, url = result
                        post_ui(
                            window,
                            "raw_log",
                            msg=f"  ◈  [DJ]    {site_name:<14} {url}",
                            color=ACCENT3,
                        )
            finally:
                if _stop_flag.is_set():
                    for future in dj_futures:
                        future.cancel()
                dj_executor.shutdown(wait=False, cancel_futures=True)

            if not _stop_flag.is_set():
                post_ui(
                    window,
                    "log",
                    msg=f"data.json: {dj_found} accounts found",
                    color=ACCENT3,
                )

        except Exception as e:
            post_ui(window, "log", msg=f"data.json error: {e}", color=DANGER)

    if _stop_flag.is_set():
        post_ui(window, "log", msg="Scan stopped by user.", color=WARN)
        post_ui(window, "status", text="STOPPED", color=WARN)
        post_ui(window, "scan_finished")
        return

    # save logs
    folder_path.mkdir(parents=True, exist_ok=True)
    safe_username = "".join(
        ch for ch in username if ch.isalnum() or ch in ("-", "_", ".")
    ) or "unknown"
    log_file = (
        folder_path
        / f"username_{safe_username}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    )

    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"MONOLYTH USERNAME RECON — {username}\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            if found:
                for name, url in found:
                    f.write(f"[FOUND] {name}: {url}\n")
            else:
                f.write("No accounts found in static list.\n")

        post_ui(
            window,
            "log",
            msg=f"Report saved: {log_file}",
            color=TEXT_DIM,
        )
    except Exception as e:
        post_ui(window, "log", msg=f"Save error: {e}", color=DANGER)

    post_ui(window, "status", text="IDLE", color=SUCCESS)
    post_ui(window, "scan_finished")


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
        [
            sg.Text("useragents :", font=FONT_MONO_S, text_color=TEXT_DIM,
                    background_color=PANEL),
            sg.Input("resources/useragents.txt", key="-UA-PATH-", font=FONT_MONO_S,
                     size=(30, 1), background_color=BG2, text_color=TEXT_DIM,
                     border_width=1, pad=((4, 6), 4)),
            sg.FileBrowse("…", font=FONT_MONO_S,
                          button_color=(TEXT_DIM, BORDER),
                          file_types=(("Text", "*.txt"), ("All", "*.*")),
                          pad=(2, 4)),
            sg.Text("one User-Agent per line", font=FONT_MONO_S,
                    text_color=TEXT_DIM, background_color=PANEL,
                    pad=((12, 4), 4)),
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

        if event == "-WORKER-EVENT-":
            action, payload = values["-WORKER-EVENT-"]

            if action == "log":
                _log(window, payload["msg"], payload.get("color"))

            elif action == "raw_log":
                window["-LOG-"].print(
                    payload["msg"],
                    text_color=payload.get("color") or TEXT,
                    end="\n",
                )

            elif action == "progress_reset":
                total = payload["total"]
                window["-PROGRESS-"].update(0, max=total)
                window["-PCT-"].update("0%")

            elif action == "progress":
                window["-PROGRESS-"].update(
                    payload["value"],
                    max=payload["total"],
                )
                window["-PCT-"].update(f'{payload["pct"]}%')

            elif action == "status":
                window["-STATUS-"].update(
                    payload["text"],
                    text_color=payload["color"],
                )

            elif action == "scan_finished":
                window["-SCAN-BTN-"].update(disabled=False)
                window["-STOP-BTN-"].update(disabled=True)

            continue

        elif event == "-SCAN-BTN-":
            username = values["-USERNAME-"].strip()
            if not username:
                _log(window, "No username entered!", DANGER)
                continue
            data_p = values["-DATA-PATH-"].strip() or None
            wmn_p  = values["-WMN-PATH-"].strip() or None
            ua_p   = values["-UA-PATH-"].strip() or None
            _stop_flag.clear()
            window["-SCAN-BTN-"].update(disabled=True)
            window["-STOP-BTN-"].update(disabled=False)
            window["-PCT-"].update("0%")
            window["-PROGRESS-"].update(0)
            _log(window, "═" * 54, ACCENT2)
            _log(window, f"INITIATING SCAN  >>>  {username}", ACCENT3)
            _scan_thread = threading.Thread(
                target=run_scan,
                args=(username, window, data_p, wmn_p, ua_p),
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