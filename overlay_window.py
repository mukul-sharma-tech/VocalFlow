"""
Floating waveform overlay shown at the bottom-center of the screen while recording.
Runs in its own thread with its own tkinter event loop (required on Windows).
The bars animate with a wavy gradient using the user's selected color theme.
"""
import math
import threading
import tkinter as tk

from app_state import OVERLAY_THEMES


class OverlayWindow:
    def __init__(self, app_state):
        self._app_state = app_state
        self._root = None
        self._canvas = None
        self._visible = False
        self._anim_step = 0
        self._anim_job = None

        # Run tkinter in its own thread so it doesn't block the main loop
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self._root = tk.Tk()
        self._root.overrideredirect(True)          # no title bar or borders
        self._root.attributes("-topmost", True)    # always on top
        self._root.attributes("-alpha", 0.0)       # start invisible
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
        """Center horizontally, sit just above the taskbar."""
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        self._root.geometry(f"140x52+{(sw - 140) // 2}+{sh - 100}")

    def show(self):
        if self._root:
            self._root.after(0, self._do_show)

    def hide(self):
        if self._root:
            self._root.after(0, self._do_hide)

    def _do_show(self):
        self._visible = True
        self._anim_step = 0
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

        cx, cy   = 70, 26
        bars     = 9
        bar_w    = 6
        spacing  = 10

        # Get the current theme's color palette
        palette = OVERLAY_THEMES.get(
            self._app_state.selected_overlay_theme,
            OVERLAY_THEMES["Vibrant Blue"]
        )

        for i in range(bars):
            x = cx - (bars // 2) * spacing + i * spacing

            # Each bar has a different height based on a sine wave
            phase = self._anim_step * 0.3 + i * 0.7
            h = int(8 + 14 * abs(math.sin(phase)))

            # Each bar also cycles through the palette at a different phase
            t = (math.sin(self._anim_step * 0.12 + i * 0.6) + 1) / 2  # 0.0 → 1.0
            t_scaled = t * (len(palette) - 1)
            idx  = int(t_scaled)
            frac = t_scaled - idx
            c0 = palette[min(idx,     len(palette) - 1)]
            c1 = palette[min(idx + 1, len(palette) - 1)]

            # Linearly interpolate between the two nearest palette stops
            r = int(c0[0] + frac * (c1[0] - c0[0]))
            g = int(c0[1] + frac * (c1[1] - c0[1]))
            b = int(c0[2] + frac * (c1[2] - c0[2]))

            self._canvas.create_rectangle(
                x - bar_w // 2, cy - h,
                x + bar_w // 2, cy + h,
                fill=f"#{r:02x}{g:02x}{b:02x}", outline=""
            )

        self._anim_step += 1
        self._anim_job = self._root.after(60, self._animate)  # ~16fps
