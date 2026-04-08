"""
System tray icon using win32gui directly — no pystray needed.

Why win32gui? pystray has threading issues on Windows when tkinter
is also running. win32gui gives us direct access to the Windows shell
notification API, which is rock solid.

The icon changes color to reflect recording state:
  grey  → idle
  red   → recording
  blue  → transcribing
  orange → error
"""
import os
import tempfile
import threading

import win32api
import win32con
import win32gui
from PIL import Image, ImageDraw

from core.app_state import AppState, RecordingState

# Context menu item IDs
MENU_SETTINGS = 1023
MENU_QUIT     = 1024

# Windows message we use for tray icon events
WM_TRAY = win32con.WM_USER + 20

# Tray icon color per state
STATE_COLORS = {
    RecordingState.IDLE:         "#888888",  # grey — just sitting there
    RecordingState.RECORDING:    "#ff3b30",  # red — mic is live
    RecordingState.TRANSCRIBING: "#007aff",  # blue — waiting for transcript
    RecordingState.ERROR:        "#ff9500",  # orange — something went wrong
}


def _make_icon(color: str) -> Image.Image:
    """Draw a simple mic shape in the given color on a dark background."""
    img = Image.new("RGB", (64, 64), (30, 30, 30))
    d = ImageDraw.Draw(img)
    d.rectangle([22, 6, 42, 36], fill=color)   # mic body
    d.arc([14, 22, 50, 50], start=0, end=180, fill=color, width=4)  # stand arc
    d.line([32, 50, 32, 58], fill=color, width=4)  # pole
    d.line([22, 58, 42, 58], fill=color, width=4)  # base
    return img


def _to_hicon(img: Image.Image):
    """Convert a PIL image to a Windows HICON handle via a temp .ico file."""
    img = img.resize((32, 32), Image.LANCZOS).convert("RGBA")
    tmp = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
    tmp.close()
    img.save(tmp.name, format="ICO")
    hicon = win32gui.LoadImage(
        0, tmp.name, win32con.IMAGE_ICON, 0, 0,
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

        # Listen for state changes so we can update the icon color
        app_state.on_state_change(self._on_state_change)

    def run_in_thread(self):
        """Start the tray in a background thread (main thread belongs to tkinter)."""
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        # Register a minimal hidden window — needed to receive tray messages
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "VocalFlowTray"
        wc.lpfnWndProc = self._wnd_proc
        try:
            win32gui.RegisterClass(wc)
        except Exception:
            pass  # already registered if app was restarted quickly

        self._hwnd = win32gui.CreateWindow(
            "VocalFlowTray", "VocalFlow",
            0, 0, 0, 0, 0, 0, 0, wc.hInstance, None
        )

        self._hicon = _to_hicon(_make_icon(STATE_COLORS[RecordingState.IDLE]))
        self._notify(win32gui.NIM_ADD)

        # Pump Windows messages — this blocks until the app quits
        win32gui.PumpMessages()

    def _notify(self, action, hicon=None):
        """Add, modify, or remove the tray icon via Shell_NotifyIcon."""
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self._hwnd, 0, flags, WM_TRAY, hicon or self._hicon, "VocalFlow")
        win32gui.Shell_NotifyIcon(action, nid)

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """Handle Windows messages sent to our hidden window."""
        if msg == WM_TRAY and lparam in (win32con.WM_LBUTTONUP, win32con.WM_RBUTTONUP):
            self._show_menu()
        elif msg == win32con.WM_DESTROY:
            try:
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self._hwnd, 0))
            except Exception:
                pass
            win32gui.PostQuitMessage(0)
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _show_menu(self):
        """Show the right-click context menu at the cursor position."""
        menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(menu, win32con.MF_STRING,    MENU_SETTINGS, "Settings")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0,             "")
        win32gui.AppendMenu(menu, win32con.MF_STRING,    MENU_QUIT,     "Quit VocalFlow")

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
            try:
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self._hwnd, 0))
            except Exception:
                pass
            self._on_quit()

    def _on_state_change(self, state: RecordingState):
        """Swap the tray icon color whenever recording state changes."""
        if not self._hwnd:
            return
        self._hicon = _to_hicon(_make_icon(STATE_COLORS.get(state, STATE_COLORS[RecordingState.IDLE])))
        try:
            win32gui.Shell_NotifyIcon(
                win32gui.NIM_MODIFY,
                (self._hwnd, 0, win32gui.NIF_ICON, WM_TRAY, self._hicon, "VocalFlow")
            )
        except Exception:
            pass
