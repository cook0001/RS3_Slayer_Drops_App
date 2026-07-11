# ⚔️ Slayer Drops (RS3)

Slayer Drops is an elite-tier drop tracker, expected profit calculator, and monster strategy guide for RuneScape 3. It features two distinct clients to fit your playstyle: a feature-rich **Standalone Desktop App** and a seamless **Alt1 Toolkit Web Overlay**.

## 🌟 Key Features

* **Live Market Data**: Instantly scrapes the official RS3 Wiki for accurate Grand Exchange prices, drop rates, and High Alchemy values.
* **GE Market Trend Sparklines**: Hooked into the Weird Gloop API to generate 90-day price trend graphs for items over 50,000 gp. Know whether to sell or hold!
* **Variance & Profit Predictor**: Employs binomial variance approximation to calculate a 95% confidence interval for expected profit on a given task size.
* **Jagex Hiscores Readiness Integration**: Enter your RSN, and the app will query the official Jagex Hiscores to compare your Slayer level against monster requirements.
* **Auto-Tracking**: 
  * *Desktop:* Uses PyTesseract & OpenCV to read the game screen and automatically add drops to your log.
  * *Alt1 Overlay:* Uses Alt1's native `@alt1/chatbox` JavaScript API for flawless, zero-overhead background chat reading.
* **Ironman Mode**: Shifts focus strictly to High Alchemy values and removes GE prices entirely.

---

## 🚀 Setup & Installation

### Option 1: Standalone Desktop App (Python)
If you prefer a standalone desktop window on your second monitor.
1. Install **Python 3.10+**.
2. Install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
*(Note: To use the Auto-Tracker feature on the desktop app, you must install the Tesseract-OCR binary on your system).*

### Option 2: Alt1 Toolkit Overlay (React / Vite)
If you prefer a transparent overlay seamlessly integrated into your game client via the Alt1 Toolkit.
1. Install **Node.js**.
2. Navigate to the `alt1_react` directory and install dependencies:
   ```bash
   cd alt1_react
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open the **Alt1 Toolkit**, go to `Browser`, and type in `http://localhost:5173`. Alternatively, point Alt1 directly to the `appconfig.json` inside the `alt1_web` legacy folder.

## 📦 Compiling to .exe
You can build the Python script into a single, shareable executable using PyInstaller:
```bash
pip install pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --icon="icon.ico" --add-data "icon.ico;." --name "SlayerDrops" app.py
```
The resulting standalone executable will be located in the `dist/` directory.

---
*Created for RuneScape 3. Not affiliated with Jagex.*
