import struct
import winreg
import os
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

def read_n_to_last_line(filename, n = 1):
    """Returns the nth before last line of a file (n=1 gives last line)"""
    num_newlines = 0
    with open(filename, 'rb') as f:
        try:
            f.seek(-2, os.SEEK_END)
            while num_newlines < n:
                f.seek(-2, os.SEEK_CUR)
                if f.read(1) == b'\n':
                    num_newlines += 1
        except OSError:
            f.seek(0)
        last_line = f.readline().decode('utf-8', 'ignore')
    return last_line

def log_and_exit(message):
    print(message)
    time.sleep(5)
    exit()
