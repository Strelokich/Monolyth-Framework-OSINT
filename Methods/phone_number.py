import FreeSimpleGUI as sg
import threading
import time
import os
import sys
import webbrowser
from pathlib import Path

try:
    import phonenumbers
    import phonenumbers.carrier
    import phonenumbers.geocoder
    import phonenumbers.timezone
    HAS_PHONENUMBERS = True
except ImportError:
    HAS_PHONENUMBERS = False

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


#лист дорков
DORK_TEMPLATES = [
    ("Telegram",    "https://www.google.com/search?q={p} site:telegram.org"),
    ("Registered",  "https://www.google.com/search?q={p} registered"),
    ("Facebook",    "https://www.google.com/search?q={p} site:facebook.com"),
    ("Twitter/X",   "https://www.google.com/search?q={p} site:twitter.com"),
    ("VKontakte",   "https://www.google.com/search?q={p} site:vk.com"),
    ("Instagram",   "https://www.google.com/search?q={p} site:instagram.com"),
    ("Craigslist",  "https://www.google.com/search?q={p} site:craigslist.org"),
    ("LinkedIn",    "https://www.google.com/search?q={p} site:linkedin.com"),
    ("Reddit",      "https://www.google.com/search?q={p} site:reddit.com"),
    ("YouTube",     "https://www.google.com/search?q={p} site:youtube.com"),
    ("Avito",       "https://www.google.com/search?q={p} site:avito.ru"),
    ("Youla",       "https://www.google.com/search?q={p} site:youla.ru"),
    ("eBay",        "https://www.google.com/search?q={p} site:ebay.com"),
    ("Kufar",       "https://www.google.com/search?q={p} site:kufar.by"),
    ("ScamAdvisor", "https://www.google.com/search?q={p} site:scamadviser.com"),
    ("Intext",      "https://www.google.com/search?q=intext:{p}"),
    ("Intitle",     "https://www.google.com/search?q=intitle:{p}"),
    ("PDF files",   "https://www.google.com/search?q={p} filetype:pdf"),
    ("Sync.me",     "https://sync.me/search/?number={p}"),
    ("GoogleSearch","https://www.google.com/search?q={p}"),
    ("Truecaller",  "https://www.truecaller.com/search/ru/{p}"),
    ("Getcontact",  "https://getcontact.com/en/search/?phone={p}"),
]

MESSENGER_LINKS = [
    ("Telegram",  "https://t.me/{p}",          ACCENT3),
    ("WhatsApp",  "https://wa.me/{p}",          SUCCESS),
    ("Viber",     "https://viber.click/{p}",    "#cc44ff"),
]


#scan logic
def run_scan(phone, window):
    _log(window, f"TARGET  >>>  {phone}", ACCENT3)
    _log(window, "─" * 56, BORDER)

    #phonenumbers analysis
    if not HAS_PHONENUMBERS:
        _log(window, "phonenumbers not installed — skipping analysis", WARN)
    else:
        try:
            parsed = phonenumbers.parse(phone, None)
            valid  = phonenumbers.is_valid_number(parsed)
            carrier_info = phonenumbers.carrier.name_for_number(parsed, "en")
            country_en   = phonenumbers.geocoder.description_for_number(parsed, "en")
            region_ru    = phonenumbers.geocoder.description_for_number(parsed, "ru")
            formatted    = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            timezones    = phonenumbers.timezone.time_zones_for_number(parsed)

            window["-INFO-NUMBER-"].update(formatted)
            window["-INFO-COUNTRY-"].update(country_en or "—")
            window["-INFO-REGION-"].update(region_ru  or "—")
            window["-INFO-CARRIER-"].update(carrier_info or "—")
            window["-INFO-VALID-"].update(
                "✓  VALID" if valid else "✗  INVALID",
                text_color=SUCCESS if valid else DANGER)
            window["-INFO-TZ-"].update(", ".join(timezones) if timezones else "—")

            _log(window, f"Formatted : {formatted}", TEXT_BRIGHT)
            _log(window, f"Country   : {country_en}", TEXT)
            _log(window, f"Region    : {region_ru}", TEXT)
            _log(window, f"Carrier   : {carrier_info or 'unknown'}", TEXT)
            _log(window, f"Valid     : {'YES' if valid else 'NO'}",
                 SUCCESS if valid else DANGER)
            _log(window, f"Timezones : {', '.join(timezones) if timezones else '—'}", TEXT_DIM)

            # messenger links
            clean = phone.replace("+", "").replace(" ", "").replace("-", "")
            _log(window, "─" * 56, BORDER)
            _log(window, "Messenger links:", ACCENT3)
            for name, tpl, _ in MESSENGER_LINKS:
                _log(window, f"  {name:<12} {tpl.replace('{p}', clean)}", TEXT_DIM)

        except Exception as e:
            _log(window, f"phonenumbers error: {e}", DANGER)

    #dorks
    _log(window, "─" * 56, BORDER)
    _log(window, f"Generating {len(DORK_TEMPLATES)} dork links...", ACCENT2)
    dorks = [(name, tpl.replace("{p}", phone)) for name, tpl in DORK_TEMPLATES]
    for name, url in dorks:
        _log(window, f"  ◈  {name:<14} {url}", TEXT_DIM)

    #save log
    folder_path.mkdir(parents=True, exist_ok=True)
    log_file = folder_path / f"phone_{phone.replace('+','').replace(' ','')}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"MONOLYTH PHONE RECON — {phone}\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("=== DORK LINKS ===\n")
            for name, url in dorks:
                f.write(f"[{name}] {url}\n")
        _log(window, f"Report saved: {log_file}", TEXT_DIM)
    except Exception as e:
        _log(window, f"Save error: {e}", DANGER)

    _log(window, "─" * 56, BORDER)
    _log(window, "SCAN COMPLETE", SUCCESS)
    window["-STATUS-"].update("IDLE", text_color=SUCCESS)
    window["-SCAN-BTN-"].update(disabled=False)


def _log(window, msg, color=None):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] {msg}", text_color=color or TEXT, end="\n")



#layout
BANNER = """\
  ██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗███████╗
  ██╔══██╗██║  ██║██╔═══██╗████╗  ██║██╔════╝
  ██████╔╝███████║██║   ██║██╔██╗ ██║█████╗  
  ██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║██╔══╝  
  ██║     ██║  ██║╚██████╔╝██║ ╚████║███████╗
  ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
         [ N U M B E R   O S I N T ]"""


def info_row(label, key, value="—", val_color=TEXT):
    return [
        sg.Text(f"{label:<12}", font=FONT_MONO_S, text_color=TEXT_DIM,
                background_color=PANEL, size=(12, 1)),
        sg.Text(":", font=FONT_MONO_S, text_color=BORDER,
                background_color=PANEL),
        sg.Text(value, key=key, font=FONT_MONO_S,
                text_color=val_color, background_color=PANEL,
                size=(34, 1), expand_x=True),
    ]


def build_layout():
    #Header
    header = [
        [sg.Text(BANNER, font=("Courier New", 9, "bold"),
                 text_color=ACCENT2, background_color=BG, pad=((0, 0), (8, 2)))],
        [sg.Text("▓░▒█" * 18,
                 font=("Courier New", 7), text_color=ACCENT1,
                 background_color=BG, pad=((0, 0), (0, 4)))],
    ]

    #Input panel
    input_panel = sg.Frame("  ◈ TARGET ", [
        [
            sg.Text("PHONE NUMBER :", font=FONT_LABEL, text_color=ACCENT3,
                    background_color=PANEL, pad=((6, 4), 8)),
            sg.Input("", key="-PHONE-", font=FONT_MONO_L, size=(24, 1),
                     background_color=BG2, text_color=TEXT_BRIGHT,
                     border_width=1, pad=((4, 8), 8),
                     tooltip="Format: +7XXXXXXXXXX  or  +1XXXXXXXXXX"),
            sg.Text("e.g. +79001234567", font=FONT_MONO_S,
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

    #Info card(left)
    _inner = [
        info_row("Number",   "-INFO-NUMBER-",  "—"),
        info_row("Country",  "-INFO-COUNTRY-", "—"),
        info_row("Region",   "-INFO-REGION-",  "—"),
        info_row("Carrier",  "-INFO-CARRIER-", "—"),
        info_row("Valid",    "-INFO-VALID-",   "—"),
        info_row("Timezone", "-INFO-TZ-",      "—"),
        [sg.HorizontalSeparator(color=BORDER, pad=(4, 6))],
        [sg.Text("MESSENGER LINKS", font=FONT_LABEL,
                 text_color=ACCENT2, background_color=PANEL, pad=((6, 0), (0, 4)))],
        *[
            [
                sg.Text(f"  {name}", font=FONT_MONO_S, text_color=col,
                        background_color=PANEL, size=(12, 1)),
                sg.Button(f"↗ {name}", key=f"-OPEN-{name}-",
                          font=FONT_MONO_S, size=(10, 1),
                          button_color=(col, PANEL), border_width=1,
                          pad=(4, 3)),
            ]
            for name, _, col in MESSENGER_LINKS
        ],
        [sg.HorizontalSeparator(color=BORDER, pad=(4, 6))],
  #      [sg.Text("DORK LINKS", font=FONT_LABEL,
   #              text_color=ACCENT2, background_color=PANEL, pad=((6, 0), (0, 4)))],
   #     *[
   #         [
   #             sg.Text(f"  ◈  {name}", font=FONT_MONO_S, text_color=TEXT,
   #                     background_color=PANEL, size=(14, 1), pad=(2, 2)),
   #             sg.Button("↗", key=f"-DORK-{name}-", font=FONT_MONO_S,
   #                       size=(3, 1), button_color=(TEXT_DIM, BORDER),
   #                       border_width=1, pad=(2, 2)),
   #         ]
   #         for name, _ in DORK_TEMPLATES
   #     ],
    ]
    info_card = sg.Frame("  ◈ NUMBER INFO ", [
        [sg.Column(_inner, background_color=PANEL,
                   scrollable=True, vertical_scroll_only=True,
                   size=(270, 460), pad=(0, 0))],
    ], font=FONT_LABEL, title_color=ACCENT2, background_color=PANEL,
       border_width=1, relief=sg.RELIEF_FLAT, pad=(0, 4))

    #Console(right)
    console = sg.Frame("  ◈ RECON OUTPUT ", [
        [sg.Multiline(
            default_text=(
                f"[{time.strftime('%H:%M:%S')}] PHONE NUMBER MODULE — ready\n"
                f"[{time.strftime('%H:%M:%S')}] Enter phone in international format (+XXXXXXXXXXX)\n"
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
                    text_color=SUCCESS, background_color=PANEL, size=(14, 1)),
        ],
    ], font=FONT_LABEL, title_color=ACCENT2, background_color=PANEL,
       border_width=1, relief=sg.RELIEF_FLAT,
       expand_x=True, expand_y=True, pad=(0, 4))

    #Status bar
    statusbar = [
        sg.Text("◈ MONOLYTH", text_color=ACCENT2, background_color=BG,
                font=FONT_MONO_S),
        sg.Text("PHONE MODULE v1.0", text_color=TEXT_DIM,
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
        [input_panel],
        [info_card, console],
        [sg.HorizontalSeparator(color=ACCENT2, pad=(0, 2))],
        statusbar,
    ]
    return layout



#main
def main():
    window = sg.Window(
        "MONOLYTH :: PHONE NUMBER OSINT",
        build_layout(),
        background_color=BG,
        size=(1200, 780),
        resizable=True,
        finalize=True,
    )

    current_phone = [""]  # mutable container for thread access

    while True:
        event, values = window.read(timeout=300)

        if event in (sg.WIN_CLOSED, "-EXIT-"):
            break

        elif event == "-SCAN-BTN-":
            phone = values["-PHONE-"].strip()
            if not phone:
                _log(window, "No phone number entered!", DANGER)
                continue
            current_phone[0] = phone
            # reset info fields
            for key in ("-INFO-NUMBER-", "-INFO-COUNTRY-", "-INFO-REGION-",
                        "-INFO-CARRIER-", "-INFO-VALID-", "-INFO-TZ-"):
                window[key].update("...")
            window["-STATUS-"].update("SCANNING...", text_color=WARN)
            window["-SCAN-BTN-"].update(disabled=True)
            _log(window, "═" * 56, ACCENT2)
            threading.Thread(
                target=run_scan, args=(phone, window), daemon=True
            ).start()

        elif event == "-CLR-BTN-":
            window["-PHONE-"].update("")

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

        #messenger buttons
        elif event.startswith("-OPEN-") and event.endswith("-"):
            name = event[6:-1]
            phone = current_phone[0] or values["-PHONE-"].strip()
            if not phone:
                _log(window, "Enter a phone number first!", DANGER)
                continue
            clean = phone.replace("+", "").replace(" ", "").replace("-", "")
            for n, tpl, _ in MESSENGER_LINKS:
                if n == name:
                    webbrowser.open(tpl.replace("{p}", clean))
                    _log(window, f"Opening {name}: {tpl.replace('{p}', clean)}", ACCENT3)
                    break

        #dork buttons
      #  elif event.startswith("-DORK-") and event.endswith("-"):
      #      name = event[6:-1]
      #      phone = current_phone[0] or values["-PHONE-"].strip()
       #     if not phone:
       #         _log(window, "Enter a phone number first!", DANGER)
       #         continue
       #     for n, tpl in DORK_TEMPLATES:
       #         if n == name:
        #            url = tpl.replace("{p}", phone)
        #            webbrowser.open(url)
        #            _log(window, f"Opening dork: {name}", TEXT_DIM)
        #            break

    window.close()


if __name__ == "__main__":
    main()