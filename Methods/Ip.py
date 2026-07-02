import os
import time
import threading
import webbrowser
from pathlib import Path

import requests
import FreeSimpleGUI as sg


#палетка
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
FONT_LABEL  = ("Courier New", 9, "bold")

BANNER = """
  ██╗██████╗      ██╗     ██████╗  ██████╗ ███╗   ███╗ █████╗ ██╗███╗   ██╗
  ██║██╔══██╗    ██╔╝     ██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██║████╗  ██║
  ██║██████╔╝   ██╔╝      ██║  ██║██║   ██║██╔████╔██║███████║██║██╔██╗ ██║
  ██║██╔═══╝   ██╔╝       ██║  ██║██║   ██║██║╚██╔╝██║██╔══██║██║██║╚██╗██║
  ██║██║      ██╔╝        ██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║██║██║ ╚████║
  ╚═╝╚═╝      ╚═╝         ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
                 [ D O M A I N  /  I P   R E C O N   M O D U L E ]
"""

#log
def log(window, msg):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] {msg}", text_color=TEXT, end="\n")

def log_ok(window, msg):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] ✓ {msg}", text_color=SUCCESS, end="\n")

def log_err(window, msg):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] ✗ {msg}", text_color=DANGER, end="\n")

def log_warn(window, msg):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] ▸ {msg}", text_color=WARN, end="\n")

def log_result(window, msg):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}]   {msg}", text_color=ACCENT3, end="\n")

def set_status(window, text, color=SUCCESS):
    window["-STATUS-"].update(value=text, text_color=color)

def save_logs(lines, filename):
    folder_path = Path("Logs")
    folder_path.mkdir(parents=True, exist_ok=True)
    full_path = folder_path / filename
    with open(full_path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    return full_path



#Core
def run_ip(ip, window):
    set_status(window, "RUNNING IP…", WARN)
    log(window, "─" * 55)
    log(window, f"Target IP: {ip}")

    #ipinfo.io live geo data
    log_warn(window, "Fetching ipinfo.io …")
    try:
        r = requests.get(f"https://ipinfo.io/{ip}/json", timeout=8)
        if r.status_code == 200:
            data = r.json()
            for key in ("ip", "hostname", "city", "region", "country",
                        "org", "timezone", "loc"):
                if key in data:
                    log_result(window, f"{key:12}: {data[key]}")
        else:
            log_err(window, f"ipinfo.io returned {r.status_code}")
    except Exception as e:
        log_err(window, f"ipinfo.io: {e}")

    #list of list
    dork_links = [
        f"https://ipinfo.io/{ip}",
        f"https://www.abuseipdb.com/check/{ip}",
        f"https://www.shodan.io/host/{ip}",
        f"https://search.censys.io/hosts/{ip}",
        f"https://bgp.he.net/ip/{ip}",
        f"https://www.google.com/search?q={ip}",
        f"https://www.google.com/search?q={ip}+index+of",
        f"https://www.google.com/search?q={ip}+login",
        f"https://www.google.com/search?q={ip}+admin",
        f"https://www.google.com/search?q={ip}+password",
        f"https://www.google.com/search?q={ip}+phpmyadmin",
        f"https://www.google.com/search?q={ip}+ftp",
        f"https://www.google.com/search?q={ip}+rdp",
        f"https://www.google.com/search?q={ip}+api",
        f"https://www.google.com/search?q={ip}+leak",
        f"https://www.google.com/search?q={ip}+database",
        f"https://www.google.com/search?q={ip}+dump",
        f"https://www.google.com/search?q={ip}+error",
        f"https://www.google.com/search?q={ip}+log",
        f"https://www.google.com/search?q={ip}+debug",
        f'https://www.google.com/search?q="{ip}"+filetype:txt',
        f'https://www.google.com/search?q="{ip}"+filetype:log',
        f'https://www.google.com/search?q="{ip}"+filetype:sql',
        f'https://www.google.com/search?q="{ip}"+filetype:conf',
    ]

    log(window, "─" * 55)
    log_warn(window, f"Generated {len(dork_links)} dork/recon links:")
    for link in dork_links:
        log_result(window, link)

    full_path = save_logs(dork_links, "ip_logs.txt")
    log(window, "─" * 55)
    log_ok(window, f"Links saved → {full_path}")
    set_status(window, "IP DONE", SUCCESS)



#core logic main
def run_domain(domain, window):
    set_status(window, "RUNNING DOMAIN…", WARN)
    log(window, "─" * 55)
    log(window, f"Target domain: {domain}")

    #crt.sh subdomain enumeration
    log_warn(window, "Querying crt.sh for subdomains …")
    subdomains = []
    try:
        r = requests.get(
            f"https://crt.sh/?q=%.{domain}&output=json", timeout=15
        )
        if r.status_code == 200:
            for entry in r.json():
                name = entry.get("name_value", "")
                for sub in name.splitlines():
                    sub = sub.strip()
                    if sub and sub not in subdomains:
                        subdomains.append(sub)
            log_ok(window, f"crt.sh: {len(subdomains)} subdomain(s) found")
            for sub in subdomains[:40]:          # cap display at 40
                log_result(window, f"  {sub}")
            if len(subdomains) > 40:
                log_warn(window, f"  … {len(subdomains) - 40} more (see log file)")
        else:
            log_err(window, f"crt.sh returned {r.status_code}")
    except Exception as e:
        log_err(window, f"crt.sh: {e}")

    #Recon/WHOIS links
    recon_links = [
        f"https://whois.domaintools.com/{domain}",
        f"https://www.virustotal.com/gui/domain/{domain}",
        f"https://www.shodan.io/search?query={domain}",
        f"https://search.censys.io/search?resource=hosts&q={domain}",
        f"https://dnsdumpster.com",
        f"https://www.google.com/search?q=site:{domain}",
        f"https://www.google.com/search?q={domain}+admin",
        f"https://www.google.com/search?q={domain}+login",
        f"https://www.google.com/search?q={domain}+leak",
        f'https://www.google.com/search?q=site:{domain}+filetype:pdf',
        f'https://www.google.com/search?q=site:{domain}+filetype:sql',
        f'https://www.google.com/search?q=site:{domain}+filetype:log',
    ]

    log(window, "─" * 55)
    log_warn(window, f"Generated {len(recon_links)} recon links:")
    for link in recon_links:
        log_result(window, link)

    all_lines = [f"# SUBDOMAINS ({domain})"] + subdomains + \
                ["\n# RECON LINKS"] + recon_links
    full_path = save_logs(all_lines, "domain_logs.txt")
    log(window, "─" * 55)
    log_ok(window, f"Results saved → {full_path}")
    set_status(window, "DOMAIN DONE", SUCCESS)



#layout
def glitch_sep(width=70):
    chars = "▓░▒█▓░▒"
    return "".join(chars[i % len(chars)] for i in range(width))

def _sep(color=BORDER, pad=(0, 4)):
    return sg.HorizontalSeparator(color=color, pad=pad)

def build_layout():
    #Header
    header = sg.Column([
        [sg.Text(BANNER, font=("Courier New", 7, "bold"),
                 text_color=ACCENT1, background_color=BG, pad=((0,0),(8,0)))],
        [sg.Text(glitch_sep(90), font=("Courier New", 7),
                 text_color=ACCENT2, background_color=BG)],
        [sg.Text(" MONOLYTH OSINT v2.0  |  Module 02 — DOMAIN / IP CHECK",
                 font=FONT_MONO_S, text_color=TEXT_DIM, background_color=BG)],
        [_sep(ACCENT2, (0, 4))],
    ], background_color=BG, expand_x=True)

    #Ip panel
    ip_panel = sg.Frame("  ◈ IP LOOKUP + DORK LINKS ", [
        [
            sg.Text("TARGET IP :", font=FONT_LABEL, text_color=ACCENT3,
                    background_color=PANEL, size=(12, 1)),
            sg.Input(key="-IP-", font=FONT_MONO, size=(30, 1),
                     background_color=BG2, text_color=TEXT_BRIGHT,
                     border_width=1),
            sg.Button("▶  RUN IP", key="-RUN_IP-", font=FONT_MONO,
                      size=(12, 1), button_color=(TEXT_BRIGHT, ACCENT1),
                      border_width=0, pad=(8, 4)),
        ],
        [
            sg.Text("", background_color=PANEL, size=(12, 1)),
            sg.Text("Geo-lookup via ipinfo.io + generates 24 dork/recon links",
                    font=FONT_MONO_S, text_color=TEXT_DIM,
                    background_color=PANEL),
        ],
    ], font=FONT_LABEL, title_color=ACCENT2, background_color=PANEL,
       border_width=1, relief=sg.RELIEF_FLAT, expand_x=True, pad=(0, 3))

    #Domain panel
    domain_panel = sg.Frame("  ◈ DOMAIN INFO GATHERING ", [
        [
            sg.Text("DOMAIN :", font=FONT_LABEL, text_color=ACCENT3,
                    background_color=PANEL, size=(12, 1)),
            sg.Input(key="-DOMAIN-", font=FONT_MONO, size=(30, 1),
                     background_color=BG2, text_color=TEXT_BRIGHT,
                     border_width=1),
            sg.Button("▶  RUN DOMAIN", key="-RUN_DOM-", font=FONT_MONO,
                      size=(14, 1), button_color=(TEXT_BRIGHT, ACCENT2),
                      border_width=0, pad=(8, 4)),
        ],
        [
            sg.Text("", background_color=PANEL, size=(12, 1)),
            sg.Text("Subdomain enum (crt.sh) + WHOIS / Shodan / Censys links",
                    font=FONT_MONO_S, text_color=TEXT_DIM,
                    background_color=PANEL),
        ],
    ], font=FONT_LABEL, title_color=ACCENT2, background_color=PANEL,
       border_width=1, relief=sg.RELIEF_FLAT, expand_x=True, pad=(0, 3))

    #Quick-open web tools
    WEB_TOOLS = [
        ("Shodan",      "https://www.shodan.io",              "IoT / host search"),
        ("Censys",      "https://search.censys.io",           "Internet-wide scan data"),
        ("AbuseIPDB",   "https://www.abuseipdb.com",          "IP reputation check"),
        ("BGP.he.net",  "https://bgp.he.net",                 "ASN & BGP lookup"),
    ]
    web_rows = [[
        sg.Text(f"  ◈  {name}", font=FONT_LABEL, text_color=ACCENT3,
                background_color=PANEL, size=(14, 1)),
        sg.Text(desc, font=FONT_MONO_S, text_color=TEXT_DIM,
                background_color=PANEL, expand_x=True),
        sg.Button("↗ OPEN", key=f"-WEB-{name}-", font=FONT_MONO_S,
                  button_color=(ACCENT3, PANEL), border_width=1, pad=(4, 2)),
    ] for name, url, desc in WEB_TOOLS]

    web_panel = sg.Frame("  ◈ WEB INSTRUMENTS ", web_rows,
                         font=FONT_LABEL, title_color=ACCENT2,
                         background_color=PANEL, border_width=1,
                         relief=sg.RELIEF_FLAT, expand_x=True, pad=(0, 4))

    #Console
    console = sg.Frame("  ◈ CONSOLE OUTPUT ", [
        [sg.Multiline(
            default_text=(
                f"[{time.strftime('%H:%M:%S')}] IP/Domain module — ready\n"
                f"[{time.strftime('%H:%M:%S')}] Enter a target and select a mode.\n"
            ),
            key="-LOG-",
            font=("Courier New", 8),
            text_color=SUCCESS,
            background_color="#04040d",
            size=(None, 16),
            expand_x=True,
            expand_y=True,
            autoscroll=True,
            disabled=True,
            no_scrollbar=False,
            pad=(4, 4),
        )],
        [
            sg.Button("CLEAR LOG", key="-CLEAR-", font=FONT_MONO_S,
                      button_color=(TEXT_DIM, BORDER), border_width=0,
                      pad=(4, 4)),
            sg.Push(background_color=PANEL),
            sg.Button("OPEN LOGS FOLDER", key="-OPEN_LOGS-",
                      font=FONT_MONO_S,
                      button_color=(ACCENT3, PANEL), border_width=1,
                      pad=(4, 4)),
        ],
    ], font=FONT_LABEL, title_color=ACCENT2,
       background_color=PANEL, border_width=1,
       relief=sg.RELIEF_FLAT, expand_x=True, expand_y=True, pad=(0, 4))

    #Status bar
    statusbar = [
        sg.Text("◈", text_color=ACCENT2, background_color=BG, font=FONT_MONO_S),
        sg.Text("STATUS:", text_color=TEXT_DIM, background_color=BG, font=FONT_MONO_S),
        sg.Text("IDLE", key="-STATUS-", text_color=SUCCESS,
                background_color=BG, font=FONT_MONO_S, size=(20, 1)),
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
        [ip_panel],
        [domain_panel],
        [_sep(BORDER, (0, 4))],
        [web_panel],
    ], background_color=BG, vertical_alignment="top",
       expand_x=True, expand_y=True, pad=((10, 6), (8, 8)))

    right = sg.Column([
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
        "MONOLYTH :: IP / Domain Recon",
        build_layout(),
        background_color=BG,
        size=(1280, 820),
        resizable=True,
        finalize=True,
        use_custom_titlebar=False,
    )

    WEB_URLS = {
        "-WEB-Shodan-":     "https://www.shodan.io",
        "-WEB-Censys-":     "https://search.censys.io",
        "-WEB-AbuseIPDB-":  "https://www.abuseipdb.com",
        "-WEB-BGP.he.net-": "https://bgp.he.net",
    }

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, "-EXIT-"):
            break

        elif event == "-RUN_IP-":
            ip = values["-IP-"].strip()
            if not ip:
                log_err(window, "IP address cannot be empty.")
                set_status(window, "NO INPUT", DANGER)
                continue
            threading.Thread(
                target=run_ip, args=(ip, window), daemon=True
            ).start()

        elif event == "-RUN_DOM-":
            domain = values["-DOMAIN-"].strip().lstrip("https://").lstrip("http://").rstrip("/")
            if not domain:
                log_err(window, "Domain cannot be empty.")
                set_status(window, "NO INPUT", DANGER)
                continue
            threading.Thread(
                target=run_domain, args=(domain, window), daemon=True
            ).start()

        elif event in WEB_URLS:
            webbrowser.open(WEB_URLS[event])
            log(window, f"Opening: {WEB_URLS[event]}")

        elif event == "-CLEAR-":
            window["-LOG-"].update(value="")
            log(window, "Console cleared.")

        elif event == "-OPEN_LOGS-":
            p = Path("Logs")
            p.mkdir(parents=True, exist_ok=True)
            webbrowser.open(str(p.resolve()))
            log(window, f"Opened: {p.resolve()}")

    window.close()


if __name__ == "__main__":
    main()