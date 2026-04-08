import tkinter as tk
import webbrowser

# Enable Windows DPI Awareness for crisp text and accurate scaling
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# Windows 11 Fluent Design Palette (Light Theme)
C_BG            = "#fafafa"       # Content background
C_SURFACE       = "#ffffff"       # Card surface
C_SIDEBAR       = "#f3f3f3"       # Sidebar background
C_SIDEBAR_HOVER = "#eaeaea"       # Sidebar item hover
C_SIDEBAR_SEL   = "#e5e5e5"       # Sidebar item selected
C_ACCENT        = "#0067c0"       # Win11 Blue Accent
C_ACCENT_HOVER  = "#005a9e"
C_TEXT          = "#1a1a1a"       # Primary text
C_SUBTEXT       = "#5d5d5d"       # Secondary text
C_BORDER        = "#e5e5e5"       # Subtle card borders
C_SUCCESS       = "#0f7b0f"       # Success green text
C_SUCCESS_BG    = "#dff6dd"       # Success green background

PAGES = ["Overview", "Setup", "API Keys", "Features", "Tips"]

class WelcomeWindow:
    def __init__(self):
        self._current_page = 0
        self._nav_items = []
        self._build()

    def _build(self):
        root = tk.Tk()
        self._root = root
        root.title("VocalFlow — Getting Started")
        root.geometry("820x600")
        root.resizable(False, False)
        root.configure(bg=C_BG)
        root.protocol("WM_DELETE_WINDOW", self._close)
        root.update_idletasks()
        
        # Center window
        x = (root.winfo_screenwidth()  - 820) // 2
        y = (root.winfo_screenheight() - 600) // 2
        root.geometry(f"820x600+{x}+{y}")
        
        self._build_layout()
        self._show_page(0)
        root.mainloop()

    def _build_layout(self):
        # Sidebar (Left Navigation Pane)
        self._sidebar = tk.Frame(self._root, bg=C_SIDEBAR, width=220)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)
        
        # Header in Sidebar
        header_frame = tk.Frame(self._sidebar, bg=C_SIDEBAR)
        header_frame.pack(fill="x", padx=20, pady=(30, 20))
        tk.Label(header_frame, text="VocalFlow", font=("Segoe UI Semibold", 14), fg=C_TEXT, bg=C_SIDEBAR, anchor="w").pack(fill="x")
        tk.Label(header_frame, text="Getting Started", font=("Segoe UI", 9), fg=C_SUBTEXT, bg=C_SIDEBAR, anchor="w").pack(fill="x")
        
        # Navigation Items
        self._nav_btns = []
        for i, page in enumerate(PAGES):
            btn_frame = tk.Frame(self._sidebar, bg=C_SIDEBAR)
            btn_frame.pack(fill="x", padx=12, pady=2)
            
            # Selection indicator (blue pill on the left)
            indicator = tk.Frame(btn_frame, bg=C_SIDEBAR, width=3, height=16)
            indicator.pack(side="left", padx=(0, 8))
            indicator.pack_propagate(False)
            
            lbl = tk.Label(btn_frame, text=page, font=("Segoe UI", 9), fg=C_TEXT, bg=C_SIDEBAR, anchor="w", cursor="hand2", pady=8)
            lbl.pack(fill="x", expand=True)
            
            # Bindings for hover and click
            def on_enter(e, f=btn_frame, l=lbl, idx=i):
                if self._current_page != idx:
                    f.config(bg=C_SIDEBAR_HOVER)
                    l.config(bg=C_SIDEBAR_HOVER)

            def on_leave(e, f=btn_frame, l=lbl, idx=i):
                if self._current_page != idx:
                    f.config(bg=C_SIDEBAR)
                    l.config(bg=C_SIDEBAR)
                    
            def on_click(e, idx=i):
                self._show_page(idx)

            lbl.bind("<Enter>", on_enter)
            lbl.bind("<Leave>", on_leave)
            lbl.bind("<Button-1>", on_click)
            btn_frame.bind("<Enter>", on_enter)
            btn_frame.bind("<Leave>", on_leave)
            btn_frame.bind("<Button-1>", on_click)
            
            self._nav_items.append((btn_frame, indicator, lbl))

        tk.Frame(self._sidebar, bg=C_SIDEBAR).pack(expand=True)
        
        # Version info
        tk.Label(self._sidebar, text="Version 1.0.0", font=("Segoe UI", 8), fg=C_SUBTEXT, bg=C_SIDEBAR).pack(pady=(0, 20))
        
        # Content Area
        self._content = tk.Frame(self._root, bg=C_BG)
        self._content.pack(side="left", fill="both", expand=True)

    def _show_page(self, idx):
        self._current_page = idx
        
        # Update sidebar styling
        for i, (frame, indicator, lbl) in enumerate(self._nav_items):
            if i == idx:
                frame.config(bg=C_SIDEBAR_SEL)
                lbl.config(bg=C_SIDEBAR_SEL, font=("Segoe UI Semibold", 9))
                indicator.config(bg=C_ACCENT)
            else:
                frame.config(bg=C_SIDEBAR)
                lbl.config(bg=C_SIDEBAR, font=("Segoe UI", 9))
                indicator.config(bg=C_SIDEBAR)
                
        # Clear content
        for w in self._content.winfo_children():
            w.destroy()
            
        # Load new page
        [self._page_overview, self._page_setup, self._page_apikeys,
         self._page_features, self._page_tips][idx]()

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _scrollable(self):
        outer = tk.Frame(self._content, bg=C_BG)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=C_BG, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        
        # Win11 style hidden scrollbar unless needed
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        inner = tk.Frame(canvas, bg=C_BG)
        wid = canvas.create_window((0,0), window=inner, anchor="nw")
        
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))
        return inner

    def _header(self, p, title, sub):
        header_container = tk.Frame(p, bg=C_BG)
        header_container.pack(fill="x", padx=36, pady=(36, 24))
        tk.Label(header_container, text=title, font=("Segoe UI Semibold", 20), fg=C_TEXT, bg=C_BG, anchor="w").pack(fill="x")
        tk.Label(header_container, text=sub, font=("Segoe UI", 10), fg=C_SUBTEXT, bg=C_BG, anchor="w", wraplength=460).pack(fill="x", pady=(4, 0))

    def _section(self, p, text):
        # Simulates letter-spacing for headers without breaking tkinter
        spaced_text = " ".join(text.upper())
        tk.Label(p, text=spaced_text, font=("Segoe UI Semibold", 8), fg=C_SUBTEXT, bg=C_BG, anchor="w").pack(fill="x", padx=36, pady=(16, 8))

    def _card(self, p):
        # Outer frame for border
        border_frame = tk.Frame(p, bg=C_BORDER, padx=1, pady=1)
        border_frame.pack(fill="x", padx=36, pady=4)
        # Inner frame for background
        inner_frame = tk.Frame(border_frame, bg=C_SURFACE)
        inner_frame.pack(fill="both", expand=True)
        return inner_frame

    def _nav_bar(self, p, idx):
        bar = tk.Frame(p, bg=C_BG, pady=24)
        bar.pack(fill="x", padx=36, side="bottom")
        
        # Bottom Navigation Buttons
        if idx < len(PAGES)-1:
            self._mkbtn(bar, "Next", C_ACCENT, "white", lambda: self._show_page(idx+1)).pack(side="right")
        else:
            self._mkbtn(bar, "Finish Setup", C_ACCENT, "white", self._close).pack(side="right")
            
        if idx > 0:
            self._mkbtn(bar, "Back", C_SURFACE, C_TEXT, lambda: self._show_page(idx-1), is_secondary=True).pack(side="right", padx=(0, 12))

    def _mkbtn(self, parent, text, bg, fg, cmd, is_secondary=False):
        border_color = C_BORDER if is_secondary else bg
        border = tk.Frame(parent, bg=border_color, padx=1, pady=1)
        
        b = tk.Label(border, text=text, font=("Segoe UI", 9), fg=fg, bg=bg, padx=24, pady=6, cursor="hand2")
        b.pack(fill="both", expand=True)
        
        # Hover effects
        def on_enter(e):
            if not is_secondary: b.config(bg=C_ACCENT_HOVER)
            else: b.config(bg="#f5f5f5")
            
        def on_leave(e):
            b.config(bg=bg)
            
        b.bind("<Enter>", on_enter)
        b.bind("<Leave>", on_leave)
        b.bind("<Button-1>", lambda e: cmd())
        return border

    # ── Page 1: Overview ────────────────────────────────────────────────────
    def _page_overview(self):
        p = self._scrollable()
        self._header(p, "Welcome to VocalFlow", "Dictate into any text field on your PC using your voice.")
        
        # Status Banner
        banner = tk.Frame(p, bg=C_SUCCESS_BG)
        banner.pack(fill="x", padx=36, pady=(0, 16))
        tk.Label(banner, text="Status: Running - The application is active in your system tray.", font=("Segoe UI", 9), fg=C_SUCCESS, bg=C_SUCCESS_BG, anchor="w", pady=10, padx=16, wraplength=420).pack(fill="x")
        
        self._section(p, "How it works")
        for step, title, desc in [
            ("1", "Hold your hotkey", "Press and hold the configured key (default: Right Alt / AltGr)."),
            ("2", "Speak naturally", "Audio is streamed and processed in real time as you speak."),
            ("3", "Release to paste", "The final transcript is automatically pasted at your cursor."),
        ]:
            card = self._card(p)
            row = tk.Frame(card, bg=C_SURFACE, pady=16)
            row.pack(fill="x", padx=20)
            
            # Step number
            num_frame = tk.Frame(row, bg="#f0f0f0", width=28, height=28)
            num_frame.pack(side="left", padx=(0, 16))
            num_frame.pack_propagate(False)
            tk.Label(num_frame, text=step, font=("Segoe UI Semibold", 10), bg="#f0f0f0", fg=C_TEXT).pack(expand=True)
            
            # Text
            inner = tk.Frame(row, bg=C_SURFACE)
            inner.pack(side="left", fill="x", expand=True)
            tk.Label(inner, text=title, font=("Segoe UI Semibold", 10), fg=C_TEXT, bg=C_SURFACE, anchor="w").pack(fill="x")
            tk.Label(inner, text=desc, font=("Segoe UI", 9), fg=C_SUBTEXT, bg=C_SURFACE, anchor="w", wraplength=420).pack(fill="x", pady=(2, 0))
            
        self._section(p, "Compatibility")
        card = self._card(p)
        tk.Label(card, text="Works seamlessly across Web Browsers, Microsoft Word, Notepad, VS Code, Outlook, and any standard text input field.", font=("Segoe UI", 9), fg=C_SUBTEXT, bg=C_SURFACE, anchor="w", justify="left", pady=16, padx=20, wraplength=420).pack(fill="x")
        
        self._nav_bar(p, 0)

    # ── Page 2: Setup ───────────────────────────────────────────────────────
    def _page_setup(self):
        p = self._scrollable()
        self._header(p, "Configuration", "Right-click the system tray icon and select Settings to configure.")
        
        for tab, badge, bcolor, desc in [
            ("ASR Configuration (Deepgram)", "Required", C_ACCENT,
             "1. Paste Deepgram API key and save.\n2. Fetch Models.\n3. Select Model: nova-3-general\n4. Select Language: en-US (or multi for mixed languages)"),
            ("Hotkey Assignment", "Required", C_ACCENT,
             "Choose which key to hold while speaking.\nDefault: Right Alt / AltGr\nOptions include Left Alt, Right Ctrl, Left Ctrl, Right Shift."),
            ("LLM Processing (Groq)", "Optional", "#6b6b6b",
             "1. Paste Groq API key and save.\n2. Fetch Models.\n3. Select Model: llama-3.3-70b-versatile\nEnables advanced spelling, grammar correction, and translation."),
            ("Features Selection", "Optional", "#6b6b6b",
             "Toggle enhancements: Spelling Correction, Grammar Correction, Code-Mix Input, or Convert to Language."),
            ("Appearance", "Optional", "#6b6b6b",
             "Select a waveform overlay theme: Vibrant Blue, Bloom Rush, Mint Flow, or Magic Garden."),
        ]:
            card = self._card(p)
            row = tk.Frame(card, bg=C_SURFACE, pady=16, padx=20)
            row.pack(fill="x")
            
            header_row = tk.Frame(row, bg=C_SURFACE)
            header_row.pack(fill="x", pady=(0, 8))
            
            tk.Label(header_row, text=tab, font=("Segoe UI Semibold", 10), fg=C_TEXT, bg=C_SURFACE).pack(side="left")
            
            # Pill badge
            badge_frame = tk.Frame(header_row, bg=bcolor, padx=6, pady=2)
            badge_frame.pack(side="left", padx=12)
            tk.Label(badge_frame, text=badge.upper(), font=("Segoe UI Semibold", 7), fg="white", bg=bcolor).pack()
            
            tk.Label(row, text=desc, font=("Segoe UI", 9), fg=C_SUBTEXT, bg=C_SURFACE, anchor="w", justify="left", wraplength=420).pack(fill="x")
            
        self._nav_bar(p, 1)

    # ── Page 3: API Keys ────────────────────────────────────────────────────
    def _page_apikeys(self):
        p = self._scrollable()
        self._header(p, "API Services", "Both services offer generous free tiers. No credit card is required.")
        
        for name, sub, details, url in [
            ("Deepgram", "Speech-to-Text Engine (Required)", "Free tier includes 12,000 minutes per year.\nRecommended model: nova-3-general", "https://console.deepgram.com/signup"),
            ("Groq", "Language Model Engine (Optional)", "Provides extremely fast post-processing.\nRecommended model: llama-3.3-70b-versatile", "https://console.groq.com"),
        ]:
            card = self._card(p)
            row = tk.Frame(card, bg=C_SURFACE, pady=16, padx=20)
            row.pack(fill="x")
            
            info = tk.Frame(row, bg=C_SURFACE)
            info.pack(side="left", fill="x", expand=True)
            
            tk.Label(info, text=name, font=("Segoe UI Semibold", 11), fg=C_TEXT, bg=C_SURFACE, anchor="w").pack(fill="x")
            tk.Label(info, text=sub, font=("Segoe UI", 9), fg=C_SUBTEXT, bg=C_SURFACE, anchor="w").pack(fill="x", pady=(2, 6))
            tk.Label(info, text=details, font=("Segoe UI", 9), fg=C_SUBTEXT, bg=C_SURFACE, anchor="w", justify="left", wraplength=420).pack(fill="x")
            
            # Clean text link
            link = tk.Label(row, text="Get API Key", font=("Segoe UI", 9), fg=C_ACCENT, bg=C_SURFACE, cursor="hand2")
            link.pack(side="right", padx=8)
            link.bind("<Enter>", lambda e, l=link: l.config(font=("Segoe UI", 9, "underline")))
            link.bind("<Leave>", lambda e, l=link: l.config(font=("Segoe UI", 9)))
            link.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            
        self._section(p, "Security Notice")
        sec_card = self._card(p)
        tk.Label(sec_card, text="API keys are securely stored within the Windows Credential Manager and are never saved as plain text on your system.", font=("Segoe UI", 9), fg=C_SUBTEXT, bg=C_SURFACE, anchor="w", pady=16, padx=20, wraplength=420).pack(fill="x")
        
        self._nav_bar(p, 2)

    # ── Page 4: Features ────────────────────────────────────────────────────
    def _page_features(self):
        p = self._scrollable()
        self._header(p, "Advanced Features", "All post-processing features require a configured Groq API key.")
        
        for title, desc in [
            ("Spelling Correction", "Automatically fixes typographic errors before pasting.\nExample: \"helo wrold\" becomes \"hello world\"."),
            ("Grammar Correction", "Refines sentence structure while preserving the original meaning.\nExample: \"i goes to store\" becomes \"I went to the store\"."),
            ("Code-Mix Input", "Optimized for users speaking mixed languages (e.g., Hindi + English).\nRequires ASR language set to 'multi'. Transliterates non-Roman scripts accurately."),
            ("Language Conversion", "Translates the spoken transcript into a selected target language before pasting.\nSupports over 20 languages and distinct regional styles."),
            ("Waveform Themes", "Customizable visual overlay during recording to match your desktop aesthetic."),
        ]:
            card = self._card(p)
            row = tk.Frame(card, bg=C_SURFACE, pady=16, padx=20)
            row.pack(fill="x")
            
            tk.Label(row, text=title, font=("Segoe UI Semibold", 10), fg=C_TEXT, bg=C_SURFACE, anchor="w").pack(fill="x")
            tk.Label(row, text=desc, font=("Segoe UI", 9), fg=C_SUBTEXT, bg=C_SURFACE, anchor="w", justify="left", wraplength=420).pack(fill="x", pady=(4, 0))
            
        self._nav_bar(p, 3)

    # ── Page 5: Tips ────────────────────────────────────────────────────────
    def _page_tips(self):
        p = self._scrollable()
        self._header(p, "Troubleshooting", "Common solutions for a smooth experience.")
        
        for title, desc in [
            ("Hotkey is unresponsive", "Certain applications block low-level keyboard inputs. Try launching VocalFlow as an administrator."),
            ("Inaccurate mixed-language detection", "Ensure the ASR language is set to 'multi'. Enable 'Code-Mix Input' in the features tab and select the correct language pair."),
            ("Text fails to paste", "Verify that the target text field is selected and actively focused before releasing the hotkey. The application utilizes the standard Ctrl+V command."),
            ("Transcript contains duplicated words", "This can occur if the API connection experiences high latency. Check your network stability or limit the length of continuous dictation."),
            ("Configurations are not saving", "Application settings are written to ~/.vocalflow_settings.json. Ensure your user account has standard read/write permissions to the home directory."),
        ]:
            card = self._card(p)
            row = tk.Frame(card, bg=C_SURFACE, pady=16, padx=20)
            row.pack(fill="x")
            
            tk.Label(row, text=title, font=("Segoe UI Semibold", 10), fg=C_TEXT, bg=C_SURFACE, anchor="w").pack(fill="x")
            tk.Label(row, text=desc, font=("Segoe UI", 9), fg=C_SUBTEXT, bg=C_SURFACE, anchor="w", justify="left", wraplength=420).pack(fill="x", pady=(4, 0))
            
        self._nav_bar(p, 4)

    def _close(self):
        self._root.destroy()

if __name__ == "__main__":
    WelcomeWindow()