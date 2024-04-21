import winreg
from ctypes import windll, create_unicode_buffer


def get_steam_path():
    try:
        hKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Wow6432Node\\Valve\\Steam')
        path = winreg.QueryValueEx(hKey, 'InstallPath')[0]
        winreg.CloseKey(hKey)
        return str(path)
    except:
        return None


def get_cs_path():
    try:
        hKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\WOW6432Node\\Valve\\cs2')
        path = winreg.QueryValueEx(hKey, 'installpath')[0]
        winreg.CloseKey(hKey)
        return str(path)
    except:
        return None


def get_last_name_used():
    try:
        hKey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'SOFTWARE\\Valve\\Steam')
        name = winreg.QueryValueEx(hKey, 'LastGameNameUsed')[0]
        winreg.CloseKey(hKey)
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


def get_foreground_window_title():
    hWnd = windll.user32.GetForegroundWindow()
    length = windll.user32.GetWindowTextLengthW(hWnd)
    buf = create_unicode_buffer(length + 2)
    windll.user32.GetWindowTextW(hWnd, buf, length + 2)
    return buf.value
