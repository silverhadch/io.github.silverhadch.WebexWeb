'use strict';

const {
    app,
    BrowserWindow,
    Tray,
    Menu,
    session,
    desktopCapturer,
} = require('electron');
const path = require('path');
const fs   = require('fs');

if (!app.requestSingleInstanceLock()) {
    app.quit();
    process.exit(0);
}

const WEBEX_URL  = 'https://web.webex.com';
const ICON_PNG   = '/app/share/icons/hicolor/256x256/apps/io.github.silverhadch.WebexWeb.png';
const STATE_FILE = path.join(app.getPath('userData'), 'window-state.json');

let win  = null;
let tray = null;

app.setDesktopName('io.github.silverhadch.WebexWeb.desktop');

function loadState() {
    try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); }
    catch { return { width: 1280, height: 860 }; }
}

function saveState() {
    if (!win || win.isMinimized() || win.isMaximized()) return;
    const [width, height] = win.getSize();
    const [x, y]          = win.getPosition();
    try { fs.writeFileSync(STATE_FILE, JSON.stringify({ width, height, x, y })); }
    catch { /* well... */ }
}

function quit() {
    saveState();
    if (tray) {
        tray.destroy();
        tray = null;
    }
    // Nuke every open window
    BrowserWindow.getAllWindows().forEach(w => w.destroy());
    app.exit(0);
}

function createWindow() {
    const state = loadState();

    win = new BrowserWindow({
        width:  state.width,
        height: state.height,
        ...(state.x != null ? { x: state.x, y: state.y } : {}),
                            icon:            ICON_PNG,
                            title:           'Webex Web',
                            autoHideMenuBar: true,
                            webPreferences: {
                                nodeIntegration:  false,
                                contextIsolation: true,
                                partition:        'persist:webex',
                            },
    });

    // Gaslight Webex
    win.webContents.setUserAgent(
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
    );

    win.loadURL(WEBEX_URL);

    win.on('resize', saveState);
    win.on('move',   saveState);

    win.on('close', (e) => {
        if (tray !== null) {
            e.preventDefault();
            saveState();
            win.hide();
        }
    });

    win.on('closed', () => { win = null; });

    win.webContents.setWindowOpenHandler(() => ({
        action: 'allow',
        overrideBrowserWindowOptions: {
            width: 1000, height: 700,
            icon:            ICON_PNG,
            autoHideMenuBar: true,
            webPreferences: {
                nodeIntegration:  false,
                contextIsolation: true,
                partition:        'persist:webex',
            },
        },
    }));
}

function createTray() {
    tray = new Tray(ICON_PNG);
    tray.setToolTip('Webex Web');
    tray.setContextMenu(Menu.buildFromTemplate([
        {
            label: 'Show / Hide',
            click: () => {
                if (win?.isVisible() && !win?.isMinimized()) { win.hide(); }
                else { win?.show(); win?.focus(); }
            },
        },
        { type: 'separator' },
        { label: 'Quit', click: quit },
    ]));
    tray.on('click', () => {
        if (win?.isVisible() && !win?.isMinimized()) { win.hide(); }
        else { win?.show(); win?.focus(); }
    });
}

// We want all windows and screens, not just screens like in QtWebEngine-based Version 1.0
function registerDisplayMediaHandler() {
    session.fromPartition('persist:webex').setDisplayMediaRequestHandler(
        async (_request, callback) => {
            try {
                const sources = await desktopCapturer.getSources({ types: ['screen', 'window'] });
                if (sources.length === 0) { callback({ video: null, audio: null }); return; }
                callback({ video: sources[0] });
            } catch (err) {
                console.error('displayMedia handler error:', err);
                callback({ video: null, audio: null });
            }
        },
        { useSystemPicker: true },
    );
}

function allowPermissions() {
    session.fromPartition('persist:webex').setPermissionRequestHandler(
        (_webContents, permission, callback) => {
            callback(['notifications', 'media', 'display-capture'].includes(permission));
        },
    );
}

app.on('second-instance', () => {
    if (win) {
        if (win.isMinimized()) win.restore();
        win.show();
        win.focus();
    }
});

app.whenReady().then(() => {
    registerDisplayMediaHandler();
    allowPermissions();
    createWindow();
    createTray();
});

app.on('window-all-closed', () => { /* keeps us alive intentionally */ });
