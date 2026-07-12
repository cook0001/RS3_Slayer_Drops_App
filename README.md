# ⚔️ Slayer Drops (RS3)

Slayer Drops is an elite-tier drop tracker, expected profit calculator, and monster strategy guide for RuneScape 3. It features two distinct clients to fit your playstyle: a feature-rich **Standalone Desktop App** and a seamless **Alt1 Toolkit Web Overlay**.

## 🌟 Key Features

* **Live Market Data**: Instantly scrapes the official RS3 Wiki for accurate Grand Exchange prices, drop rates, and High Alchemy values.
* **GE Market Trend Sparklines**: Hooked into the Weird Gloop API to generate 90-day price trend graphs for items over 50,000 gp. Know whether to sell or hold!
* **Variance & Profit Predictor**: Employs binomial variance approximation to calculate a 95% confidence interval for expected profit on a given task size.
* **Jagex Hiscores Readiness Integration**: Enter your RSN, and the app will query the official Jagex Hiscores to compare your Slayer level against monster requirements.
* **Auto-Tracking (Cross-Platform)**: 
  * *Desktop:* Uses PyTesseract & OpenCV to read the game screen and automatically add drops to your log. Works on Windows, macOS, and Linux!
  * *Alt1 Overlay:* Uses Alt1's native `@alt1/chatbox` JavaScript API for flawless, zero-overhead background chat reading.
* **Ironman Mode**: Shifts focus strictly to High Alchemy values and removes GE prices entirely.
* **Alt1 Overlay Exclusives**: 
  * Premium Glassmorphism UI with dark mode support.
  * LocalStorage Session Persistence—never lose your tracked drops if you close the app!
  * Smart Search Auto-complete directly linked to the Wiki API.

---

## 📥 Download (Pre-Compiled Releases)
Don't want to mess with Python or Node.js? No problem! 

This repository is equipped with a **fully automated CI/CD pipeline**. Every time a new version is pushed, our GitHub Actions workflow automatically compiles pristine, standalone applications for **Windows, macOS, and Linux**. 

You can instantly download the latest, ready-to-run versions directly from the **[Releases Tab](https://github.com/cook0001/RS3_Slayer_Drops_App/releases)**.

---

## 🚀 Setup & Installation (For Developers)

### Option 1: Standalone Desktop App (Python)
If you prefer a standalone desktop window on your second monitor. Fully supported on Windows, macOS, and Linux.
1. Install **Python 3.10+**.
2. Install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```
3. **Optional Auto-Tracker Requirements**:
   To use the screen-reading Auto-Tracker, you must have Tesseract OCR installed on your system:
   * **Windows:** Install the Tesseract binary (`C:\Program Files\Tesseract-OCR\tesseract.exe`).
   * **macOS:** `brew install tesseract`
   * **Linux:** `sudo apt install tesseract-ocr`
4. Run the application:
   ```bash
   python app.py
   ```

### Option 2: Alt1 Toolkit Overlay (React / Vite)
If you prefer a transparent overlay seamlessly integrated into your game client via the Alt1 Toolkit.

**🌍 Live Version (Recommended):**
The Alt1 application is now hosted on a custom domain! You can install it into Alt1 Toolkit with a single click using the link below:

**[➕ One-Click Install to Alt1 Toolkit](alt1://addapp/https://app.armstrader.store/appconfig.json)**

*(Alternatively, you can just type `https://app.armstrader.store` into your normal web browser and click the "Install to Alt1" button!)*

**💻 Running Locally (For Developers):**
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
4. Open the **Alt1 Toolkit**, go to `Browser`, and type in `http://localhost:5173`.

## 📦 Compiling to Standalone Executable
You can build the Python script into a single, shareable executable using PyInstaller. 

**Windows:**
```bash
pip install pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --icon="icon.ico" --add-data "icon.ico;." --name "SlayerDrops" app.py
```
**macOS / Linux:**
```bash
pip install pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --icon="icon.ico" --add-data "icon.ico:." --name "SlayerDrops" app.py
```
*(Note: macOS/Linux use a colon `:` separator for `--add-data` instead of a semicolon `;`).*

The resulting standalone executable will be located in the `dist/` directory. On Mac, it will generate a `.app` bundle.

---
*Created for RuneScape 3. Not affiliated with Jagex.*
