import struct
import winreg
import time


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


def log_and_exit(message):
    print(message)
    time.sleep(5)
    exit()
