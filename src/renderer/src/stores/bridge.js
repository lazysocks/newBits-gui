import { reactive } from 'vue'

export const store = reactive({
  connected: false,
  logs: [],
  progress: { current: 0, total: 0, desc: '' }
})

let pendingResolve = null
let pendingReject = null

let bridgeReadyResolve
let bridgeReadyPromise = new Promise(resolve => { bridgeReadyResolve = resolve })

export function initBridge(usePkexec = false) {
  window.api.onBridgeEvent((event) => {
    if (event.type === 'log') {
      store.logs.push({ ...event, timestamp: Date.now() })
    } else if (event.type === 'progress') {
      store.progress = { current: event.current, total: event.total, desc: event.desc || '' }
    } else if (event.type === 'result') {
      if (pendingResolve) {
        const res = pendingResolve
        pendingResolve = null
        pendingReject = null
        res(event.data)
      }
    } else if (event.type === 'error') {
      if (pendingReject) {
        const rej = pendingReject
        pendingResolve = null
        pendingReject = null
        rej(new Error(event.msg))
      }
    }
  })

  window.api.onBridgeClosed((code) => {
    store.connected = false
    if (pendingReject) {
      pendingReject(new Error(`Bridge exited with code ${code}`))
      pendingResolve = null
      pendingReject = null
    }
  })

  return window.api.startBridge(usePkexec).then((res) => {
    if (res.success) {
      store.connected = true
      bridgeReadyResolve()
    } else {
      throw new Error(res.error)
    }
  })
}

export function restartBridge(usePkexec = false) {
  bridgeReadyPromise = new Promise(resolve => { bridgeReadyResolve = resolve })
  window.api.removeAllBridgeListeners()
  return initBridge(usePkexec)
}

export async function sendCommand(cmd) {
  await bridgeReadyPromise
  store.progress = { current: 0, total: 0, desc: '' }
  return new Promise((resolve, reject) => {
    pendingResolve = resolve
    pendingReject = reject
    window.api.sendCommand(cmd)
  })
}
