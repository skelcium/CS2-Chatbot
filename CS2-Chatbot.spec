# -*- mode: python ; coding: utf-8 -*-
# CS2-Chatbot PyInstaller Specification File
# This file is REQUIRED for proper dependency inclusion - do not delete!
from PyInstaller.utils.hooks import collect_all

# Collect all data, binaries, and hidden imports for each package
nicegui_data, nicegui_binaries, nicegui_hiddenimports = collect_all('nicegui')
pywebview_data, pywebview_binaries, pywebview_hiddenimports = collect_all('pywebview')
pydirectinput_data, pydirectinput_binaries, pydirectinput_hiddenimports = collect_all('pydirectinput')
pycharacterai_data, pycharacterai_binaries, pycharacterai_hiddenimports = collect_all('PyCharacterAI')

datas = [('.')]
datas += nicegui_data
datas += pywebview_data
datas += pydirectinput_data
datas += pycharacterai_data

binaries = []
binaries += nicegui_binaries
binaries += pywebview_binaries
binaries += pydirectinput_binaries
binaries += pycharacterai_binaries

hiddenimports = [
    'PyCharacterAI', 'nicegui', 'pydirectinput', 'requests', 'numerize', 'vdf', 'pywebview',
    # Additional modules that might be missed
    'asyncio', 'json', 'random', 'traceback', 'logging',
    # NiceGUI specific modules
    'nicegui.elements', 'nicegui.events', 'nicegui.ui', 'nicegui.run',
    # PyDirectInput specific modules  
    'pydirectinput._pyautogui_win', 'pydirectinput._pyautogui_x11',
    # PyCharacterAI dependencies
    'curl_cffi', 'curl_cffi.requests',
    # Additional dependencies
    'typing_extensions', 'bottle', 'proxy_tools', 'pythonnet'
]
hiddenimports += nicegui_hiddenimports
hiddenimports += pywebview_hiddenimports
hiddenimports += pydirectinput_hiddenimports
hiddenimports += pycharacterai_hiddenimports


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CS2-Chatbot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
