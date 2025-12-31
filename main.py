import asyncio
import json
import logging
import os
import pydirectinput
import random
import requests
import traceback
import vdf
import winreg
from ctypes import wintypes, windll, create_unicode_buffer, byref, POINTER, sizeof
from PyCharacterAI import get_client
from nicegui import ui, run
from numerize import numerize


# util.py temporarily moved into main to use logger, might rework later
windll.advapi32.OpenProcessToken.restype = wintypes.BOOL
windll.advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, POINTER(wintypes.HANDLE)]

windll.advapi32.GetTokenInformation.restype = wintypes.BOOL
windll.advapi32.GetTokenInformation.argtypes = [wintypes.HANDLE, wintypes.DWORD, POINTER(None), wintypes.DWORD,
                                                POINTER(wintypes.DWORD)]

windll.kernel32.CloseHandle.restype = wintypes.BOOL
windll.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

windll.kernel32.FormatMessageW.restype = wintypes.DWORD
windll.kernel32.FormatMessageW.argtypes = [wintypes.DWORD, wintypes.LPCVOID, wintypes.DWORD, wintypes.DWORD,
                                           POINTER(wintypes.LPWSTR), wintypes.DWORD, wintypes.LPVOID]

windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
windll.kernel32.GetCurrentProcess.argtypes = []

windll.kernel32.GetLastError.restype = wintypes.DWORD
windll.kernel32.GetLastError.argtypes = []

windll.kernel32.LocalFree.restype = wintypes.HLOCAL
windll.kernel32.LocalFree.argtypes = [wintypes.HLOCAL]

FORMAT_MESSAGE_ALLOCATE_BUFFER = 0x100
FORMAT_MESSAGE_FROM_SYSTEM = 0x1000
FORMAT_MESSAGE_IGNORE_INSERTS = 0x200

TOKEN_READ = 0x20008  # STANDARD_RIGHTS_READ | TOKEN_QUERY
TokenElevationType = 18  # TOKEN_INFORMATION_CLASS.TokenElevationType
TokenElevation = 20  # TOKEN_INFORMATION_CLASS.TokenElevation
TokenElevationTypeLimited = 3  # TOKEN_ELEVATION_TYPE.TokenElevationTypeLimited


def log_last_win_error(user_data=None):
    err = windll.kernel32.GetLastError()

    buf = wintypes.LPWSTR(0)
    default_lang_id = wintypes.DWORD(1024)  # MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT)

    res = windll.kernel32.FormatMessageW(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM |
                                         FORMAT_MESSAGE_IGNORE_INSERTS, 0, err, default_lang_id, byref(buf), 0, 0)

    if user_data:
        logger.error(f"{user_data} - Win Error [{err}] - {buf.value}")
    else:
        logger.error(f"Win Error [{err}] - {buf.value}")

    if res != 0:
        windll.kernel32.LocalFree(buf)


def is_running_as_admin():
    token_handle = wintypes.HANDLE()
    if not windll.advapi32.OpenProcessToken(windll.kernel32.GetCurrentProcess(), TOKEN_READ, byref(token_handle)):
        log_last_win_error('OpenProcessToken')
        return False

    token_information_elevation_type = wintypes.DWORD(0)
    buf_len = wintypes.DWORD(0)
    if (not windll.advapi32.GetTokenInformation(token_handle, TokenElevationType,
                                                byref(token_information_elevation_type),
                                                sizeof(token_information_elevation_type), byref(buf_len))
            or sizeof(token_information_elevation_type) != buf_len.value):
        windll.kernel32.CloseHandle(token_handle)
        log_last_win_error('GetTokenInformation')
        return False

    logger.debug(f"Token elevation type: {token_information_elevation_type.value}")

    token_information_elevation = wintypes.DWORD(0)
    buf_len = wintypes.DWORD(0)
    if (not windll.advapi32.GetTokenInformation(token_handle, TokenElevation, byref(token_information_elevation),
                                                sizeof(token_information_elevation), byref(buf_len))
            or sizeof(token_information_elevation) != buf_len.value):
        windll.kernel32.CloseHandle(token_handle)
        log_last_win_error('GetTokenInformation')
        return False

    logger.debug(f"Token elevation: {token_information_elevation.value}")

    windll.kernel32.CloseHandle(token_handle)
    return (token_information_elevation_type.value != TokenElevationTypeLimited
            and token_information_elevation.value != 0)


def get_steam_path():
    reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Wow6432Node\\Valve\\Steam')
    path = winreg.QueryValueEx(reg_key, 'InstallPath')[0]
    winreg.CloseKey(reg_key)
    return str(path)


def get_cs_path():
    reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\WOW6432Node\\Valve\\cs2')
    path = winreg.QueryValueEx(reg_key, 'installpath')[0]
    winreg.CloseKey(reg_key)
    return str(path)


def get_active_steam_id():
    reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'SOFTWARE\\Valve\\Steam\\ActiveProcess')
    steam_id = winreg.QueryValueEx(reg_key, 'ActiveUser')[0]
    winreg.CloseKey(reg_key)
    return steam_id


def get_last_steam_nick():
    reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'SOFTWARE\\Valve\\Steam')
    name = winreg.QueryValueEx(reg_key, 'LastGameNameUsed')[0]
    winreg.CloseKey(reg_key)
    return name


def is_condebug_in_game_args():
    steam_path = get_steam_path()
    if not steam_path:
        logger.warning('Could not get Steam path')
        return False

    user_id = get_active_steam_id()
    if user_id == 0:
        logger.warning('Could not identify active Steam user (is Steam running?)')
        return False

    cfg_path = steam_path + f"\\userdata\\{str(user_id)}\\config\\localconfig.vdf"
    if not os.path.exists(cfg_path):
        logger.warning('Steam missing localconfig.vdf')
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
    window_handle = windll.user32.GetForegroundWindow()
    length = windll.user32.GetWindowTextLengthW(window_handle)
    buf = create_unicode_buffer(length + 2)
    windll.user32.GetWindowTextW(window_handle, buf, length + 2)
    return buf.value


# Enhanced notify function that logs to both GUI and terminal
def notify_and_log(message, type='info', level='info', **kwargs):
    """Show notification in GUI and log to terminal"""
    # Map notify types to log levels
    log_level_map = {
        'positive': 'info',
        'negative': 'error',
        'warning': 'warning',
        'info': 'info'
    }

    # Get the appropriate log level
    log_level = log_level_map.get(type, level)

    # Log to terminal
    if log_level == 'error':
        logger.error(f"GUI Notification: {message}")
    elif log_level == 'warning':
        logger.warning(f"GUI Notification: {message}")
    else:
        logger.info(f"GUI Notification: {message}")

    # Show in GUI - ensure type is valid
    from typing import Literal
    valid_types = ['positive', 'negative', 'warning', 'info', 'ongoing']
    if type in valid_types:
        ui.notify(message, type=type, **kwargs)  # type: ignore
    else:
        ui.notify(message, type='info', **kwargs)


class ToggleButton(ui.button):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._state = False
        self.on('click', self.toggle)

    def toggle(self) -> None:
        """Toggle the button state."""
        self._state = not self._state
        self.update()

        if cai_token.value == '':
            notify_and_log('Please set a C.AI token!', type='negative')
            tabs.set_value('Settings')
            self._state = not self._state
        elif not current_char:
            notify_and_log('Please select a character to use first!', type='negative')
            tabs.set_value('Characters')
            self._state = not self._state
        elif self._state:
            notify_and_log('Chatbot is now running!', type='positive', color='pink')
            toggle_active.classes(remove='animate-pulse')
            status_badge.set_visibility(False)
            cai_token.disable()
        else:
            notify_and_log('Chatbot has been disabled.', type='warning')
            cai_token.enable()

        self.update()

    def update(self) -> None:
        self.props(f'color={"green" if self._state else "pink"}')
        super().update()


async def handle_chat():
    global last_log
    if toggle_active._state:
        log = get_last_chat(log_path)

        # Don't respond to same message or when there's no [ALL] chat message
        if log == last_log or log is None:
            return

        data = log.split(': ')

        # Don't respond to self
        if get_last_steam_nick() in data[0]:
            return

        last_log = log
        message = data[1]

        if mimic_mode_switch.value:
            response_message = ''.join([char.upper() if random.randint(0, 1) else char.lower() for char in message])
        else:
            if not current_chat or not current_character_id:
                notify_and_log('No character selected or chat not initialized!', type='negative')
                return

            try:
                logger.debug(f"Sending message to character {current_character_id}: {message}")
                answer = await client.chat.send_message(
                    current_character_id, current_chat.chat_id, message
                )
                response_message = answer.get_primary_candidate().text
                logger.debug(f"Received response: {response_message}")
            except Exception as e:
                logger.error(f"Failed to send message to Character.AI: {str(e)}")
                logger.error(f"Exception details: {traceback.format_exc()}")
                notify_and_log(f'Failed to send message: {str(e)}', type='negative')
                return

        # Clean string
        text = response_message.replace('"', "''").replace('\n', ' ')

        # Chunk our message in order to send everything
        texts = [text[i:i + chat_char_limit] for i in range(0, len(text), chat_char_limit)]

        for text in texts:
            with open(exec_path, 'w', encoding='utf-8') as f:
                f.write(f'say "{text}"')

            # Don't send an input to other windows
            if get_foreground_window_title() == 'Counter-Strike 2':
                if human_mode_switch.value:
                    await asyncio.sleep(each_key_delay * len(text))

                pydirectinput.write(bind_key)
                await asyncio.sleep(chat_delay)


def swap_theme(e):
    if e.value:
        theme.enable()
    else:
        theme.disable()


def load_settings():
    try:
        with open(settings_file) as f:
            settings = json.load(f)
            if settings['token']:
                cai_token.value = settings['token']
    except FileNotFoundError:
        print('No settings file, creating one.')
        with open(settings_file, 'w') as f:
            json.dump({'token': ''}, f)
    except json.JSONDecodeError:
        print('Invalid JSON data, recreating file.')
        with open(settings_file, 'w') as f:
            json.dump({'token': ''}, f)


def check_if_updated():
    try:
        data = requests.get('https://api.github.com/repositories/708269905/releases').json()
        recent_tag = data[0]['tag_name']

        if recent_tag != current_version:
            ui.notify(
                'A new update is available, click <a style="color: #ec4899" href="https://github.com/skelcium/CS2-Chatbot/releases" target="_blank">here</a> to download it.',
                html=True, close_button='Close', timeout=20000)
    except:
        ui.notify("Failed to check if up-to-date.")


def check_if_admin():
    if not is_running_as_admin():
        ui.notify('Not running as admin, some features <b>may not work</b>.', html=True, close_button='Close',
                  timeout=0, type='warning')


def check_if_condebug():
    if not is_condebug_in_game_args():
        ui.notify('Could not find <b>-condebug</b> in Steam CS2 launch arguments.', html=True, close_button='Close',
                  timeout=0, type='warning')


def select_character_sync(char):
    """Synchronous wrapper for select_character using NiceGUI's context"""

    # Use NiceGUI's run.io_bound to properly handle the async function
    async def wrapper():
        await select_character(char)

    # Use ui.timer to run the async function once
    ui.timer(0.01, wrapper, once=True)


async def select_character(char):
    logger.debug(f"Attempting to select character: {char.name} (ID: {char.character_id})")
    if not client:
        notify_and_log('Please set a C.AI token!', type='negative')
        tabs.set_value('Settings')
        return

    global current_character_id
    global current_char
    global current_chat

    try:
        current_character_id = char.character_id
        current_char = char

        # Create new chat using new library
        logger.debug(f"Creating chat for character {char.character_id}")
        current_chat, _ = await client.chat.create_chat(current_character_id)
        logger.debug(f"Chat created successfully: {current_chat.chat_id}")

        reset_button.enable()

        if hasattr(char, 'avatar') and char.avatar:
            avatar = char.avatar.get_url()
        else:
            avatar = 'https://characterai.io/i/80/static/topic-pics/cai-light-on-dark.jpg'

        notify_and_log(f'Selected <b>{char.name}</b> as your character.', type='positive', avatar=avatar,
                       color='pink', html=True)

    except Exception as e:
        logger.error(f"Failed to create chat for character {char.name}: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        notify_and_log(f'Failed to create chat: {str(e)}', type='negative')
        return


async def set_token(token, overwrite=False):
    global client

    try:
        client = await get_client(token=token)
        me = await client.account.fetch_me()
        username = me.username

        if username == 'ANONYMOUS':
            ui.notify('An invalid token has been set!', type='negative')
        else:
            ui.notify(f'Welcome {username}!', type='positive', color='pink')

            # Save correct token
            if overwrite:
                with open(settings_file, 'w') as f:
                    json.dump({'token': token}, f)

            await search(query_type='Trending')
    except Exception as e:
        ui.notify(f'Authentication failed: {str(e)}', type='negative')
        client = None


async def search(query_type='Search'):
    if cai_token.value == '':
        ui.notify('Please set a C.AI token!', type='negative')
        tabs.set_value('Settings')
        return

    search_btn.disable()

    try:
        # Check if client is authenticated
        if not client:
            notify_and_log('Please set a C.AI token first!', type='negative')
            return

        # NEW search methods using proper async calls
        if query_type == 'Recommended':
            logger.debug("Fetching recommended characters")
            characters = await client.character.fetch_recommended_characters()
        elif query_type == 'Recent':
            logger.debug("Fetching recent chats")
            # Get recent chats and extract character info
            recent_chats = await client.chat.fetch_recent_chats()
            characters = []
            for chat in recent_chats:
                # Create a character-like object from chat info
                char_obj = type('Character', (), {
                    'character_id': chat.character_id,
                    'name': chat.character_name,
                    'title': '',
                    'description': '',
                    'num_interactions': 0,
                    'avatar': chat.character_avatar if hasattr(chat, 'character_avatar') else None
                })()
                characters.append(char_obj)
        elif query_type == 'Trending':
            logger.debug("Fetching featured characters (trending)")
            # Use featured characters as trending equivalent
            characters = await client.character.fetch_featured_characters()
        elif query_type == 'Search':
            logger.debug(f"Searching for characters with query: {character_input.value}")
            characters = await client.character.search_characters(character_input.value)
        else:
            characters = []

        logger.debug(f"Retrieved {len(characters)} characters for query_type: {query_type}")
        results.clear()

        for character in characters:
            name = character.name
            if hasattr(character, 'avatar') and character.avatar:
                avatar = character.avatar.get_url()
            else:
                avatar = 'https://characterai.io/i/80/static/topic-pics/cai-light-on-dark.jpg'

            with results:
                with ui.link().on('click', lambda char=character: select_character_sync(char)).classes(
                        'no-underline hover:scale-105 duration-100 active:scale-100 text-pink-600'):
                    with ui.card().tight().classes('w-36 h-48 text-center').classes(
                            'shadow-md shadow-black dark:bg-[#121212]'):
                        ui.image(avatar).classes('h-32')
                        with ui.row().classes('absolute right-2 top-1'):
                            if hasattr(character, 'num_interactions') and character.num_interactions:
                                interaction_label = f'🗨️{numerize.numerize(character.num_interactions)}'
                            else:
                                interaction_label = ''

                            ui.label(interaction_label).classes('text-center drop-shadow-[0_1.2px_1.2px_rgba(0,0,0,1)]')
                        with ui.card_section().classes('h-6 w-full font-bold'):
                            ui.label(name).classes('drop-shadow-[0_1.2px_1.2px_rgba(0,0,0,0.8)] break-words')

        character_count_badge.text = len(characters)

    except Exception as e:
        traceback_msg = traceback.format_exc()
        ui.notify(traceback_msg)
        search_btn.enable()

    search_btn.enable()


if __name__ == "__main__":
    # Setup comprehensive logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.FileHandler('cs2_chatbot_debug.log', 'w'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    logger.info("=== CS2-Chatbot Starting with Debug Logging ===")
    logger.info("Logging initialized - messages will appear in both GUI and terminal")

    current_version = 'v1.3.1'

    theme = ui.dark_mode()
    theme.enable()

    ui.query('.nicegui-content').classes('p-0')
    ui.colors(primary='#ec4899')

    # c.ai vars
    settings_file = 'chatbot_settings.json'
    client = None
    current_character_id = None
    current_char = None
    current_chat = None

    # Game data
    cs_path = os.path.join(get_cs_path(), 'game', 'csgo')
    logger.debug(f"CS path - {cs_path}")

    log_path = os.path.join(cs_path, 'console.log')
    logger.debug(f"Log path - {log_path}")

    exec_path = os.path.join(cs_path, 'cfg', 'message.cfg')
    logger.debug(f"Exec path - {exec_path}")

    bind_key = 'p'

    chat_char_limit = 221  # Cut-off observed with 222
    chat_delay = 0.5
    last_log = ''
    each_key_delay = 0.2

    handle_chat_timer = ui.timer(0.1, handle_chat, active=True)

    with ui.dialog() as dialog_help_api, ui.card():
        ui.markdown('''
        <h1 style="margin: 0 0 20px 0">Get API Token</h1>
        
        <ol>
            <li> Visit <a style="text-decoration: none; color: hotpink;" target='_blank' href='https://old.character.ai/'>https://old.character.ai/</a> </li>
            <li> Open DevTools in your browser </li>
            <li> Go to Storage → Local Storage → char_token </li>
            <li> Copy value </li>
        </ol>
        ''')

        ui.button('Close', on_click=dialog_help_api.close).props('outline')

    with ui.splitter(value=16).classes('w-full h-screen').props(':limits="[16, 32]"') as splitter:
        with splitter.before:
            ui.icon('chat', color='primary').classes('m-auto text-5xl mt-6')
            with ui.tabs().props('vertical').classes('w-full h-full') as tabs:
                characters = ui.tab('Characters', icon='group')
                with characters:
                    character_count_badge = ui.badge('0').classes('absolute mr-3')
                settings = ui.tab('Settings', icon='settings')

            with ui.row().classes('p-2 mx-auto'):
                toggle_active = ToggleButton(icon='power_settings_new').classes('w-11 animate-pulse')
                with toggle_active:
                    status_badge = ui.badge('OFF').props('floating').classes('bg-red rounded')
                reset_button = ui.button(icon='restart_alt').classes('w-11 outline').on('click',
                                                                                        lambda e: select_character_sync(
                                                                                            current_char))
                reset_button.disable()

                with reset_button:
                    ui.tooltip("⚠️ Reset Character's memory").classes('bg-red')

        with splitter.after:
            with ui.tab_panels(tabs, value=characters).props('vertical').classes('w-full h-full'):
                with ui.tab_panel(characters).classes('overflow-x-hidden'):
                    with ui.row().classes('flex items-center w-full'):
                        character_input = ui.input('Character').on('keypress.enter', search).classes('w-52')
                        search_btn = ui.button(on_click=search, icon='search').classes('outline mt-auto')
                        character_select = ui.select(['Recommended', 'Trending', 'Recent'], value='Trending',
                                                     on_change=lambda e: search(query_type=e.value)).classes(
                            'ml-auto').props('filled')

                    ui.separator()
                    results = ui.row().classes('justify-center')
                    with results:
                        ui.chat_message(
                            "Hello, recommended characters will be displayed here once you've set a C.AI token.",
                            name='Skel',
                            stamp='now',
                            avatar='https://avatars.githubusercontent.com/u/141345390?s=400&u=16b4e98ca85ea791552d50cdb4aef6491a95e7c9&v=4'
                        ).props(add="bg-color='pink' text-color='white'")

                with ui.tab_panel(settings):
                    with ui.grid(columns=2).classes('w-full'):
                        with ui.card().tight().classes('shadow-sm shadow-black'):
                            with ui.card_section():
                                ui.badge('API')
                                cai_token = ui.input(label='C.AI Token', password=True,
                                                     on_change=lambda e: set_token(e.value, overwrite=True))

                                with ui.row().classes('mt-5'):
                                    ui.button(icon='help', on_click=dialog_help_api.open).props('rounded')

                        with ui.card().tight().classes('shadow-sm shadow-black'):
                            with ui.card_section():
                                ui.badge('Appearance')
                                ui.html('<br>')

                                ui.switch('Dark Theme', on_change=swap_theme, value=True)

                                with ui.row().classes('mt-3'):
                                    with ui.button(icon='colorize').props('rounded') as button:
                                        ui.color_picker(on_pick=lambda e: ui.colors(primary=e.color))

                        with ui.card().tight().classes('shadow-sm shadow-black'):
                            with ui.card_section():
                                ui.badge('Chatbot')
                                ui.html('<br>')

                                mimic_mode_switch = ui.switch('Mimic Mode')
                                human_mode_switch = ui.switch('Humanized Typing Speed')

                                with mimic_mode_switch:
                                    ui.tooltip('Repeat messages with randomly applied capitalization, JuSt LikE ThiS!')

    check_if_updated()
    check_if_admin()
    check_if_condebug()
    load_settings()

    logger.info("Starting CS2-Chatbot with new PyCharacterAI library...")
    ui.run(native=True, show=True, window_size=(840, 600), title='CS2 Chatbot', reload=False, show_welcome_message=False)
