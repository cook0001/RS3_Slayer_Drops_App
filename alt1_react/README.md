# ⚔️ Slayer Drops (Alt1 React Overlay)

This is the Alt1 Toolkit integration for the Slayer Drops application, rewritten in React + Vite for optimal performance and a seamless in-game overlay experience.

## 🚀 Live Version

The application is deployed automatically to GitHub Pages on our custom domain. The most reliable way to install it is directly through the Alt1 Toolkit:

1. Open **Alt1 Toolkit** on your computer.
2. Click the **Browser** button in the top toolbar.
3. Type `https://app.armstrader.store` into the address bar and press Enter.
4. Alt1 will automatically detect the app configuration and prompt you to "Add App". Click it!

*(Alternative: You can visit `https://app.armstrader.store` in Chrome/Edge and click the "Install to Alt1" button in the top right, provided your Windows `alt1://` protocol handler is working correctly.)*

---

### ⚠️ Troubleshooting Alt1 Installation (SPA Issues)
Because this tracker is built as a modern Single Page Application (SPA), Alt1's built-in browser sometimes gets confused and fails to render the "Add App" button automatically. If you are having trouble installing the app, follow these steps:

**Step 1: Use the Explicit Config Link**
Instead of the standard website address, you must give Alt1 the exact configuration manifest path.
1. Open the Alt1 Toolkit on your desktop.
2. Open Alt1's built-in **Browser**.
3. Paste this exact address into Alt1's top browser bar and hit Enter: 
   `https://app.armstrader.store/appconfig.json`
4. The yellow "Add App" banner should now forcefully appear at the top of your Alt1 screen.

**Step 2: Use the Direct Web-Add Protocol**
If pasting the `.json` string inside the browser fails, we can use Alt1's special installation protocol through your native Windows command prompt to force-inject it.
1. Right-click your Windows Start button and select **Run** (or press `Windows Key + R`).
2. Paste this exact string into the box: 
   `alt1://addapp/https://app.armstrader.store/appconfig.json`
3. Click OK. Alt1 should force-open a pop-up confirmation asking you to install the app.

**Step 3: Check Alt1's Hardware Acceleration**
If the screen still goes entirely white or doesn't react at all, your Alt1 internal Chromium build is failing to render the page due to hardware settings:
1. Open Alt1 **Settings** > **Other** tab.
2. Toggle the checkmark for **"Use GPU rendering (Hardware Acceleration)"** (if it's on, turn it off; if it's off, turn it on).
3. Completely restart Alt1 and try Step 1 again.

---

## 💻 Local Development Setup

1. **Install Dependencies:**
   ```bash
   npm install
   ```

2. **Start the Development Server:**
   ```bash
   npm run dev
   ```

3. **Load into Alt1:**
   - Open RuneScape 3 and the Alt1 Toolkit.
   - Click the "Browser" button in the Alt1 toolbar.
   - Enter `http://localhost:5173` into the address bar.
   - (Optional) Save it as a bookmark in Alt1 for quick access.

## 🛠️ Building for Production

If you want to manually build the static files:
```bash
npm run build
```
The compiled files will be in the `dist` directory, which can be hosted on any static web server.
