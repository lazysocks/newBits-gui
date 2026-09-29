import { contextBridge, ipcRenderer } from 'electron'

const api = {
  startBridge: (usePkexec = false) => ipcRenderer.invoke('bridge:start', usePkexec),
  sendCommand: (command) => ipcRenderer.invoke('bridge:send', command),
  getWorkdir: () => ipcRenderer.invoke('app:workdir'),
  onBridgeEvent: (callback) => {
    ipcRenderer.on('bridge:event', (_, event) => callback(event))
  },
  onBridgeClosed: (callback) => {
    ipcRenderer.on('bridge:closed', (_, code) => callback(code))
  },
  removeAllBridgeListeners: () => {
    ipcRenderer.removeAllListeners('bridge:event')
    ipcRenderer.removeAllListeners('bridge:closed')
  }
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('api', api)
  } catch (e) {
    console.error(e)
  }
} else {
  window.api = api
}
