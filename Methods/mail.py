import FreeSimpleGUI as sg
import threading
import time
import os
import sys
import webbrowser
import requests
from pathlib import Path

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

folder_path = Path("Logs")

#список сортов
LOOKUP_SITES = [
    ("IntelX",        "https://intelx.io/?s={e}"),
    ("MailMeteor",    "https://mailmeteor.com/tools/reverse-email-lookup?email={e}"),
    ("GHunt",         "https://gmail-osint.activetk.jp/{prefix}"),   # special
]

DORK_TEMPLATES = [
    ("General",       "https://www.google.com/search?q={e}"),
    ("Profile",       "https://www.google.com/search?q={e} profile"),
    ("Registered",    "https://www.google.com/search?q={e} registered"),
    ("Signup",        "https://www.google.com/search?q={e} signup"),
    ("Account",       "https://www.google.com/search?q={e} account"),
    ("Facebook",      "https://www.google.com/search?q={e} site:facebook.com"),
    ("Instagram",     "https://www.google.com/search?q={e} site:instagram.com"),
    ("VKontakte",     "https://www.google.com/search?q={e} site:vk.com"),
    ("LinkedIn",      "https://www.google.com/search?q={e} site:linkedin.com"),
    ("Twitter/X",     "https://www.google.com/search?q={e} site:twitter.com"),
    ("Telegram",      "https://www.google.com/search?q={e} site:t.me"),
    ("Password",      "https://www.google.com/search?q={e} password"),
    ("Hash",          "https://www.google.com/search?q={e} hash"),
    ("Leaked",        "https://www.google.com/search?q={e} leaked"),
    ("Dump",          "https://www.google.com/search?q={e} dump"),
    ("Database",      "https://www.google.com/search?q={e} database"),
    ("TXT files",     "https://www.google.com/search?q={e} filetype:txt"),
    ("CSV files",     "https://www.google.com/search?q={e} filetype:csv"),
    ("SQL files",     "https://www.google.com/search?q={e} filetype:sql"),
    ("JSON files",    "https://www.google.com/search?q={e} filetype:json"),
    ("PDF files",     "https://www.google.com/search?q={e} filetype:pdf"),
    ("Pastebin",      "https://www.google.com/search?q={e} site:pastebin.com"),
    ("Ghostbin",      "https://www.google.com/search?q={e} site:ghostbin.com"),
    ("ControlC",      "https://www.google.com/search?q={e} site:controlc.com"),
    ("JustPaste",     "https://www.google.com/search?q={e} site:justpaste.it"),
]


#scan logic
def run_scan(email, window):
    _log(window, f"TARGET  >>>  {email}", ACCENT3)
    _log(window, "─" * 58, BORDER)

    #basic validation
    if "@" not in email or "." not in email.split("@")[-1]:
        _log(window, "Invalid email format!", DANGER)
        window["-STATUS-"].update("INVALID EMAIL", text_color=DANGER)
        window["-SCAN-BTN-"].update(disabled=False)
        return

    domain = email.split("@")[-1].lower()
    prefix = email.split("@")[0]

    window["-INFO-EMAIL-"].update(email)
    window["-INFO-DOMAIN-"].update(domain)
    window["-INFO-PREFIX-"].update(prefix)

    _log(window, f"Domain  : {domain}", TEXT)
    _log(window, f"Prefix  : {prefix}", TEXT)

    #GHunt(gmail only)
    _log(window, "─" * 58, BORDER)
    if "gmail" in domain:
        _log(window, "Gmail detected — running GHunt lookup...", ACCENT2)
        try:
            ghunt_url = f"https://gmail-osint.activetk.jp/{prefix}"
            r = requests.get(ghunt_url, timeout=10)
            window["-INFO-GHUNT-"].update(r.url, text_color=SUCCESS)
            _log(window, f"GHunt URL : {r.url}", SUCCESS)
        except Exception as e:
            _log(window, f"GHunt error: {e}", DANGER)
            window["-INFO-GHUNT-"].update("error", text_color=DANGER)
    else:
        _log(window, f"Non-Gmail domain ({domain}) — GHunt skipped", TEXT_DIM)
        window["-INFO-GHUNT-"].update("N/A — not Gmail", text_color=TEXT_DIM)

    #dork links
    _log(window, "─" * 58, BORDER)
    _log(window, f"Building {len(DORK_TEMPLATES)} dork links...", ACCENT2)
    for name, tpl in DORK_TEMPLATES:
        url = tpl.replace("{e}", email)
        _log(window, f"  ◈  {name:<14} {url}", TEXT_DIM)

    #save log
    folder_path.mkdir(parents=True, exist_ok=True)
    safe = email.replace("@", "_at_").replace(".", "_")
    log_file = folder_path / f"mail_{safe}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"MONOLYTH MAIL RECON — {email}\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("=== LOOKUP SITES ===\n")
            for name, tpl in LOOKUP_SITES:
                url = tpl.replace("{e}", email).replace("{prefix}", prefix)
                f.write(f"[{name}] {url}\n")
            f.write("\n=== DORK LINKS ===\n")
            for name, tpl in DORK_TEMPLATES:
                f.write(f"[{name}] {tpl.replace('{e}', email)}\n")
        _log(window, f"Report saved: {log_file}", TEXT_DIM)
    except Exception as e:
        _log(window, f"Save error: {e}", DANGER)

    _log(window, "─" * 58, BORDER)
    _log(window, "SCAN COMPLETE", SUCCESS)
    window["-STATUS-"].update("IDLE", text_color=SUCCESS)
    window["-SCAN-BTN-"].update(disabled=False)


def _log(window, msg, color=None):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] {msg}", text_color=color or TEXT, end="\n")


# ══════════════════════════════════════════════
#   LAYOUT
# ══════════════════════════════════════════════
BANNER = """\
  ███╗   ███╗ █████╗ ██╗██╗      ███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗
  ████╗ ████║██╔══██╗██║██║      ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║
  ██╔████╔██║███████║██║██║      ███████╗█████╗  ███████║██████╔╝██║     ███████║
  ██║╚██╔╝██║██╔══██║██║██║      ╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║
  ██║ ╚═╝ ██║██║  ██║██║███████╗ ███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║
  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
                           [ E M A I L   O S I N T ]"""


def irow(label, key, val="—", col=None):
    return [
        sg.Text(f"{label:<12}", font=FONT_MONO_S, text_color=TEXT_DIM,
                background_color=PANEL, size=(12, 1)),
        sg.Text(":", font=FONT_MONO_S, text_color=BORDER, background_color=PANEL),
        sg.Text(val, key=key, font=FONT_MONO_S,
                text_color=col or TEXT, background_color=PANEL,
                size=(32, 1), expand_x=True),
    ]


def build_layout():
    #Header
    header = [
        [sg.Text(BANNER, font=("Courier New", 7, "bold"),
                 text_color=ACCENT2, background_color=BG, pad=((0, 0), (8, 2)))],
        [sg.Text("▓░▒█" * 22,
                 font=("Courier New", 7), text_color=ACCENT1,
                 background_color=BG, pad=((0, 0), (0, 4)))],
    ]

    #Input panel
    input_panel = sg.Frame("  ◈ TARGET ", [
        [
            sg.Text("EMAIL :", font=FONT_LABEL, text_color=ACCENT3,
                    background_color=PANEL, pad=((8, 4), 8)),
            sg.Input("", key="-EMAIL-", font=FONT_MONO_L, size=(30, 1),
                     background_color=BG2, text_color=TEXT_BRIGHT,
                     border_width=1, pad=((4, 8), 8),
                     tooltip="e.g. target@gmail.com"),
            sg.Text("e.g. target@gmail.com", font=FONT_MONO_S,
                    text_color=TEXT_DIM, background_color=PANEL,
                    pad=((0, 12), 8)),
            sg.Button("▶  SCAN", key="-SCAN-BTN-", font=FONT_LABEL,
                      size=(12, 1), button_color=(TEXT_BRIGHT, ACCENT1),
                      border_width=0, pad=(4, 6)),
            sg.Button("CLR", key="-CLR-BTN-", font=FONT_MONO_S,
                      size=(5, 1), button_color=(TEXT_DIM, BORDER),
                      border_width=1, pad=(4, 6)),
        ],
    ], font=FONT_LABEL, title_color=ACCENT2, background_color=PANEL,
       border_width=1, relief=sg.RELIEF_FLAT, expand_x=True, pad=(0, 4))

    #Left panel:info+links
    _lookup_btns = [
        [
            sg.Text(f"  ◈  {name}", font=FONT_MONO_S, text_color=ACCENT3,
                    background_color=PANEL, size=(14, 1), pad=(2, 3)),
            sg.Button("↗ OPEN", key=f"-LOOKUP-{name}-", font=FONT_MONO_S,
                      size=(8, 1), button_color=(ACCENT3, PANEL),
                      border_width=1, pad=(2, 3)),
        ]
        for name, _ in LOOKUP_SITES
    ]

 #   _dork_btns = [
 #       [
  #          sg.Text(f"  ◈  {name}", font=FONT_MONO_S, text_color=TEXT,
 #                   background_color=PANEL, size=(14, 1), pad=(2, 2)),
 #           sg.Button("↗", key=f"-DORK-{name}-", font=FONT_MONO_S,
 #                     size=(3, 1), button_color=(TEXT_DIM, BORDER),
  #                    border_width=1, pad=(2, 2)),
  #      ]
 #       for name, _ in DORK_TEMPLATES
  #  ]

    _inner = [
        irow("Email",   "-INFO-EMAIL-",  "—"),
        irow("Domain",  "-INFO-DOMAIN-", "—"),
        irow("Prefix",  "-INFO-PREFIX-", "—"),
        irow("GHunt",   "-INFO-GHUNT-",  "—"),
        [sg.HorizontalSeparator(color=BORDER, pad=(4, 6))],
        [sg.Text("LOOKUP SITES", font=FONT_LABEL,
                 text_color=ACCENT2, background_color=PANEL, pad=((6, 0), (2, 4)))],
        *_lookup_btns,
        [sg.HorizontalSeparator(color=BORDER, pad=(4, 6))],
        [sg.Text("DORK LINKS", font=FONT_LABEL,
                 text_color=ACCENT2, background_color=PANEL, pad=((6, 0), (2, 4)))]
  #      *_dork_btns,
    ]

    left_panel = sg.Frame("  ◈ EMAIL INFO ", [
        [sg.Column(_inner, background_color=PANEL,
                   scrollable=True, vertical_scroll_only=True,
                   size=(270, 460), pad=(0, 0))],
    ], font=FONT_LABEL, title_color=ACCENT2, background_color=PANEL,
       border_width=1, relief=sg.RELIEF_FLAT, pad=(0, 4))

    #Console(right)
    console = sg.Frame("  ◈ RECON OUTPUT ", [
        [sg.Multiline(
            default_text=(
                f"[{time.strftime('%H:%M:%S')}] MAIL SEARCH MODULE — ready\n"
                f"[{time.strftime('%H:%M:%S')}] Enter target email and press SCAN\n"
            ),
            key="-LOG-",
            font=("Courier New", 8),
            text_color=TEXT,
            background_color="#04040d",
            size=(70, 32),
            expand_x=True,
            expand_y=True,
            autoscroll=True,
            disabled=True,
            pad=(4, 4),
        )],
        [
            sg.Button("CLEAR LOG", key="-CLEAR-", font=FONT_MONO_S, size=(10, 1),
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
        sg.Text("MAIL MODULE v1.0", text_color=TEXT_DIM,
                background_color=BG, font=FONT_MONO_S),
        sg.Push(background_color=BG),
        sg.Text(time.strftime("%Y-%m-%d  %H:%M"), text_color=TEXT_DIM,
                background_color=BG, font=FONT_MONO_S),
        sg.Text(" ◈ ", text_color=ACCENT2, background_color=BG, font=FONT_MONO_S),
        sg.Button("EXIT", key="-EXIT-", font=FONT_MONO_S, size=(6, 1),
                  button_color=(DANGER, BG2), border_width=1, pad=(2, 2)),
    ]

    return [
        *header,
        [input_panel],
        [left_panel, console],
        [sg.HorizontalSeparator(color=ACCENT2, pad=(0, 2))],
        statusbar,
    ]


#main
def main():
    window = sg.Window(
        "MONOLYTH :: MAIL SEARCH",
        build_layout(),
        background_color=BG,
        size=(1200, 780),
        resizable=True,
        finalize=True,
    )

    current_email = [""]

    while True:
        event, values = window.read(timeout=300)

        if event in (sg.WIN_CLOSED, "-EXIT-"):
            break

        elif event == "-SCAN-BTN-":
            email = values["-EMAIL-"].strip()
            if not email:
                _log(window, "No email entered!", DANGER)
                continue
            current_email[0] = email
            for key in ("-INFO-EMAIL-", "-INFO-DOMAIN-", "-INFO-PREFIX-", "-INFO-GHUNT-"):
                window[key].update("...")
            window["-STATUS-"].update("SCANNING...", text_color=WARN)
            window["-SCAN-BTN-"].update(disabled=True)
            _log(window, "═" * 58, ACCENT2)
            threading.Thread(
                target=run_scan, args=(email, window), daemon=True
            ).start()

        elif event == "-CLR-BTN-":
            window["-EMAIL-"].update("")

        elif event == "-CLEAR-":
            window["-LOG-"].update(value="")

        elif event == "-OPEN-LOGS-":
            folder_path.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(str(folder_path))
            elif sys.platform == "darwin":
                os.system(f"open {folder_path}")
            else:
                os.system(f"xdg-open {folder_path}")

        # ── lookup buttons ──
        elif event.startswith("-LOOKUP-") and event.endswith("-"):
            email = current_email[0] or values["-EMAIL-"].strip()
            if not email:
                _log(window, "Enter an email first!", DANGER)
                continue
            name = event[8:-1]
            prefix = email.split("@")[0] if "@" in email else email
            for n, tpl in LOOKUP_SITES:
                if n == name:
                    url = tpl.replace("{e}", email).replace("{prefix}", prefix)
                    webbrowser.open(url)
                    _log(window, f"Opening {name}: {url}", ACCENT3)
                    break

        # ----------dork buttons--------
    #    elif event.startswith("-DORK-") and event.endswith("-"):
    #        email = current_email[0] or values["-EMAIL-"].strip()
    #        if not email:
    #            _log(window, "Enter an email first!", DANGER)
    #            continue
    #        name = event[6:-1]
            #for n, tpl in DORK_TEMPLATES:
            #    if n == name:
            #        url = tpl.format(e=email)   # ВАЖНО
            #        webbrowser.open(url)
            #        _log(window, f"Opening dork: {name}", TEXT_DIM)
            #        break

    window.close()


if __name__ == "__main__":
    main()