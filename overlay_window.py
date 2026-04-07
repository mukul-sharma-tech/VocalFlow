import tkinter as tk
import threading
import math


class OverlayWindow:
    """Floating waveform-style indicator shown while recording."""

    def __init__(self):
        self._root: tk.Tk | None = None
        self._visible = False
        self._anim_step = 0
        self._anim_job = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        self._root = tk.Tk()
        self._root.overrideredirect(True)          # no title bar
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.0)
        self._root.configure(bg="#1e1e1e")
        self._root.geometry("140x52")
        self._root.resizable(False, False)

        self._canvas = tk.Canvas(
            self._root, width=140, height=52,
            bg="#1e1e1e", highlightthickness=0
        )
        self._canvas.pack()
        self._position()
        self._root.mainloop()

    def _position(self):
        if not self._root:
            return
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x = (sw - 140) // 2
        y = sh - 100  # near taskbar
        self._root.geometry(f"140x52+{x}+{y}")

    def show(self):
        if self._root:
            self._root.after(0, self._do_show)

    def hide(self):
        if self._root:
            self._root.after(0, self._do_hide)

    def _do_show(self):
        self._visible = True
        self._root.attributes("-alpha", 1.0)
        self._animate()

    def _do_hide(self):
        self._visible = False
        if self._anim_job:
            self._root.after_cancel(self._anim_job)
            self._anim_job = None
        self._root.attributes("-alpha", 0.0)
        self._canvas.delete("all")

    def _animate(self):
        if not self._visible:
            return
        self._canvas.delete("all")
        cx, cy = 70, 26
        bars = 9
        bar_w = 6
        spacing = 10
        for i in range(bars):
            x = cx - (bars // 2) * spacing + i * spacing
            phase = self._anim_step * 0.3 + i * 0.7
            h = int(8 + 14 * abs(math.sin(phase)))
            self._canvas.create_rectangle(
                x - bar_w // 2, cy - h,
                x + bar_w // 2, cy + h,
                fill="#ff3b30", outline=""
            )
        self._anim_step += 1
        self._anim_job = self._root.after(60, self._animate)
