import { app, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { homedir } from 'os'
import { existsSync } from 'fs'
import { spawn } from 'child_process'
import { is } from '@electron-toolkit/utils'

let pythonBridge = null
let mainWindow = null

function createWindow() {
  const iconPath = app.isPackaged
    ? join(process.resourcesPath, 'icon.png')
    : join(__dirname, '../../build/icon.png')

  mainWindow = new BrowserWindow({
    width: 900,
    height: 680,
    minWidth: 800,
    minHeight: 600,
    title: 'newBits — ChromeOS Recovery',
    icon: existsSync(iconPath) ? iconPath : undefined,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

function startPythonBridge(usePkexec = false) {
  const bridgePath = app.isPackaged
    ? join(process.resourcesPath, 'app.asar.unpacked/python/bridge.py')
    : join(__dirname, '../../python/bridge.py')
  const args = usePkexec
    ? ['uv', 'run', '--script', bridgePath]
    : ['run', '--script', bridgePath]
  const cmd = usePkexec ? 'pkexec' : 'uv'

  const proc = spawn(cmd, args, { stdio: ['pipe', 'pipe', 'pipe'] })
  pythonBridge = proc

  let buffer = ''
  proc.stdout.on('data', (data) => {
    buffer += data.toString()
    const lines = buffer.split('\n')
    buffer = lines.pop()
    for (const line of lines) {
      if (!line.trim()) continue
      try {
        const event = JSON.parse(line)
        mainWindow?.webContents.send('bridge:event', event)
      } catch {
        console.error('Bridge parse error:', line)
      }
    }
  })

  proc.stderr.on('data', (data) => {
    const msg = data.toString().trim()
    console.error('Python stderr:', msg)
    mainWindow?.webContents.send('bridge:event', { type: 'log', level: 'error', msg })
  })

  proc.on('close', (code) => {
    if (pythonBridge !== proc) return  // killed intentionally during restart
    pythonBridge = null
    mainWindow?.webContents.send('bridge:closed', code)
  })
}

app.whenReady().then(() => {
  createWindow()

  ipcMain.handle('bridge:start', (_, usePkexec) => {
    if (pythonBridge) {
      pythonBridge.kill()
      pythonBridge = null
    }
    try {
      startPythonBridge(usePkexec)
      return { success: true }
    } catch (e) {
      return { success: false, error: e.message }
    }
  })

  ipcMain.handle('bridge:send', (_, command) => {
    if (!pythonBridge) return false
    pythonBridge.stdin.write(JSON.stringify(command) + '\n')
    return true
  })

  ipcMain.handle('app:workdir', () => {
    console.log('[workdir] app.isPackaged    :', app.isPackaged)
    console.log('[workdir] process.execPath  :', process.execPath)
    console.log('[workdir] APPIMAGE env      :', process.env.APPIMAGE)
    console.log('[workdir] HOME env          :', process.env.HOME)
    console.log('[workdir] homedir()         :', homedir())
    console.log('[workdir] app.getAppPath()  :', app.getAppPath())
    console.log('[workdir] app.userData      :', app.getPath('userData'))
    if (app.isPackaged) {
      const workdir = join(homedir(), '.local', 'share', 'newbits-gui', 'workdir')
      console.log('[workdir] resolved (pkg)    :', workdir)
      return workdir
    }
    const workdir = join(app.getAppPath(), 'newbits-workdir')
    console.log('[workdir] resolved (dev)    :', workdir)
    return workdir
  })

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (pythonBridge) {
    try { pythonBridge.kill() } catch { /* elevated bridge exits when stdin closes */ }
    pythonBridge = null
  }
  if (process.platform !== 'darwin') app.quit()
})
