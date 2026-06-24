#!/usr/bin/env python3

import os
import sys

_flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
for f in (
    "--enable-features=WebRTCPipeWireCapturer",
    "--autoplay-policy=no-user-gesture-required",
):
    if f.split("=")[0] not in _flags:
        _flags = (_flags + " " + f).strip()
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = _flags

from PyQt6.QtCore import QSettings, QStandardPaths, QUrl, Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QSystemTrayIcon,
)
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEnginePage,
    QWebEngineSettings,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

APP_ID = "io.github.silverhadch.WebexWeb"
APP_NAME = "Webex Web"
START_URL = "https://web.webex.com"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


class WebexPage(QWebEnginePage):

    def __init__(self, profile: QWebEngineProfile, parent=None):
        super().__init__(profile, parent)
        self._wire_permissions()

    def _wire_permissions(self):
        if hasattr(self, "permissionRequested"):
            self.permissionRequested.connect(self._on_permission)
        else:
            self.featurePermissionRequested.connect(self._on_feature)

    def _on_permission(self, permission):  # new API
        from PyQt6.QtWebEngineCore import QWebEnginePermission

        pt = QWebEnginePermission.PermissionType
        allow = {
            pt.MediaAudioCapture,
            pt.MediaVideoCapture,
            pt.MediaAudioVideoCapture,
            pt.DesktopVideoCapture,
            pt.DesktopAudioVideoCapture,
            pt.Notifications,
        }
        if permission.permissionType() in allow:
            permission.grant()
        else:
            permission.deny()

    def _on_feature(self, origin, feature):
        F = QWebEnginePage.Feature
        allow = {
            F.MediaAudioCapture,
            F.MediaVideoCapture,
            F.MediaAudioVideoCapture,
            F.DesktopVideoCapture,
            F.DesktopAudioVideoCapture,
            F.Notifications,
        }
        policy = (
            QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            if feature in allow
            else QWebEnginePage.PermissionPolicy.PermissionDeniedByUser
        )
        self.setFeaturePermission(origin, feature, policy)

    def createWindow(self, _type):
        popup = PopupWindow(self.profile())
        popup.resize(1000, 700)
        popup.show()
        return popup.view.page()


class PopupWindow(QMainWindow):

    _open = []

    def __init__(self, profile: QWebEngineProfile):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.view = QWebEngineView(self)
        self.view.setPage(WebexPage(profile, self.view))
        self.setCentralWidget(self.view)
        self.view.page().windowCloseRequested.connect(self.close)
        PopupWindow._open.append(self)

    def closeEvent(self, e):
        if self in PopupWindow._open:
            PopupWindow._open.remove(self)
        super().closeEvent(e)


class MainWindow(QMainWindow):
    def __init__(self, profile: QWebEngineProfile):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon.fromTheme(APP_ID))

        self.view = QWebEngineView(self)
        self.view.setPage(WebexPage(profile, self.view))
        self.setCentralWidget(self.view)

        self._restore_geometry()
        self._build_tray()
        self.view.load(QUrl(START_URL))

    def _build_tray(self):
        self.tray = QSystemTrayIcon(self)
        icon = QIcon.fromTheme(APP_ID)
        if icon.isNull():
            icon = self.style().standardIcon(
                self.style().StandardPixmap.SP_ComputerIcon
            )
        self.tray.setIcon(icon)
        self.tray.setToolTip(APP_NAME)

        menu = QMenu()
        show = QAction("Show / Hide", self)
        show.triggered.connect(self._toggle)
        quit_ = QAction("Quit", self)
        quit_.triggered.connect(self._quit)
        menu.addAction(show)
        menu.addSeparator()
        menu.addAction(quit_)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle()

    def _toggle(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def _quit(self):
        self._save_geometry()
        QApplication.quit()

    def _restore_geometry(self):
        s = QSettings(APP_ID, APP_ID)
        geo = s.value("geometry")
        if geo is not None:
            self.restoreGeometry(geo)
        else:
            self.resize(1280, 860)

    def _save_geometry(self):
        s = QSettings(APP_ID, APP_ID)
        s.setValue("geometry", self.saveGeometry())

    def closeEvent(self, e):
        if self.tray.isVisible():
            self._save_geometry()
            e.ignore()
            self.hide()
        else:
            self._save_geometry()
            e.accept()


def _setup_profile(app) -> QWebEngineProfile:
    data = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    )
    profile = QWebEngineProfile("webexweb", app)
    profile.setHttpUserAgent(USER_AGENT)
    profile.setPersistentCookiesPolicy(
        QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
    )
    if data:
        os.makedirs(data, exist_ok=True)
        profile.setPersistentStoragePath(os.path.join(data, "storage"))
        profile.setCachePath(os.path.join(data, "cache"))

    s = profile.settings()
    s.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
    s.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
    s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
    s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)

    profile.downloadRequested.connect(lambda d: d.accept())

    def present(notification):
        win = app.activeWindow()
        tray = getattr(MainWindow, "_singleton_tray", None)
        if tray is not None:
            tray.showMessage(
                notification.title(),
                notification.message(),
                QSystemTrayIcon.MessageIcon.Information,
                5000,
            )
        notification.show()

    profile.setNotificationPresenter(present)
    return profile


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setDesktopFileName(APP_ID)
    app.setQuitOnLastWindowClosed(False)

    profile = _setup_profile(app)
    win = MainWindow(profile)
    MainWindow._singleton_tray = win.tray
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
