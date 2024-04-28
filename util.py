import os, vdf, winreg
from ctypes import wintypes, windll, create_unicode_buffer, byref, POINTER, sizeof

windll.advapi32.OpenProcessToken.restype = wintypes.BOOL
windll.advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, POINTER(wintypes.HANDLE)]

windll.advapi32.GetTokenInformation.restype = wintypes.BOOL
windll.advapi32.GetTokenInformation.argtypes = [wintypes.HANDLE, wintypes.DWORD, POINTER(None), wintypes.DWORD, POINTER(wintypes.DWORD)]

windll.kernel32.CloseHandle.restype = wintypes.BOOL
windll.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
windll.kernel32.GetCurrentProcess.argtypes = []

TOKEN_READ = 0x20008           # STANDARD_RIGHTS_READ | TOKEN_QUERY
TokenElevationType = 18        # TOKEN_INFORMATION_CLASS.TokenElevationType
TokenElevation = 20            # TOKEN_INFORMATION_CLASS.TokenElevation
TokenElevationTypeLimited = 3  # TOKEN_ELEVATION_TYPE.TokenElevationTypeLimited


def is_running_as_admin():
    try:
        hToken = wintypes.HANDLE()
        if not windll.advapi32.OpenProcessToken(windll.kernel32.GetCurrentProcess(), TOKEN_READ, byref(hToken)):
            return False

        token_information_elevation_type = wintypes.DWORD(0)
        dwLen = wintypes.DWORD(0)
        if (not windll.advapi32.GetTokenInformation(hToken, TokenElevationType, byref(token_information_elevation_type),
                                                    sizeof(token_information_elevation_type), byref(dwLen))
                or sizeof(token_information_elevation_type) != dwLen.value):
            windll.kernel32.CloseHandle(hToken)
            return False

        token_information_elevation = wintypes.DWORD(0)
        dwLen = wintypes.DWORD(0)
        if (not windll.advapi32.GetTokenInformation(hToken, TokenElevation, byref(token_information_elevation),
                                                    sizeof(token_information_elevation), byref(dwLen))
                or sizeof(token_information_elevation) != dwLen.value):
            windll.kernel32.CloseHandle(hToken)
            return False

        windll.kernel32.CloseHandle(hToken)
        return token_information_elevation_type.value != TokenElevationTypeLimited and token_information_elevation.value != 0
    except:
        windll.kernel32.CloseHandle(hToken)
        return False


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


def get_current_user_id():
    try:
        hKey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'SOFTWARE\\Valve\\Steam\\ActiveProcess')
        id = winreg.QueryValueEx(hKey, 'ActiveUser')[0]
        winreg.CloseKey(hKey)
        return id
    except:
        return 0


def get_last_name_used():
    try:
        hKey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'SOFTWARE\\Valve\\Steam')
        name = winreg.QueryValueEx(hKey, 'LastGameNameUsed')[0]
        winreg.CloseKey(hKey)
        return name
    except:
        return None


def is_condebug_in_steam_args():
    steam_path = get_steam_path()
    if not steam_path:
        return False

    user_id = get_current_user_id()
    if user_id == 0:
        return False

    cfg_path = steam_path + f"\\userdata\\{str(user_id)}\\config\\localconfig.vdf"
    if not os.path.exists(cfg_path):
        return False

    try:
        cfg = vdf.load(open(cfg_path, encoding='utf-8'))

        if 'Steam' in cfg['UserLocalConfigStore']['Software']['Valve']:
            args = cfg['UserLocalConfigStore']['Software']['Valve']['Steam']['apps']['730']['LaunchOptions']
        else:
            args = cfg['UserLocalConfigStore']['Software']['Valve']['steam']['apps']['730']['LaunchOptions']

        return '-condebug' in args.lower()
    except:
        return False


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
