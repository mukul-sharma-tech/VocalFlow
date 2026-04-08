"""
Floating waveform overlay shown at the bottom-center of the screen while recording.
Draws smooth rounded capsule bars with a gradient glow — elegant and professional.
Runs in its own thread with its own tkinter event loop (required on Windows).
"""
import math
import threading
import tkinter as tk

from core.app_state import OVERLAY_THEMES

# Overlay dimensions
W, H = 180, 64

class OverlayWindow:
    def __init__(self, app_state, audio_engine=None):
        self._app_state    = app_state
        self._audio_engine = audio_engine  # used for voice-reactive bars
        self._root = None
        self._canvas = None
        self._visible = False
        self._anim_step = 0
        self._anim_job = None
        
        # Store canvas item IDs to update them (zero CPU usage trick)
        self._bg_id = None
        self._glow_ids = []
        self._bar_ids = []
        
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.0)
        self._root.attributes("-transparentcolor", "#000001")  # punch-through bg
        self._root.configure(bg="#000001")
        self._root.geometry(f"{W}x{H}")
        self._root.resizable(False, False)

        self._canvas = tk.Canvas(
            self._root, width=W, height=H,
            bg="#000001", highlightthickness=0
        )
        self._canvas.pack()
        
        # Pre-build the canvas items once
        self._build_items()
        
        self._position()
        self._root.mainloop()

    def _build_items(self):
        """Creates perfectly curvy capsule shapes once using capstyle=tk.ROUND."""
        bars = 11
        bar_w = 8
        cy = H // 2
        
        # Background pill
        self._bg_id = self._canvas.create_line(
            20, cy, W - 20, cy,
            width=H - 16, capstyle=tk.ROUND, fill="#1a1a2e"
        )
        
        # Create the glow and main bars (hidden at 0 height initially)
        for _ in range(bars):
            glow = self._canvas.create_line(0, 0, 0, 0, width=bar_w + 4, capstyle=tk.ROUND)
            main = self._canvas.create_line(0, 0, 0, 0, width=bar_w, capstyle=tk.ROUND)
            self._glow_ids.append(glow)
            self._bar_ids.append(main)

    def _position(self):
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        # Changed from sh - 110 to sh - 160 to shift the overlay up
        self._root.geometry(f"{W}x{H}+{(sw - W) // 2}+{sh - 160}")

    def show(self):
        if self._root:
            self._root.after(0, self._do_show)

    def hide(self):
        if self._root:
            self._root.after(0, self._do_hide)

    def _do_show(self):
        self._visible = True
        self._anim_step = 0
        self._root.attributes("-alpha", 0.92)
        self._animate()

    def _do_hide(self):
        self._visible = False
        if self._anim_job:
            self._root.after_cancel(self._anim_job)
            self._anim_job = None
        self._root.attributes("-alpha", 0.0)
        
        # Reset bars to flat when hidden
        cy = H // 2
        for i in range(11):
            self._canvas.coords(self._glow_ids[i], 0, cy, 0, cy)
            self._canvas.coords(self._bar_ids[i], 0, cy, 0, cy)

    def _animate(self):
        if not self._visible:
            return

        palette = OVERLAY_THEMES.get(
            self._app_state.selected_overlay_theme,
            OVERLAY_THEMES["Vibrant Blue"]
        )

        bars = 11
        bar_w = 8
        gap = 7
        cx = W // 2
        cy = H // 2
        t = self._anim_step

        for i in range(bars):
            x = cx - (bars // 2) * (bar_w + gap) + i * (bar_w + gap)

            # Get live mic volume (0.0 = silence, 1.0 = loud)
            rms = getattr(self._audio_engine, "rms_level", 0.0) if self._audio_engine else 0.0

            # Idle wave always runs so bars never look frozen
            idle = math.sin(t * 0.4 + i * 0.5) * 0.5 + 0.5  # 0.0–1.0

            # Voice boost: each bar gets a slightly different phase for organic look
            voice_phase = math.sin(t * 0.6 + i * 0.7) * 0.5 + 0.5
            voice = rms * voice_phase

            # Combine idle + voice, apply bell curve (center bars taller)
            center_boost = 1.0 - abs(i - bars // 2) / (bars // 2) * 0.4
            h = int((4 + 8 * idle + 20 * voice) * center_boost)
            h = max(h, 2)

            # Fast color shifting math
            t_color = (math.sin(t * 0.25 + i * 0.5) + 1) / 2
            t_scaled = t_color * (len(palette) - 1)
            idx  = int(t_scaled)
            frac = t_scaled - idx
            c0 = palette[min(idx,     len(palette) - 1)]
            c1 = palette[min(idx + 1, len(palette) - 1)]
            r = int(c0[0] + frac * (c1[0] - c0[0]))
            g = int(c0[1] + frac * (c1[1] - c0[1]))
            b = int(c0[2] + frac * (c1[2] - c0[2]))
            color = f"#{r:02x}{g:02x}{b:02x}"

            # Glow color calculation
            glow_r = max(0, r - 40)
            glow_g = max(0, g - 40)
            glow_b = max(0, b - 40)
            glow_color = f"#{glow_r:02x}{glow_g:02x}{glow_b:02x}"
            
            # Update existing items (buttery smooth and curvy)
            self._canvas.coords(self._glow_ids[i], x, cy - h - 1, x, cy + h + 1)
            self._canvas.itemconfig(self._glow_ids[i], fill=glow_color)

            self._canvas.coords(self._bar_ids[i], x, cy - h, x, cy + h)
            self._canvas.itemconfig(self._bar_ids[i], fill=color)

        self._anim_step += 1
        self._anim_job = self._root.after(20, self._animate)  # ~50fps