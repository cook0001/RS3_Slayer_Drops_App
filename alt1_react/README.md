# ⚔️ Slayer Drops (Alt1 React Overlay)

This is the Alt1 Toolkit integration for the Slayer Drops application, rewritten in React + Vite for optimal performance and a seamless in-game overlay experience.

## 🚀 Live Version

The application is deployed automatically to GitHub Pages on our custom domain. The most reliable way to install it is directly through the Alt1 Toolkit:

1. Open **Alt1 Toolkit** on your computer.
2. Click the **Browser** button in the top toolbar.
3. Type `https://app.armstrader.store` into the address bar and press Enter.
4. Alt1 will automatically detect the app configuration and prompt you to "Add App". Click it!

*(Alternative: You can visit `https://app.armstrader.store` in Chrome/Edge and click the "Install to Alt1" button in the top right, provided your Windows `alt1://` protocol handler is working correctly.)*

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
