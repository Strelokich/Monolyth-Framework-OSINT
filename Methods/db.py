import os
import csv
import time
import threading
from pathlib import Path

import openpyxl
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
FONT_LABEL  = ("Courier New", 9, "bold")

BANNER = """
  ██████╗  █████╗ ████████╗ █████╗ ██████╗  █████╗ ███████╗███████╗
  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝
  ██║  ██║███████║   ██║   ███████║██████╔╝███████║███████╗█████╗  
  ██║  ██║██╔══██║   ██║   ██╔══██║██╔══██╗██╔══██║╚════██║██╔══╝  
  ██████╔╝██║  ██║   ██║   ██║  ██║██████╔╝██║  ██║███████║███████╗
  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝
              [ L O C A L   D A T A B A S E   S E A R C H ]
"""



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

def log_warn(window, msg):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}] ▸ {msg}", text_color=WARN, end="\n")

def log_result(window, msg):
    ts = time.strftime("%H:%M:%S")
    window["-LOG-"].print(f"[{ts}]   {msg}", text_color=ACCENT3, end="\n")

def set_status(window, text, color=SUCCESS):
    window["-STATUS-"].update(value=text, text_color=color)



#core search service(original logic preserved)
def search(query, directory, window):
    found   = False
    results = []

    set_status(window, "SEARCHING...", WARN)
    log(window, f"Query: '{query}'")
    log(window, f"Directory: {directory}")
    log(window, "─" * 50)

    try:
        files = os.listdir(directory)
        csv_count  = sum(1 for f in files if f.lower().endswith(".csv"))
        xlsx_count = sum(1 for f in files if f.lower().endswith(".xlsx"))
        log(window, f"Files found — CSV: {csv_count}  XLSX: {xlsx_count}")
        log(window, "─" * 50)

        for filename in files:
            filepath = os.path.join(directory, filename)

            #CSV
            if filename.lower().endswith(".csv"):
                log_warn(window, f"Scanning {filename} …")
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        reader = csv.reader(f)
                        for line_number, row in enumerate(reader, start=1):
                            if query.lower() in str(row).lower():
                                result_line = (
                                    f"[FOUND CSV] {filename} "
                                    f"(line {line_number}): {row}"
                                )
                                log_result(window, result_line)
                                results.append(result_line)
                                found = True
                except Exception as e:
                    log_err(window, f"{filename}: {e}")

            #xlsx
            elif filename.lower().endswith(".xlsx"):
                log_warn(window, f"Scanning {filename} …")
                try:
                    workbook = openpyxl.load_workbook(filepath, data_only=True)
                    for sheet in workbook.worksheets:
                        for row_number, row in enumerate(
                            sheet.iter_rows(values_only=True), start=1
                        ):
                            if query.lower() in str(row).lower():
                                result_line = (
                                    f"[FOUND XLSX] {filename} "
                                    f"[{sheet.title}] "
                                    f"(row {row_number}): {row}"
                                )
                                log_result(window, result_line)
                                results.append(result_line)
                                found = True
                except Exception as e:
                    log_err(window, f"{filename}: {e}")

        log(window, "─" * 50)

        if found:
            folder_path = Path("Logs")
            folder_path.mkdir(parents=True, exist_ok=True)
            full_path = folder_path / "db_logs.txt"
            with open(full_path, "w", encoding="utf-8") as out:
                for line in results:
                    out.write(line + "\n")

            log_ok(window, f"{len(results)} match(es) found.")
            log_ok(window, f"Results saved → {full_path}")
            set_status(window, f"{len(results)} MATCHES", SUCCESS)
            window["-RESULT_COUNT-"].update(
                value=f"  ◈  {len(results)} result(s) saved to Logs/db_logs.txt",
                text_color=SUCCESS,
            )
        else:
            log(window, "No matches found.")
            set_status(window, "NO MATCHES", TEXT_DIM)
            window["-RESULT_COUNT-"].update(
                value="  ◈  No matches found.",
                text_color=TEXT_DIM,
            )

    except Exception as e:
        log_err(window, f"FATAL: {e}")
        set_status(window, "ERROR", DANGER)



#layout
def build_layout():
    #Header
    header = sg.Column([
        [sg.Text(BANNER, font=("Courier New", 7, "bold"),
                 text_color=ACCENT1, background_color=BG, pad=((0,0),(8,0)))],
        [sg.Text(glitch_sep(90), font=("Courier New", 7),
                 text_color=ACCENT2, background_color=BG)],
        [sg.Text(" MONOLYTH OSINT v2.0  |  Module 01 — LOCAL DATABASES",
                 font=FONT_MONO_S, text_color=TEXT_DIM, background_color=BG)],
        [_sep(ACCENT2, (0, 4))],
    ], background_color=BG, expand_x=True)

    #Search panel
    search_panel = sg.Frame("  ◈ SEARCH PARAMETERS ", [
        [
            sg.Text("QUERY :", font=FONT_LABEL, text_color=ACCENT3,
                    background_color=PANEL, size=(10, 1)),
            sg.Input(key="-QUERY-", font=FONT_MONO, size=(36, 1),
                     background_color=BG2, text_color=TEXT_BRIGHT,
                     border_width=1),
            sg.Button("▶  SEARCH", key="-SEARCH-", font=FONT_MONO,
                      size=(12, 1), button_color=(TEXT_BRIGHT, ACCENT1),
                      border_width=0, pad=(8, 4)),
        ],
        [
            sg.Text("DIRECTORY :", font=FONT_LABEL, text_color=ACCENT3,
                    background_color=PANEL, size=(10, 1)),
            sg.Input(key="-DIR-", default_text=os.getcwd(),
                     font=FONT_MONO_S, size=(36, 1),
                     background_color=BG2, text_color=TEXT_BRIGHT,
                     border_width=1),
            sg.FolderBrowse("  BROWSE", font=FONT_MONO_S,
                            button_color=(ACCENT3, PANEL),
                            target="-DIR-", pad=(8, 4)),
        ],
        [
            sg.Text("", background_color=PANEL, size=(10, 1)),
            sg.Text("Searches all .csv and .xlsx files in the chosen directory.",
                    font=FONT_MONO_S, text_color=TEXT_DIM,
                    background_color=PANEL),
        ],
    ], font=FONT_LABEL, title_color=ACCENT2,
       background_color=PANEL, border_width=1,
       relief=sg.RELIEF_FLAT, expand_x=True, pad=(0, 4))

    #Stats strip
    stats_strip = [
        sg.Text("◈", text_color=ACCENT2, background_color=BG,
                font=FONT_MONO_S),
        sg.Text("  ◈  Awaiting query…", key="-RESULT_COUNT-",
                font=FONT_MONO_S, text_color=TEXT_DIM,
                background_color=BG, expand_x=True),
    ]

    #Console
    console = sg.Frame("  ◈ CONSOLE OUTPUT ", [
        [sg.Multiline(
            default_text=(
                f"[{time.strftime('%H:%M:%S')}] DB Search module — ready\n"
                f"[{time.strftime('%H:%M:%S')}] Enter a query and choose a directory.\n"
            ),
            key="-LOG-",
            font=("Courier New", 8),
            text_color=SUCCESS,
            background_color="#04040d",
            size=(None, 18),
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
        sg.Text("◈", text_color=ACCENT2, background_color=BG,
                font=FONT_MONO_S),
        sg.Text("STATUS:", text_color=TEXT_DIM, background_color=BG,
                font=FONT_MONO_S),
        sg.Text("IDLE", key="-STATUS-", text_color=SUCCESS,
                background_color=BG, font=FONT_MONO_S, size=(20, 1)),
        sg.Push(background_color=BG),
        sg.Text(f"OPERATOR SESSION  {time.strftime('%Y-%m-%d  %H:%M')}",
                text_color=TEXT_DIM, background_color=BG,
                font=FONT_MONO_S),
        sg.Text(" ◈ ", text_color=ACCENT2, background_color=BG,
                font=FONT_MONO_S),
        sg.Button("EXIT", key="-EXIT-", font=FONT_MONO_S, size=(6, 1),
                  button_color=(DANGER, BG2), border_width=1, pad=(2, 2)),
    ]

    layout = [
        [sg.Column([
            [header],
            [search_panel],
            stats_strip,
            [_sep(BORDER, (0, 4))],
            [console],
        ], background_color=BG, expand_x=True, expand_y=True,
           pad=((10, 10), (8, 8)))],
        [_sep(ACCENT2, (0, 2))],
        statusbar,
    ]
    return layout



#main loop
def main():
    sg.set_options(element_padding=(0, 0), margins=(0, 0))

    window = sg.Window(
        "MONOLYTH :: DB Search",
        build_layout(),
        background_color=BG,
        size=(900, 700),
        resizable=True,
        finalize=True,
        use_custom_titlebar=False,
    )
    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, "-EXIT-"):
            break

        elif event == "-SEARCH-":
            query = values["-QUERY-"].strip()
            directory = values["-DIR-"].strip()

            if not query:
                log_err(window, "Query cannot be empty.")
                set_status(window, "NO QUERY", DANGER)
                continue

            if not os.path.isdir(directory):
                log_err(window, f"Directory not found: {directory}")
                set_status(window, "BAD DIRECTORY", DANGER)
                continue

            set_status(window, "RUNNING…", WARN)
            threading.Thread(
                target=search,
                args=(query, directory, window),
                daemon=True,
            ).start()

        elif event == "-CLEAR-":
            window["-LOG-"].update(value="")
            log(window, "Console cleared.")

        elif event == "-OPEN_LOGS-":
            logs_path = Path("Logs")
            logs_path.mkdir(parents=True, exist_ok=True)
            import webbrowser
            webbrowser.open(str(logs_path.resolve()))
            log(window, f"Opened logs folder: {logs_path.resolve()}")

    window.close()

if __name__ == "__main__":
    main()
