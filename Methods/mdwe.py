import sys
import time
import random
import requests
import threading
from urllib.parse import urlparse
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# GUI Imports
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QProgressBar
)
from PySide6.QtGui import QPalette, QColor, QFont, QTextCursor
from PySide6.QtCore import Qt, QObject, Signal, QThread

# ================= CONFIGURATION & HEADERS =================

HEADERS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_header():
    return {"User-Agent": random.choice(HEADERS)}

# ================= WORKER THREAD =================

class ScannerWorker(QThread):
    log_signal = Signal(str)      # Сигнал для текста
    progress_signal = Signal(int) # Сигнал для прогресса (опционально)
    finished_signal = Signal()    # Сигнал завершения

    def __init__(self, target, mode="full"):
        super().__init__()
        self.target = target
        self.mode = mode
        self.is_running = True

    def log(self, text):
        self.log_signal.emit(text)

    def run(self):
        self.log(f"[*] INITIALIZING SCAN TARGET: {self.target}")
        self.log(f"[*] MODE: {self.mode.upper()}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False) # Поставьте False, если хотите видеть браузер
                context = browser.new_context(user_agent=random.choice(HEADERS))
                page = context.new_page()

                if self.mode == "admin" or self.mode == "full":
                    self.scan_admin_panels(page)
                
                if self.mode == "config" or self.mode == "full":
                    self.scan_config_files(page)
                
                if self.mode == "db" or self.mode == "full":
                    self.scan_database_dumps(page)
                
                if self.mode == "logs" or self.mode == "full":
                    self.scan_log_files(page)

                if self.mode == "0day" or self.mode == "full":
                    self.scan_zero_day(page)

                browser.close()
                
        except Exception as e:
            self.log(f"[FATAL ERROR] {str(e)}")
        
        self.log("[*] SCAN COMPLETED.")
        self.finished_signal.emit()

# CORE LOGIC FROM

    def google_search(self, page, dork):
        if not self.is_running: return []
        
        query = f"site:{self.target} {dork}"
        search_url = f"https://www.google.com/search?q={query}"
        results = []
        
        try:
            self.log(f"[QUERY] {dork}")
            page.goto(search_url, timeout=30000)
            page.wait_for_timeout(random.randint(2000, 4000)) # Anti-bot delay
            
            content = page.content()
            
            # Проверка на капчу
            if "captcha" in content.lower() or "sorry" in page.url:
                self.log("[!] GOOGLE CAPTCHA DETECTED. SKIPPING...")
                return []

            if "did not match any documents" in content:
                return []

            soup = BeautifulSoup(content, 'html.parser')
            # Парсинг ссылок из выдачи Google (стандартные селекторы)
            for g in soup.find_all('div', class_='g'):
                anchors = g.find_all('a')
                if anchors:
                    link = anchors[0]['href']
                    if link.startswith('http'):
                        results.append(link)
                        
        except Exception as e:
            self.log(f"[ERR] Search failed: {e}")
            
        return results

    def scan_admin_panels(self, page):
        self.log("\n--- STARTING ADMIN PANEL SCAN ---")
        dorks = [
                "admin/", "admin.php", "administrator/", "admin/login.php", "login.php", "admin_panel/", "admin-area/",
                "admin_login.php", "admin/index.php", "admincp/", "user.php", "controlpanel/", "dashboard/", "panel/",
                "manage/", "admin/account.php", "admin/home.php", "cpanel/", "backend/", "admin1/", "admin2/", "moderator/",
                "webadmin/", "siteadmin/", "login/", "auth/", "signin/", "wp-login.php", "wp-admin/"
        ]
        for dork in dorks:
            links = self.google_search(page, dork)
            for link in links:
                self.log(f"[FOUND ADMIN] {link}")

    def scan_config_files(self, page):
        self.log("\n--- STARTING CONFIG FILE SCAN ---")
        dorks = [
            "filetype:env", "filetype:xml", "filetype:conf", "filetype:cnf",
            "filetype:reg", "filetype:ini", "ext:env", "intext:\"DB_PASSWORD\""
        ]
        for dork in dorks:
            links = self.google_search(page, dork)
            for link in links:
                self.log(f"[FOUND CONFIG] {link}")

    def scan_database_dumps(self, page):
        self.log("\n--- STARTING DATABASE DUMP SCAN ---")
        dorks = [
            "filetype:sql", "filetype:db", "filetype:dump", "filetype:bkp",
            "intext:\"sql dump\"", "intext:\"index of\" \"backup\"",
            "ext:sql intext:\"insert into\""
        ]
        for dork in dorks:
            links = self.google_search(page, dork)
            for link in links:
                self.log(f"[FOUND DB LEAK] {link}")

    def scan_log_files(self, page):
        self.log("\n--- STARTING LOG FILE SCAN ---")
        dorks = [
            "filetype:log", "intext:\"error log\"", "ext:log", 
            "inurl:log", "intext:\"fatal error\""
        ]
        for dork in dorks:
            links = self.google_search(page, dork)
            for link in links:
                self.log(f"[FOUND LOG] {link}")

    def scan_zero_day(self, page):
        self.log("\n--- STARTING 0-DAY / VULN SCAN ---")
        dorks = [
            "inurl:php?id=", "inurl:index.php?id=", "inurl:page?id=",
            "intext:\"syntax error\" filetype:php",
            "inurl:eval(", "inurl:base64_decode("
        ]
        for dork in dorks:
            links = self.google_search(page, dork)
            for link in links:
                self.log(f"[POTENTIAL VULN] {link}")

# GUI CLASS

class STALKER_GUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MDWE SCANNER [RE:CODED]")
        self.resize(1000, 650)
        self.worker = None

        # Main Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # TITLE
        title = QLabel("MDWE // OSINT & VULN SCANNER")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Consolas", 22, QFont.Bold))
        layout.addWidget(title)

        # SEPARATOR
        sep = QLabel("--------------------------------------------------")
        sep.setAlignment(Qt.AlignCenter)
        sep.setFont(QFont("Consolas", 10))
        sep.setStyleSheet("color: #2e8b57;")
        layout.addWidget(sep)

        # INPUT FIELD
        self.input = QLineEdit()
        self.input.setPlaceholderText("ENTER TARGET DOMAIN (e.g., example.com)...")
        self.input.setFont(QFont("Consolas", 12))
        self.input.setStyleSheet("""
            QLineEdit {
                background-color: #050807;
                color: #7CFC98;
                border: 2px solid #2e8b57;
                padding: 10px;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #7CFC98;
            }
        """)
        layout.addWidget(self.input)

        # BUTTONS LAYOUT
        btn_layout = QHBoxLayout()
        
        # Define buttons and their scan modes
        buttons_config = [
            ("ADMIN SCAN", "admin"),
            ("CONFIG SCAN", "config"),
            ("DB & SQL", "db"),
            ("LOG FILES", "logs"),
            ("0-DAY CHECK", "0day"),
            ("FULL ATTACK", "full")
        ]

        for text, mode in buttons_config:
            btn = QPushButton(text)
            btn.setFont(QFont("Consolas", 11, QFont.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #101810;
                    border: 1px solid #2e8b57;
                    color: #7CFC98;
                    padding: 12px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #1f3326;
                    border: 1px solid #7CFC98;
                    color: #ffffff;
                }
                QPushButton:pressed {
                    background-color: #2e8b57;
                }
            """)
            btn.clicked.connect(lambda _, m=mode: self.start_scan(m))
            btn_layout.addWidget(btn)

        layout.addLayout(btn_layout)


        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #2e8b57;
                background-color: #050807;
                height: 10px;
                text-align: center; 
            }
            QProgressBar::chunk {
                background-color: #2e8b57;
            }
        """)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        # LOG WINDOW
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 10))
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #050807;
                border: 1px solid #2e8b57;
                color: #7CFC98;
                padding: 5px;
            }
        """)
        layout.addWidget(self.log_area)

        self.setLayout(layout)

    def append_log(self, text):
        self.log_area.append(text)
        self.log_area.moveCursor(QTextCursor.End)

    def start_scan(self, mode):
        target = self.input.text().strip()
        if not target:
            self.append_log("[!] ERROR: Target input is empty.")
            return

        # Disable input while running (optional, but good for safety)
        self.progress.setRange(0, 0) # Infinite loading animation
        self.append_log(f"\n> INITIATING {mode.upper()} SCAN ON: {target}...")

        # Setup Thread
        self.worker = ScannerWorker(target, mode)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.scan_finished)
        self.worker.start()

    def scan_finished(self):
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.append_log("> SCAN SEQUENCE FINISHED.\n")

# ================= MAIN =================

def set_stalker_palette(app):
    palette = QPalette()
    dark_color = QColor("#050807")
    text_color = QColor("#7CFC98")
    
    palette.setColor(QPalette.Window, dark_color)
    palette.setColor(QPalette.WindowText, text_color)
    palette.setColor(QPalette.Base, dark_color)
    palette.setColor(QPalette.AlternateBase, dark_color)
    palette.setColor(QPalette.ToolTipBase, text_color)
    palette.setColor(QPalette.ToolTipText, dark_color)
    palette.setColor(QPalette.Text, text_color)
    palette.setColor(QPalette.Button, dark_color)
    palette.setColor(QPalette.ButtonText, text_color)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    
    app.setPalette(palette)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_stalker_palette(app)
    
    window = STALKER_GUI()
    window.show()
    
    sys.exit(app.exec())