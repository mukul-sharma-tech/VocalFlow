import tkinter as tk
from tkinter import ttk, messagebox
import threading
from app_state import AppState, HOTKEY_OPTIONS
from groq_service import CODE_MIX_OPTIONS, TARGET_LANGUAGES


class SettingsWindow:
    def __init__(self, app_state: AppState, keychain, settings):
        self._app_state = app_state
        self._keychain = keychain
        self._settings = settings
        self._win: tk.Toplevel | None = None

    def open(self):
        if self._win and self._win.winfo_exists():
            self._win.lift()
            self._win.focus_force()
            return
        self._build()

    def _build(self):
        win = tk.Toplevel()
        self._win = win
        win.title("VocalFlow Settings")
        win.geometry("480x680")
        win.resizable(False, False)

        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_asr_tab(notebook)
        self._build_groq_tab(notebook)
        self._build_features_tab(notebook)
        self._build_hotkey_tab(notebook)
        self._build_appearance_tab(notebook)

    # ------------------------------------------------------------------ #
    # ASR tab                                                              #
    # ------------------------------------------------------------------ #

    def _build_asr_tab(self, nb):
        frame = ttk.Frame(nb, padding=12)
        nb.add(frame, text="ASR (Deepgram)")

        ttk.Label(frame, text="Deepgram API Key").grid(row=0, column=0, sticky="w", pady=4)
        key_var = tk.StringVar(value=self._app_state.deepgram_api_key)
        key_entry = ttk.Entry(frame, textvariable=key_var, show="*", width=40)
        key_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=2)

        show_var = tk.BooleanVar(value=False)
        def toggle_show():
            key_entry.config(show="" if show_var.get() else "*")
        ttk.Checkbutton(frame, text="Show", variable=show_var, command=toggle_show).grid(
            row=1, column=2, padx=4
        )

        status_var = tk.StringVar()
        def save_key():
            val = key_var.get().strip()
            self._keychain.store("deepgram_api_key", val)
            self._app_state.deepgram_api_key = val
            status_var.set("Saved!")
            win = self._win
            if win:
                win.after(2000, lambda: status_var.set(""))

        ttk.Button(frame, text="Save", command=save_key).grid(row=2, column=0, sticky="w", pady=4)
        ttk.Label(frame, textvariable=status_var, foreground="green").grid(row=2, column=1, sticky="w")

        ttk.Separator(frame).grid(row=3, column=0, columnspan=3, sticky="ew", pady=8)

        ttk.Label(frame, text="Model").grid(row=4, column=0, sticky="w")
        model_var = tk.StringVar(value=self._app_state.selected_model)
        model_combo = ttk.Combobox(frame, textvariable=model_var, state="readonly", width=30)
        model_combo.grid(row=4, column=1, columnspan=2, sticky="ew", pady=2)

        ttk.Label(frame, text="Language").grid(row=5, column=0, sticky="w")
        lang_var = tk.StringVar(value=self._app_state.selected_language)
        lang_combo = ttk.Combobox(frame, textvariable=lang_var, state="readonly", width=30)
        lang_combo.grid(row=5, column=1, columnspan=2, sticky="ew", pady=2)

        fetch_status = tk.StringVar()

        def on_model_change(event=None):
            selected = model_var.get()
            self._app_state.selected_model = selected
            self._settings.set("selected_model", selected)
            model = next(
                (m for m in self._app_state.available_models if m.canonical_name == selected), None
            )
            if model:
                langs = model.languages
                lang_combo["values"] = langs
                if self._app_state.selected_language not in langs:
                    lang_var.set(langs[0] if langs else "")
                    self._app_state.selected_language = lang_var.get()

        model_combo.bind("<<ComboboxSelected>>", on_model_change)

        def on_lang_change(event=None):
            self._app_state.selected_language = lang_var.get()
            self._settings.set("selected_language", lang_var.get())

        lang_combo.bind("<<ComboboxSelected>>", on_lang_change)

        def fetch_models():
            fetch_status.set("Fetching...")
            def _done(models):
                self._app_state.available_models = models
                names = [m.canonical_name for m in models]
                if self._win:
                    self._win.after(0, lambda: _update_ui(names))
            def _update_ui(names):
                model_combo["values"] = names
                if self._app_state.selected_model in names:
                    model_var.set(self._app_state.selected_model)
                elif names:
                    model_var.set(names[0])
                    self._app_state.selected_model = names[0]
                on_model_change()
                fetch_status.set("Done" if names else "No models found")
                if self._win:
                    self._win.after(2000, lambda: fetch_status.set(""))

            from deepgram_service import DeepgramService
            DeepgramService().fetch_models(self._app_state.deepgram_api_key, _done)

        ttk.Button(frame, text="Fetch Models", command=fetch_models).grid(
            row=6, column=0, sticky="w", pady=6
        )
        ttk.Label(frame, textvariable=fetch_status, foreground="gray").grid(
            row=6, column=1, sticky="w"
        )

        # Populate if already loaded
        if self._app_state.available_models:
            names = [m.canonical_name for m in self._app_state.available_models]
            model_combo["values"] = names
            model_var.set(self._app_state.selected_model)
            on_model_change()

        frame.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------ #
    # Groq tab                                                             #
    # ------------------------------------------------------------------ #

    def _build_groq_tab(self, nb):
        frame = ttk.Frame(nb, padding=12)
        nb.add(frame, text="Groq (LLM)")

        ttk.Label(frame, text="Groq API Key").grid(row=0, column=0, sticky="w", pady=4)
        key_var = tk.StringVar(value=self._app_state.groq_api_key)
        key_entry = ttk.Entry(frame, textvariable=key_var, show="*", width=40)
        key_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=2)

        show_var = tk.BooleanVar()
        def toggle():
            key_entry.config(show="" if show_var.get() else "*")
        ttk.Checkbutton(frame, text="Show", variable=show_var, command=toggle).grid(
            row=1, column=2, padx=4
        )

        status_var = tk.StringVar()
        def save_key():
            val = key_var.get().strip()
            self._keychain.store("groq_api_key", val)
            self._app_state.groq_api_key = val
            status_var.set("Saved!")
            if self._win:
                self._win.after(2000, lambda: status_var.set(""))

        ttk.Button(frame, text="Save", command=save_key).grid(row=2, column=0, sticky="w", pady=4)
        ttk.Label(frame, textvariable=status_var, foreground="green").grid(row=2, column=1, sticky="w")

        ttk.Separator(frame).grid(row=3, column=0, columnspan=3, sticky="ew", pady=8)

        ttk.Label(frame, text="Model").grid(row=4, column=0, sticky="w")
        groq_model_var = tk.StringVar(value=self._app_state.selected_groq_model)
        groq_combo = ttk.Combobox(frame, textvariable=groq_model_var, state="readonly", width=30)
        groq_combo.grid(row=4, column=1, columnspan=2, sticky="ew", pady=2)

        def on_groq_model_change(event=None):
            self._app_state.selected_groq_model = groq_model_var.get()
            self._settings.set("selected_groq_model", groq_model_var.get())
        groq_combo.bind("<<ComboboxSelected>>", on_groq_model_change)

        fetch_status = tk.StringVar()
        def fetch_groq():
            fetch_status.set("Fetching...")
            def _done(models):
                self._app_state.available_groq_models = models
                ids = [m.id for m in models]
                if self._win:
                    self._win.after(0, lambda: _update(ids))
            def _update(ids):
                groq_combo["values"] = ids
                if self._app_state.selected_groq_model in ids:
                    groq_model_var.set(self._app_state.selected_groq_model)
                elif ids:
                    groq_model_var.set(ids[0])
                    self._app_state.selected_groq_model = ids[0]
                fetch_status.set("Done" if ids else "No models found")
                if self._win:
                    self._win.after(2000, lambda: fetch_status.set(""))
            from groq_service import GroqService
            GroqService().fetch_models(self._app_state.groq_api_key, _done)

        ttk.Button(frame, text="Fetch Models", command=fetch_groq).grid(
            row=5, column=0, sticky="w", pady=6
        )
        ttk.Label(frame, textvariable=fetch_status, foreground="gray").grid(
            row=5, column=1, sticky="w"
        )

        if self._app_state.available_groq_models:
            ids = [m.id for m in self._app_state.available_groq_models]
            groq_combo["values"] = ids
            groq_model_var.set(self._app_state.selected_groq_model)

        frame.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------ #
    # Features tab                                                         #
    # ------------------------------------------------------------------ #

    def _build_features_tab(self, nb):
        frame = ttk.Frame(nb, padding=12)
        nb.add(frame, text="Features")

        row = 0

        spell_var = tk.BooleanVar(value=self._app_state.correction_mode_enabled)
        def on_spell():
            self._app_state.correction_mode_enabled = spell_var.get()
            self._settings.set("correction_mode_enabled", spell_var.get())
        ttk.Checkbutton(frame, text="Spelling Correction", variable=spell_var, command=on_spell).grid(
            row=row, column=0, sticky="w", pady=4
        )
        row += 1

        grammar_var = tk.BooleanVar(value=self._app_state.grammar_correction_enabled)
        def on_grammar():
            self._app_state.grammar_correction_enabled = grammar_var.get()
            self._settings.set("grammar_correction_enabled", grammar_var.get())
        ttk.Checkbutton(frame, text="Grammar Correction", variable=grammar_var, command=on_grammar).grid(
            row=row, column=0, sticky="w", pady=4
        )
        row += 1

        ttk.Separator(frame).grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1

        codemix_var = tk.BooleanVar(value=self._app_state.code_mix_enabled)
        codemix_combo_var = tk.StringVar(value=self._app_state.selected_code_mix)
        codemix_combo = ttk.Combobox(
            frame,
            textvariable=codemix_combo_var,
            values=[f"{n} ({d})" for n, d in CODE_MIX_OPTIONS],
            state="disabled", width=35
        )

        def on_codemix_toggle():
            enabled = codemix_var.get()
            self._app_state.code_mix_enabled = enabled
            self._settings.set("code_mix_enabled", enabled)
            codemix_combo.config(state="readonly" if enabled else "disabled")

        def on_codemix_select(event=None):
            raw = codemix_combo_var.get().split(" (")[0]
            self._app_state.selected_code_mix = raw
            self._settings.set("selected_code_mix", raw)

        ttk.Checkbutton(frame, text="Code-Mix Input", variable=codemix_var, command=on_codemix_toggle).grid(
            row=row, column=0, sticky="w"
        )
        row += 1
        codemix_combo.grid(row=row, column=0, columnspan=2, sticky="ew", pady=2)
        codemix_combo.bind("<<ComboboxSelected>>", on_codemix_select)
        if self._app_state.code_mix_enabled:
            codemix_combo.config(state="readonly")
        row += 1

        ttk.Separator(frame).grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1

        target_var = tk.BooleanVar(value=self._app_state.target_language_enabled)
        target_lang_var = tk.StringVar(value=self._app_state.selected_target_language)
        target_combo = ttk.Combobox(
            frame, textvariable=target_lang_var,
            values=TARGET_LANGUAGES, state="disabled", width=35
        )

        def on_target_toggle():
            enabled = target_var.get()
            self._app_state.target_language_enabled = enabled
            self._settings.set("target_language_enabled", enabled)
            target_combo.config(state="readonly" if enabled else "disabled")

        def on_target_select(event=None):
            self._app_state.selected_target_language = target_lang_var.get()
            self._settings.set("selected_target_language", target_lang_var.get())

        ttk.Checkbutton(frame, text="Convert to Language", variable=target_var, command=on_target_toggle).grid(
            row=row, column=0, sticky="w"
        )
        row += 1
        target_combo.grid(row=row, column=0, columnspan=2, sticky="ew", pady=2)
        target_combo.bind("<<ComboboxSelected>>", on_target_select)
        if self._app_state.target_language_enabled:
            target_combo.config(state="readonly")

        frame.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------ #
    # Hotkey tab                                                           #
    # ------------------------------------------------------------------ #

    def _build_hotkey_tab(self, nb):
        frame = ttk.Frame(nb, padding=12)
        nb.add(frame, text="Hotkey")

        ttk.Label(frame, text="Hold key to record, release to transcribe.").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        hotkey_var = tk.StringVar(value=self._app_state.selected_hotkey)
        options = list(HOTKEY_OPTIONS.items())

        for i, (key, info) in enumerate(options):
            rb = ttk.Radiobutton(
                frame, text=info["display"], variable=hotkey_var, value=key,
                command=lambda k=key: self._set_hotkey(k)
            )
            rb.grid(row=i + 1, column=0, sticky="w", pady=3)

        frame.columnconfigure(0, weight=1)

    def _set_hotkey(self, key: str):
        self._app_state.selected_hotkey = key
        self._settings.set("selected_hotkey", key)

    # ------------------------------------------------------------------ #
    # Appearance tab                                                       #
    # ------------------------------------------------------------------ #

    def _build_appearance_tab(self, nb):
        from app_state import OVERLAY_THEMES
        frame = ttk.Frame(nb, padding=12)
        nb.add(frame, text="Appearance")

        ttk.Label(frame, text="Waveform overlay theme:").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        theme_var = tk.StringVar(value=self._app_state.selected_overlay_theme)

        for i, (name, palette) in enumerate(OVERLAY_THEMES.items()):
            rb = ttk.Radiobutton(
                frame, text=name, variable=theme_var, value=name,
                command=lambda n=name: self._set_theme(n)
            )
            rb.grid(row=i + 1, column=0, sticky="w", pady=4)

            # Color preview strip
            preview = tk.Canvas(frame, width=100, height=16, highlightthickness=0, bg="#1e1e1e")
            seg_w = 100 // len(palette)
            for j, (r, g, b) in enumerate(palette):
                preview.create_rectangle(
                    j * seg_w, 0, (j + 1) * seg_w, 16,
                    fill=f"#{r:02x}{g:02x}{b:02x}", outline=""
                )
            preview.grid(row=i + 1, column=1, padx=12, sticky="w")

        frame.columnconfigure(0, weight=1)

    def _set_theme(self, name: str):
        self._app_state.selected_overlay_theme = name
        self._settings.set("selected_overlay_theme", name)
