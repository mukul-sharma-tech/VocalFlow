"""
System tray icon using win32api/win32gui directly.
This is the most reliable approach on Windows — no pystray needed.
"""
import os
import sys
import threading
import struct
import ctypes
from ctypes import wintypes
import win32api
import win32con
import win32gui
from PIL import Image, ImageDraw
from app_state import AppState, RecordingState

# Menu item IDs
MENU_SETTINGS = 1023
MENU_QUIT     = 1024

# Custom window message for tray events
WM_TRAY = win32con.WM_USER + 20


def _make_icon_image(color: str) -> Image.Image:
    img = Image.new("RGB", (64, 64), (30, 30, 30))
    d = ImageDraw.Draw(img)
    d.rectangle([22, 6, 42, 36], fill=color)
    d.arc([14, 22, 50, 50], start=0, end=180, fill=color, width=4)
    d.line([32, 50, 32, 58], fill=color, width=4)
    d.line([22, 58, 42, 58], fill=color, width=4)
    return img


STATE_COLORS = {
    RecordingState.IDLE:         "#888888",
    RecordingState.RECORDING:    "#ff3b30",
    RecordingState.TRANSCRIBING: "#007aff",
    RecordingState.ERROR:        "#ff9500",
}


def _image_to_hicon(img: Image.Image):
    """Convert PIL image to a Windows HICON handle."""
    img = img.resize((32, 32), Image.LANCZOS).convert("RGBA")
    # Save to temp .ico and load via win32gui
    import tempfile
    tmp = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
    tmp.close()
    img.save(tmp.name, format="ICO")
    hicon = win32gui.LoadImage(
        0, tmp.name,
        win32con.IMAGE_ICON,
        0, 0,
        win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
    )
    os.unlink(tmp.name)
    return hicon


class TrayController:
    def __init__(self, app_state: AppState, on_settings, on_quit):
        self._app_state = app_state
        self._on_settings = on_settings
        self._on_quit = on_quit
        self._hwnd = None
        self._hicon = None
        app_state.on_state_change(self._on_state_change)

    def run_in_thread(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def _run(self):
        # Register a window class
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "VocalFlowTray"
        wc.lpfnWndProc = self._wnd_proc
        try:
            win32gui.RegisterClass(wc)
        except Exception:
            pass  # already registered on restart

        self._hwnd = win32gui.CreateWindow(
            "VocalFlowTray", "VocalFlow",
            0, 0, 0, 0, 0,
            0, 0, wc.hInstance, None
        )

        self._hicon = _image_to_hicon(_make_icon_image(STATE_COLORS[RecordingState.IDLE]))
        self._add_tray_icon()
        print("Tray icon added.")

        # Message pump
        win32gui.PumpMessages()

    def _add_tray_icon(self):
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self._hwnd, 0, flags, WM_TRAY, self._hicon, "VocalFlow")
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)

    def _update_tray_icon(self, hicon):
        flags = win32gui.NIF_ICON
        nid = (self._hwnd, 0, flags, WM_TRAY, hicon, "VocalFlow")
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)

    def _remove_tray_icon(self):
        try:
            nid = (self._hwnd, 0)
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        except Exception:
            pass

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAY:
            if lparam == win32con.WM_RBUTTONUP or lparam == win32con.WM_LBUTTONUP:
                self._show_menu()
        elif msg == win32con.WM_DESTROY:
            self._remove_tray_icon()
            win32gui.PostQuitMessage(0)
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _show_menu(self):
        menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(menu, win32con.MF_STRING, MENU_SETTINGS, "Settings")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        win32gui.AppendMenu(menu, win32con.MF_STRING, MENU_QUIT, "Quit VocalFlow")

        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self._hwnd)
        cmd = win32gui.TrackPopupMenu(
            menu,
            win32con.TPM_LEFTALIGN | win32con.TPM_RETURNCMD | win32con.TPM_NONOTIFY,
            pos[0], pos[1], 0, self._hwnd, None
        )
        win32gui.PostMessage(self._hwnd, win32con.WM_NULL, 0, 0)

        if cmd == MENU_SETTINGS:
            self._on_settings()
        elif cmd == MENU_QUIT:
            self._remove_tray_icon()
            self._on_quit()

    def _on_state_change(self, state: RecordingState):
        if self._hwnd is None:
            return
        color = STATE_COLORS.get(state, STATE_COLORS[RecordingState.IDLE])
        new_hicon = _image_to_hicon(_make_icon_image(color))
        # Post to tray thread's message loop
        win32gui.PostMessage(self._hwnd, win32con.WM_USER + 21, 0, 0)
        self._hicon = new_hicon
        try:
            self._update_tray_icon(new_hicon)
        except Exception:
            pass
