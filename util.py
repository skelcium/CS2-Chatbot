import struct
import winreg
import time
from ctypes import wintypes, windll, create_unicode_buffer

def get_steam_path():
    try:
        hKey = None
        if (8 * struct.calcsize("P")) == 64:
            hKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Wow6432Node\\Valve\\Steam')
        else:
            hKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Valve\\Steam')

        path = winreg.QueryValueEx(hKey, "InstallPath")
        winreg.CloseKey(hKey)
        return str(path[0])
    except:
        return None


def get_last_game_name_used():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam')
        name, _ = winreg.QueryValueEx(key, 'LastGameNameUsed')
        return name
    except:
        return None


def get_last_chat(log_dir, n=10):
    with open(log_dir, encoding='utf-8', errors='replace') as f:
        lines = f.readlines()[-n:]
        lines.reverse()

    for line in lines:
        if '  [ALL] ' in line:
            return line


def get_window():
    hWnd = windll.user32.GetForegroundWindow()
    length = windll.user32.GetWindowTextLengthW(hWnd)
    buf = create_unicode_buffer(length + 1)
    windll.user32.GetWindowTextW(hWnd, buf, length + 1)

    # 1-liner alternative: return buf.value if buf.value else None
    if buf.value:
        return buf.value
    else:
        return None