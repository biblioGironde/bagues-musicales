const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("electronBLE", {
  onDevices: cb => ipcRenderer.on("ble-devices", (_e, list) => cb(list)),
  select: deviceId => ipcRenderer.send("ble-select", deviceId),
});
