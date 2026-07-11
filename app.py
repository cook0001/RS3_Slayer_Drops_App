import customtkinter as ctk
import tkinter.messagebox as messagebox
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont
import threading
import requests
from bs4 import BeautifulSoup
import urllib.parse
import json
import os
import io
import concurrent.futures
import re
import locale
import time
import csv
import winsound
import math
import sys
import ctypes
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

try:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
except ImportError:
    toaster = None

try:
    import mss
    import pytesseract
    import cv2
    import numpy as np
    HAS_CV = True
except ImportError:
    HAS_CV = False

try:
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CACHE_DIR = "cache"
IMG_CACHE_DIR = os.path.join(CACHE_DIR, "images")
DATA_CACHE_DIR = os.path.join(CACHE_DIR, "data")
SESSION_FILE = os.path.join(CACHE_DIR, "session.json")
META_FILE = os.path.join(CACHE_DIR, "session_meta.json")

os.makedirs(IMG_CACHE_DIR, exist_ok=True)
os.makedirs(DATA_CACHE_DIR, exist_ok=True)

SLAYER_MONSTERS = [
    # Slayer
    "Aberrant spectre", "Abyssal demon", "Acheron mammoth", "Airut", "Aquanite", "Automatons",
    "Banshee", "Bloodveld", "Camel warrior", "Cave horror", "Celestial dragon", "Corrupted worker", 
    "Crystal shapeshifter", "Dark beast", "Desert strykewyrm", "Dust devil", "Edimmu", "Gargoyle", 
    "Gemstone dragon", "Glacor", "Ice strykewyrm", "Jungle strykewyrm", "Kurask", "Living wyvern", 
    "Moss golem", "Mutated jadinko", "Nechryael", "Nightmare", "Nodon dragonkin", "Ripper demon", 
    "Rune dragon", "Soul devourer", "Spiritual mage", "Spiritual warrior", "Terror dog", 
    "Tormented demon", "Vyrewatch",
    # Bosses
    "Araxxor", "Telos, the Warden", "Zamorak, Lord of Chaos", "Kerapac, the bound", 
    "Nex", "Nex: Angel of Death", "TzKal-Zuk", "Raksha, the Shadow Colossus", "Legiones", 
    "Kalphite King", "Vorago", "Queen Black Dragon", "Corporeal Beast", "Vindicta", 
    "Gregorovic", "Helwyr", "Twin Furies", "Kree'arra", "General Graardor", "Commander Zilyana", "K'ril Tsutsaroth"
]

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def format_number(num):
    return f"{num:,}"

def parse_price(price_str):
    try:
        clean = price_str.replace(',', '').replace('Not sold', '0').replace('N/A', '0')
        nums = [int(s) for s in re.findall(r'\d+', clean)]
        if nums:
            return sum(nums) // len(nums)
        return 0
    except:
        return 0

def parse_probability(rarity_str):
    rarity_str = rarity_str.lower()
    if 'always' in rarity_str:
        return 1.0
    match = re.search(r'1\s*/\s*([\d,]+(?:(?:\.\d+)?))', rarity_str)
    if match:
        denom = float(match.group(1).replace(',', ''))
        if denom > 0:
            return 1.0 / denom
    if 'common' in rarity_str and 'uncommon' not in rarity_str:
        return 0.05
    elif 'uncommon' in rarity_str:
        return 0.01
    elif 'rare' in rarity_str and 'very' not in rarity_str:
        return 0.001
    elif 'very rare' in rarity_str:
        return 0.0001
    return 0.0

class AutoTracker(threading.Thread):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.running = True
        self.daemon = True
        self.tesseract_installed = False
        paths = [r'C:\Program Files\Tesseract-OCR\tesseract.exe', r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe']
        for p in paths:
            if os.path.exists(p):
                pytesseract.pytesseract.tesseract_cmd = p
                self.tesseract_installed = True
                break

    def run(self):
        if not HAS_CV or not self.tesseract_installed:
            self.app.after(0, self.app.stop_auto_tracker)
            return
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            capture_area = {
                "top": int(monitor["height"] * 0.7),
                "left": 0,
                "width": int(monitor["width"] * 0.4),
                "height": int(monitor["height"] * 0.3)
            }
            while self.running:
                try:
                    img = np.array(sct.grab(capture_area))
                    gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
                    text = pytesseract.image_to_string(thresh)
                    for line in text.split('\n'):
                        line = line.strip().lower()
                        if "drop:" in line or "loot:" in line:
                            parts = line.split(":")
                            if len(parts) > 1:
                                item_name = parts[-1].strip().title()
                                if len(item_name) > 2:
                                    self.app.after(0, self.app.auto_add_drop_by_name, item_name)
                except: pass
                time.sleep(2.5)

class RS3DropLookupApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Tell Windows this is a distinct app to fix Taskbar Icon
        try:
            myappid = 'rs3.slayerdrops.tracker.1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except: pass
        
        self.title("RS3 Slayer Drops")
        self.geometry("1400x900")
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except: pass
        
        self.current_drops = []
        self.current_info = {}
        
        self.sessions = {"Default": {}}
        self.session_meta = {"Default": {"start_time": None}}
        self.current_session = "Default"
        
        self.ctk_images = {}
        self.sparklines = {}
        self.auto_tracker_thread = None
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_main_area()
        self.load_session()
        self.update_gphr_display()

    def build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=340, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(11, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Slayer Drops", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Hiscores Username
        self.rs_username_var = ctk.StringVar()
        user_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        user_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        ctk.CTkLabel(user_frame, text="RSN:").pack(side="left")
        ctk.CTkEntry(user_frame, textvariable=self.rs_username_var, placeholder_text="Username for Readiness").pack(side="left", fill="x", expand=True, padx=(5,0))

        # Ironman Mode
        self.ironman_var = ctk.BooleanVar(value=False)
        self.ironman_cb = ctk.CTkSwitch(self.sidebar_frame, text="Ironman Mode", variable=self.ironman_var, command=self.render_drops, progress_color="#b33939")
        self.ironman_cb.grid(row=2, column=0, padx=20, pady=5, sticky="w")

        # Search Auto-complete
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkComboBox(self.sidebar_frame, values=sorted(SLAYER_MONSTERS), variable=self.search_var)
        self.search_entry.grid(row=3, column=0, padx=20, pady=(10, 10), sticky="ew")
        
        search_btn_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        search_btn_frame.grid(row=4, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.search_btn = ctk.CTkButton(search_btn_frame, text="Search", command=lambda: self.start_search(force=False), width=120)
        self.search_btn.pack(side="left", expand=True, padx=(0, 5))
        self.refresh_btn = ctk.CTkButton(search_btn_frame, text="Live Refresh", fg_color="#b08d00", hover_color="#8c7000", command=lambda: self.start_search(force=True))
        self.refresh_btn.pack(side="right", expand=True, padx=(5, 0))

        # Filters
        self.filter_label = ctk.CTkLabel(self.sidebar_frame, text="Filters & Sorting", font=ctk.CTkFont(size=14, weight="bold"))
        self.filter_label.grid(row=5, column=0, padx=20, pady=(5, 0), sticky="w")
        
        self.min_val_label = ctk.CTkLabel(self.sidebar_frame, text="Min Value: 0 gp")
        self.min_val_label.grid(row=6, column=0, padx=20, pady=(0, 0), sticky="w")
        self.min_val_slider = ctk.CTkSlider(self.sidebar_frame, from_=0, to=50000, number_of_steps=100, command=self.update_min_val)
        self.min_val_slider.set(0)
        self.min_val_slider.grid(row=7, column=0, padx=20, pady=(0, 5), sticky="ew")

        check_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        check_frame.grid(row=8, column=0, padx=20, sticky="w")
        self.hide_charms_var = ctk.BooleanVar(value=False)
        self.hide_charms = ctk.CTkCheckBox(check_frame, text="Charms", variable=self.hide_charms_var, command=self.render_drops)
        self.hide_charms.grid(row=0, column=0, pady=5, padx=(0, 10))
        self.hide_salvage_var = ctk.BooleanVar(value=False)
        self.hide_salvage = ctk.CTkCheckBox(check_frame, text="Salvage", variable=self.hide_salvage_var, command=self.render_drops)
        self.hide_salvage.grid(row=0, column=1, pady=5)

        self.sort_var = ctk.StringVar(value="Default")
        self.sort_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Default", "Highest Price", "Lowest Price", "Highest Alch", "Rarity"], variable=self.sort_var, command=lambda e: self.render_drops())
        self.sort_menu.grid(row=9, column=0, padx=20, pady=5, sticky="ew")
        
        # Variance Predictor Tool
        calc_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="#1d1e20")
        calc_frame.grid(row=10, column=0, padx=20, pady=5, sticky="ew")
        self.task_qty_entry = ctk.CTkEntry(calc_frame, placeholder_text="Task Amount (e.g. 150)")
        self.task_qty_entry.pack(padx=10, pady=(10, 5), fill="x")
        self.calc_btn = ctk.CTkButton(calc_frame, text="Predict Task Profit (ML Variance)", command=self.calculate_profit)
        self.calc_btn.pack(padx=10, pady=(0, 10), fill="x")

        # Loot Tracker
        self.tracker_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="#1a251a")
        self.tracker_frame.grid(row=11, column=0, padx=20, pady=10, sticky="nsew")
        self.tracker_frame.grid_columnconfigure(0, weight=1)
        
        self.session_var = ctk.StringVar(value=self.current_session)
        self.session_menu = ctk.CTkOptionMenu(self.tracker_frame, variable=self.session_var, command=self.change_session)
        self.session_menu.grid(row=0, column=0, pady=(10, 5), padx=10, sticky="ew")
        
        self.tracker_total_label = ctk.CTkLabel(self.tracker_frame, text="Total: 0 gp", text_color="#55ff55", font=ctk.CTkFont(weight="bold", size=16))
        self.tracker_total_label.grid(row=1, column=0, pady=2)
        
        self.tracker_gphr_label = ctk.CTkLabel(self.tracker_frame, text="GP/Hr: 0 gp", text_color="#ffcc00", font=ctk.CTkFont(weight="bold", size=14))
        self.tracker_gphr_label.grid(row=2, column=0, pady=2)
        
        btn_frame = ctk.CTkFrame(self.tracker_frame, fg_color="transparent")
        btn_frame.grid(row=3, column=0, pady=5, sticky="ew")
        self.view_tracker_btn = ctk.CTkButton(btn_frame, text="Manage", fg_color="#2b7b2b", hover_color="#1e5c1e", command=self.open_tracker_window, width=120)
        self.view_tracker_btn.pack(side="left", padx=10)
        self.export_btn = ctk.CTkButton(btn_frame, text="Import CSV", fg_color="#555555", hover_color="#333333", command=self.import_csv, width=120)
        self.export_btn.pack(side="right", padx=10)

        self.auto_tracker_var = ctk.BooleanVar(value=False)
        self.auto_tracker_cb = ctk.CTkCheckBox(self.tracker_frame, text="Auto-OCR Tracker", variable=self.auto_tracker_var, command=self.toggle_auto_tracker)
        self.auto_tracker_cb.grid(row=4, column=0, pady=10)

    def build_main_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(self.main_frame, text="Ready. Search a monster or boss to begin.", font=ctk.CTkFont(size=16))
        self.status_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.strategy_frame = ctk.CTkFrame(self.main_frame, fg_color="#1f2833", corner_radius=10)
        self.strategy_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.strategy_label = ctk.CTkLabel(self.strategy_frame, text="Strategy & Readiness | Search to evaluate", text_color="#5cdb95")
        self.strategy_label.pack(pady=10)

        self.drops_scroll = ctk.CTkScrollableFrame(self.main_frame)
        self.drops_scroll.grid(row=2, column=0, sticky="nsew")
        
    def fetch_hiscores(self, username):
        if not username: return None
        try:
            r = requests.get(f"https://secure.runescape.com/m=hiscore/index_lite.ws?player={urllib.parse.quote(username)}", timeout=5)
            if r.status_code == 200:
                lines = r.text.strip().split('\n')
                if len(lines) >= 20:
                    slayer_line = lines[19].split(',')
                    if len(slayer_line) >= 2:
                        return int(slayer_line[1])
        except: pass
        return None

    def generate_sparkline(self, item_name):
        try:
            safe_name = "".join([c for c in item_name if c.isalpha() or c.isdigit()]).rstrip()
            spark_path = os.path.join(IMG_CACHE_DIR, f"spark_{safe_name}.png")
            if os.path.exists(spark_path): return spark_path
            
            r = requests.get(f"https://api.weirdgloop.org/exchange/history/rs/last90d?name={urllib.parse.quote(item_name)}", timeout=5)
            if r.status_code == 200:
                data = r.json()
                if item_name in data and data[item_name]:
                    prices = [pt["price"] for pt in data[item_name]]
                    fig = plt.figure(figsize=(1.5, 0.4), dpi=100)
                    ax = fig.add_subplot(111)
                    color = "#55ff55" if prices[-1] >= prices[0] else "#ff5555"
                    ax.plot(prices, color=color, linewidth=2)
                    ax.axis('off')
                    fig.savefig(spark_path, transparent=True, bbox_inches='tight', pad_inches=0)
                    plt.close(fig)
                    return spark_path
        except: pass
        return None

    def update_min_val(self, value):
        val = int(value)
        self.min_val_label.configure(text=f"Min Value: {format_number(val)} gp")
        if hasattr(self, "_render_timer") and self._render_timer:
            self.after_cancel(self._render_timer)
        self._render_timer = self.after(300, self.render_drops)

    def change_session(self, choice):
        if choice == "New Session...":
            dialog = ctk.CTkInputDialog(text="Enter new session name:", title="New Session")
            name = dialog.get_input()
            if name:
                self.sessions[name] = {}
                self.session_meta[name] = {"start_time": None}
                self.current_session = name
            else:
                self.session_var.set(self.current_session)
        else:
            self.current_session = choice
            
        options = list(self.sessions.keys()) + ["New Session..."]
        self.session_menu.configure(values=options)
        self.session_var.set(self.current_session)
        self.update_tracker_summary()

    def calculate_profit(self):
        if not self.current_drops: return
        qty_str = self.task_qty_entry.get()
        if not qty_str.isdigit(): return
        
        task_amount = int(qty_str)
        expected_profit = 0
        variance = 0
        
        for d in self.current_drops:
            prob = d.get("probability", 0.0)
            val = max(d.get("price_val", 0), d.get("alch_val", 0))
            
            avg_qty = 1
            qty_str_clean = d.get("quantity", "1").replace(',', '')
            nums = [int(s) for s in re.findall(r'\d+', qty_str_clean)]
            if nums: avg_qty = sum(nums) / len(nums)
                
            expected_profit += (prob * val * avg_qty * task_amount)
            # Binomial variance Approximation
            variance += (task_amount * prob * (1 - prob) * ((val * avg_qty) ** 2))
            
        std_dev = math.sqrt(variance)
        lower = max(0, expected_profit - 1.96 * std_dev)
        upper = expected_profit + 1.96 * std_dev
        
        self.status_label.configure(
            text=f"Expected: {format_number(int(expected_profit))} gp (95% CI: {format_number(int(lower))} - {format_number(int(upper))} gp)", 
            text_color="#5cdb95"
        )

    def start_search(self, force=False):
        monster = self.search_var.get().strip()
        if not monster: return
        self.status_label.configure(text=f"Loading data for {monster}...", text_color="#ffaa00")
        self.search_btn.configure(state="disabled")
        self.refresh_btn.configure(state="disabled")
        threading.Thread(target=self.fetch_drops, args=(monster, force), daemon=True).start()

    def fetch_drops(self, monster, force):
        formatted_name = urllib.parse.quote(monster.replace(" ", "_"))
        cache_file = os.path.join(DATA_CACHE_DIR, f"{formatted_name}.json")
        info_file = os.path.join(DATA_CACHE_DIR, f"{formatted_name}_info.json")
        drops = []
        info = {"weakness": "Unknown", "style": "Unknown", "slayer_lvl": "Unknown"}
        
        if not force and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f: drops = json.load(f)
                if os.path.exists(info_file):
                    with open(info_file, 'r', encoding='utf-8') as f: info = json.load(f)
                self.after(0, self.on_drops_loaded, drops, info, monster, True)
                return
            except: pass
            
        try:
            url = f"https://runescape.wiki/w/{formatted_name}"
            if force: url += f"?action=purge&_={int(time.time())}"
            headers = {"User-Agent": "SlayerDrops/5.0"}
            response = requests.get(url, headers=headers)
            if response.status_code == 404:
                self.after(0, self.show_error, f"Monster '{monster}' not found.")
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            
            infobox = soup.find('table', class_='infobox')
            if infobox:
                for tr in infobox.find_all('tr'):
                    th = tr.find('th')
                    td = tr.find('td')
                    if th and td:
                        txt = th.text.strip().lower()
                        if 'weakness' in txt: info['weakness'] = td.text.strip()
                        elif 'combat style' in txt: info['style'] = td.text.strip()
                        elif 'slayer' in txt and 'level' in txt: info['slayer_lvl'] = td.text.strip()

            tables = soup.find_all('table', class_='wikitable')
            
            def fetch_image(img_url, img_filename):
                try:
                    img_path = os.path.join(IMG_CACHE_DIR, img_filename)
                    if not os.path.exists(img_path):
                        r = requests.get(f"https://runescape.wiki{img_url}", headers=headers, timeout=5)
                        if r.status_code == 200:
                            img = Image.open(io.BytesIO(r.content))
                            img.thumbnail((32, 32), Image.Resampling.LANCZOS)
                            img.save(img_path)
                    return img_path
                except: return None

            for table in tables:
                headers_row = [th.text.strip().lower() for th in table.find_all('th')]
                if 'item' in headers_row and ('rarity' in headers_row or 'drop' in headers_row):
                    for row in table.find_all('tr')[1:]:
                        cols = row.find_all(['td', 'th'])
                        if len(cols) >= 5:
                            img_tag = cols[0].find('img')
                            img_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else None
                            
                            item = cols[1].text.strip().split('[')[0].strip()
                            quantity = cols[2].text.strip()
                            rarity = cols[3].text.strip().split('[')[0].strip()
                            price = cols[4].text.strip()
                            alch_val = parse_price(cols[5].text.strip()) if len(cols) >= 6 else 0
                            
                            if item and item != "Item":
                                safe_name = "".join([c for c in item if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                                img_filename = f"{safe_name.replace(' ', '_')}.png" if safe_name else "default.png"
                                parsed_p = parse_price(price)
                                
                                drops.append({
                                    "item": item, "quantity": quantity, "rarity": rarity, "price": price,
                                    "price_val": parsed_p, "alch_val": alch_val,
                                    "probability": parse_probability(rarity), "img_url": img_url,
                                    "img_filename": img_filename, "img_path": None, "spark_path": None
                                })

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_img = {executor.submit(fetch_image, d["img_url"], d["img_filename"]): d for d in drops if d["img_url"]}
                for future in concurrent.futures.as_completed(future_to_img):
                    d = future_to_img[future]
                    d["img_path"] = future.result()
                    
                # Fetch sparklines for expensive items
                future_to_spark = {executor.submit(self.generate_sparkline, d["item"]): d for d in drops if max(d["price_val"], d["alch_val"]) >= 50000}
                for future in concurrent.futures.as_completed(future_to_spark):
                    d = future_to_spark[future]
                    d["spark_path"] = future.result()

            if drops:
                with open(cache_file, 'w', encoding='utf-8') as f: json.dump(drops, f)
                with open(info_file, 'w', encoding='utf-8') as f: json.dump(info, f)
                self.after(0, self.on_drops_loaded, drops, info, monster, False)
            else:
                self.after(0, self.show_error, f"No drop tables found for '{monster}'.")
        except Exception as e:
            self.after(0, self.show_error, f"An error occurred: {str(e)}")

    def show_error(self, message):
        self.status_label.configure(text=message, text_color="#ff5555")
        self.search_btn.configure(state="normal")
        self.refresh_btn.configure(state="normal")

    def on_drops_loaded(self, drops, info, monster, from_cache):
        self.current_drops = drops
        self.current_info = info
        source = "Cache" if from_cache else "Live Wiki Prices"
        self.status_label.configure(text=f"Loaded {len(drops)} drops for {monster} ({source})", text_color="#55ff55")
        
        # Check Hiscores
        user = self.rs_username_var.get().strip()
        readiness_str = ""
        if user:
            slayer_lvl = self.fetch_hiscores(user)
            req_lvl = info.get('slayer_lvl', '1')
            req_lvl = int(re.sub(r'\D', '', req_lvl)) if re.sub(r'\D', '', req_lvl) else 1
            if slayer_lvl:
                if slayer_lvl >= req_lvl: readiness_str = f"| Readiness: OK (Lvl {slayer_lvl})"
                else: readiness_str = f"| Readiness: UNDER-LEVELED (Lvl {slayer_lvl} vs {req_lvl})"
            else:
                readiness_str = "| Readiness: Player not found"
        
        self.strategy_label.configure(text=f"Strategy | Weakness: {info.get('weakness','N/A')} | Style: {info.get('style','N/A')} | Req Slayer: {info.get('slayer_lvl','1')} {readiness_str}")
        
        self.search_btn.configure(state="normal")
        self.refresh_btn.configure(state="normal")
        self.render_drops()

    def render_drops(self):
        for widget in self.drops_scroll.winfo_children(): widget.destroy()
            
        min_price = int(self.min_val_slider.get())
        hide_charms = self.hide_charms_var.get()
        hide_salvage = self.hide_salvage_var.get()
        sort_mode = self.sort_var.get()
        ironman = self.ironman_var.get()

        filtered = []
        for d in self.current_drops:
            val = d.get("alch_val", 0) if ironman else max(d.get("price_val", 0), d.get("alch_val", 0))
            if val < min_price: continue
            name_lower = d["item"].lower()
            if hide_charms and "charm" in name_lower: continue
            if hide_salvage and "salvage" in name_lower: continue
            filtered.append(d)

        if sort_mode == "Highest Price" and not ironman:
            filtered.sort(key=lambda x: max(x.get("price_val", 0), x.get("alch_val", 0)), reverse=True)
        elif sort_mode == "Highest Alch" or (sort_mode == "Highest Price" and ironman):
            filtered.sort(key=lambda x: x.get("alch_val", 0), reverse=True)
        elif sort_mode == "Lowest Price":
            filtered.sort(key=lambda x: x.get("alch_val", 0) if ironman else x.get("price_val", 0))
        elif sort_mode == "Rarity (Common First)":
            filtered.sort(key=lambda x: x.get("probability", 0), reverse=True)

        if not filtered:
            ctk.CTkLabel(self.drops_scroll, text="No drops match the current filters.", text_color="#aaaaaa").pack(pady=20)
            return

        for d in filtered:
            row = ctk.CTkFrame(self.drops_scroll, fg_color="#333333", corner_radius=8)
            row.pack(fill="x", pady=4, padx=5)
            
            # Icon
            img_path = d.get("img_path")
            if img_path and os.path.exists(img_path):
                if d["item"] not in self.ctk_images:
                    pil_img = Image.open(img_path)
                    self.ctk_images[d["item"]] = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(32, 32))
                ctk.CTkLabel(row, text="", image=self.ctk_images[d["item"]]).pack(side="left", padx=10, pady=10)
            else:
                ctk.CTkLabel(row, text="🚫", width=32).pack(side="left", padx=10, pady=10)

            # Details
            details = ctk.CTkFrame(row, fg_color="transparent")
            details.pack(side="left", fill="both", expand=True, padx=10)
            ctk.CTkLabel(details, text=d["item"], font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(5, 0))
            ctk.CTkLabel(details, text=f"Qty: {d['quantity']}  •  Rarity: {d['rarity']}", text_color="#aaaaaa", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 5))

            # Sparkline for expensive items
            spark_path = d.get("spark_path")
            if spark_path and os.path.exists(spark_path) and not ironman:
                if f"spark_{d['item']}" not in self.ctk_images:
                    pil_spark = Image.open(spark_path)
                    self.ctk_images[f"spark_{d['item']}"] = ctk.CTkImage(light_image=pil_spark, dark_image=pil_spark, size=(150, 40))
                ctk.CTkLabel(row, text="", image=self.ctk_images[f"spark_{d['item']}"]).pack(side="left", padx=10)

            # Price
            price_val = d.get("price_val", 0)
            alch_val = d.get("alch_val", 0)
            if ironman:
                price_text = f"Alch: {format_number(alch_val)} gp" if alch_val > 0 else "Untradeable"
            else:
                price_text = f"{format_number(price_val)} gp"
                if alch_val > price_val:
                    price_text = f"🔥 {format_number(alch_val)} gp"
            
            ctk.CTkLabel(row, text=price_text, font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffcc00").pack(side="left", padx=20)
            ctk.CTkButton(row, text="+1", width=40, font=ctk.CTkFont(weight="bold"), command=lambda item=d: self.add_to_tracker(item)).pack(side="right", padx=10)

    def trigger_alert(self, item_name, price):
        if toaster:
            threading.Thread(target=toaster.show_toast, args=("Epic Drop!", f"You received {item_name} worth {format_number(price)} gp!", "icon.ico", 5), daemon=True).start()
        try: winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except: pass

    def add_to_tracker(self, drop_data, qty_add=1):
        name = drop_data["item"]
        ironman = self.ironman_var.get()
        price = drop_data.get("alch_val", 0) if ironman else max(drop_data.get("price_val", 0), drop_data.get("alch_val", 0))
        img_path = drop_data.get("img_path")
        
        sess = self.sessions[self.current_session]
        if name in sess: sess[name]["qty"] += qty_add
        else: sess[name] = {"qty": qty_add, "price": price, "img_path": img_path}
            
        meta = self.session_meta.get(self.current_session, {})
        if not meta.get("start_time"):
            meta["start_time"] = time.time()
            self.session_meta[self.current_session] = meta
            
        self.update_tracker_summary()
        self.save_session()

    def auto_add_drop_by_name(self, detected_name):
        for d in self.current_drops:
            if detected_name.lower() in d["item"].lower():
                self.add_to_tracker(d)
                self.status_label.configure(text=f"Auto-logged: {d['item']}", text_color="#55ffff")
                break

    def import_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not filepath: return
        try:
            added = 0
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    item_key = next((k for k in row.keys() if 'item' in k.lower() or 'name' in k.lower()), None)
                    qty_key = next((k for k in row.keys() if 'amount' in k.lower() or 'quantity' in k.lower()), None)
                    if item_key and qty_key:
                        name = row[item_key]
                        qty = int(row[qty_key])
                        matched_d = next((d for d in self.current_drops if name.lower() in d["item"].lower()), None)
                        if matched_d: self.add_to_tracker(matched_d, qty)
                        else:
                            sess = self.sessions[self.current_session]
                            if name in sess: sess[name]["qty"] += qty
                            else: sess[name] = {"qty": qty, "price": 0, "img_path": None}
                        added += 1
            self.update_tracker_summary()
            self.save_session()
            messagebox.showinfo("Import", f"Imported {added} items into '{self.current_session}'.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import: {e}")

    def update_gphr_display(self):
        self.update_tracker_summary()
        self.after(1000, self.update_gphr_display)

    def update_tracker_summary(self):
        sess = self.sessions.get(self.current_session, {})
        meta = self.session_meta.get(self.current_session, {})
        
        total_val = sum(item["qty"] * item["price"] for item in sess.values())
        self.tracker_total_label.configure(text=f"Total: {format_number(total_val)} gp")
        
        start_time = meta.get("start_time")
        if start_time and total_val > 0:
            elapsed_sec = time.time() - start_time
            if elapsed_sec > 0:
                gphr = total_val / (elapsed_sec / 3600)
                self.tracker_gphr_label.configure(text=f"GP/Hr: {format_number(int(gphr))} gp")
        else:
            self.tracker_gphr_label.configure(text="GP/Hr: 0 gp")

    def save_session(self):
        with open(SESSION_FILE, "w") as f: json.dump(self.sessions, f)
        with open(META_FILE, "w") as f: json.dump(self.session_meta, f)

    def load_session(self):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    data = json.load(f)
                if data:
                    self.sessions = data
                    self.current_session = list(self.sessions.keys())[0]
                    self.session_var.set(self.current_session)
                    options = list(self.sessions.keys()) + ["New Session..."]
                    self.session_menu.configure(values=options)
            except: pass
        if os.path.exists(META_FILE):
            try:
                with open(META_FILE, "r") as f: self.session_meta = json.load(f)
            except: pass
        self.update_tracker_summary()

    def open_tracker_window(self):
        win = ctk.CTkToplevel(self)
        win.title(f"Manage Session: {self.current_session}")
        win.geometry("500x650")
        win.attributes("-topmost", True)
        ctk.CTkLabel(win, text=f"Session: {self.current_session}", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        sess = self.sessions[self.current_session]
        for name, data in sess.items():
            r = ctk.CTkFrame(scroll, fg_color="#2b2b2b")
            r.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(r, text=f"{name}  x{data['qty']}", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(r, text=f"{format_number(data['qty'] * data['price'])} gp", text_color="#ffcc00").pack(side="right", padx=10)

        def reset_tracker():
            self.sessions[self.current_session].clear()
            self.session_meta[self.current_session] = {"start_time": None}
            self.update_tracker_summary()
            self.save_session()
            win.destroy()
            
        def export_png(): self.export_loot()
            
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="Close", command=win.destroy).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(btn_frame, text="Export PNG", fg_color="#0066cc", hover_color="#004c99", command=export_png).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(btn_frame, text="Clear Session", fg_color="#b33939", hover_color="#8b2727", command=reset_tracker).pack(side="right", padx=10, expand=True)
        
    def export_loot(self):
        sess = self.sessions[self.current_session]
        if not sess:
            messagebox.showwarning("Empty", "Nothing to export!")
            return
        try:
            row_h = 50
            total_items = len(sess)
            img = Image.new("RGB", (500, 100 + total_items * row_h), color="#1e1e1e")
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), f"RS3 Drops - {self.current_session}", fill="#ffffff")
            total_val = sum(item["qty"] * item["price"] for item in sess.values())
            draw.text((20, 45), f"Total Profit: {format_number(total_val)} gp", fill="#55ff55")
            
            y = 90
            for name, data in sess.items():
                if data["img_path"] and os.path.exists(data["img_path"]):
                    icon = Image.open(data["img_path"]).convert("RGBA")
                    img.paste(icon, (20, y), mask=icon)
                draw.text((70, y+8), f"{name} x{data['qty']}", fill="#ffffff")
                draw.text((350, y+8), f"{format_number(data['qty'] * data['price'])} gp", fill="#ffcc00")
                y += row_h
                
            img.save(f"export_{self.current_session}.png")
            messagebox.showinfo("Export Successful", f"Saved to 'export_{self.current_session}.png'!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export image: {e}")

    def toggle_auto_tracker(self):
        if self.auto_tracker_var.get():
            self.auto_tracker_thread = AutoTracker(self)
            self.auto_tracker_thread.start()
            self.status_label.configure(text="Auto-Tracker Started (Monitoring Chatbox)", text_color="#55ffff")
        else:
            self.stop_auto_tracker()
            
    def stop_auto_tracker(self):
        self.auto_tracker_var.set(False)
        if self.auto_tracker_thread:
            self.auto_tracker_thread.running = False
            self.auto_tracker_thread = None
        self.status_label.configure(text="Auto-Tracker Stopped.", text_color="#aaaaaa")

if __name__ == "__main__":
    app = RS3DropLookupApp()
    app.mainloop()
