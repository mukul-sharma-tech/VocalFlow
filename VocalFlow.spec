# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # app packages
        'config',
        'core', 'core.app_state', 'core.audio_engine', 'core.audio_muter',
        'core.hotkey_manager', 'core.text_injector',
        'services', 'services.deepgram_service', 'services.groq_service',
        'storage', 'storage.keychain_service',
        'ui', 'ui.tray_controller', 'ui.overlay_window',
        'ui.settings_window', 'ui.welcome_window',
        # pycaw / COM
        'pycaw.pycaw', 'comtypes', 'comtypes.client', 'comtypes.server',
        # keyring Windows backend
        'keyring.backends.Windows',
        # audio
        'sounddevice', 'numpy',
        # win32
        'win32api', 'win32con', 'win32gui',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VocalFlow',
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # no terminal window — tray app
    bootloader_ignore_signals=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
