// Bagues musicales — enveloppe Electron de la webapp (version démo libre)
const { app, BrowserWindow, ipcMain, shell } = require("electron");
const path = require("path");

if (process.platform === "linux") app.commandLine.appendSwitch("enable-experimental-web-platform-features");

let win = null;
let pendingBleCallback = null;

function createWindow() {
  win = new BrowserWindow({
    width: 1280, height: 820, minWidth: 760, minHeight: 520,
    backgroundColor: "#0b0716", title: "Bagues musicales", autoHideMenuBar: true,
    webPreferences: { preload: path.join(__dirname, "preload.js"), contextIsolation: true, nodeIntegration: false },
  });

  // Web Bluetooth : Electron n'a pas de sélecteur intégré -> on transmet la liste à l'interface
  win.webContents.on("select-bluetooth-device", (event, devices, callback) => {
    event.preventDefault();
    pendingBleCallback = callback;
    win.webContents.send("ble-devices", devices.map(d => ({ deviceId: d.deviceId, deviceName: d.deviceName })));
  });

  // liens externes (code source…) dans le navigateur par défaut
  win.webContents.setWindowOpenHandler(({ url }) => { shell.openExternal(url); return { action: "deny" }; });
  win.webContents.on("will-navigate", (e, url) => { if (!url.startsWith("file:")) { e.preventDefault(); shell.openExternal(url); } });

  win.loadFile(path.join(__dirname, "app", "index.html"));
}

ipcMain.on("ble-select", (_e, deviceId) => {
  if (pendingBleCallback) { pendingBleCallback(deviceId || ""); pendingBleCallback = null; }
});

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
