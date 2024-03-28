from characterai import PyCAI
from util import *
import pydirectinput
import json
import time
import traceback

settings_file = 'settings.json'

try:
    with open(settings_file) as f:
        settings = json.load(f)
except FileNotFoundError:
    log_and_exit('No settings file found!')

for key, values in settings.items():
    for value in values:
        param = settings[key][value]
        if not param:
            log_and_exit(f'Please set {value} in {settings_file}!')

# C.AI
cai_client = PyCAI(settings['c.ai']['api_key'])
char = settings['c.ai']['character_id']

# Save tgt and history_external_id
# to avoid making a lot of requests

chat = cai_client.chat.get_chat(char)

history_id = chat['external_id']
participants = chat['participants']

# In the list of "participants",
# a character can be at zero or in the first place
if not participants[0]['is_human']:
    tgt = participants[0]['user']['username']
else:
    tgt = participants[1]['user']['username']

# Game
cs_path = get_steam_path() + '\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\'
log_dir = cs_path + 'console.log'
exec_dir = cs_path + 'cfg\\message.cfg'

chat_char_limit = 222
chat_delay = 0.5
last_log = ''
msg_identifier = '  [ALL] '


while True:
    log = get_last_chat(log_dir)
    time.sleep(0.05)

    # Don't respond to same message or when there's no [ALL] chat message
    if log == last_log or log is None:
        continue

    data = log.split(': ')

    # Don't respond to self
    if get_last_game_name_used() in data[0]:
        continue

    last_log = log
    message = data[1]

    while True:
        try:
            data = cai_client.chat.send_message(
                history_id, text=message, tgt=tgt
            )

            name = data['src_char']['participant']['name']
            text = data['replies'][0]['text'].replace('\n', ' ').replace('"', "''").replace(';', '')
            break
        except:
            print("Error sending or retrieving message, retrying.")
            print(traceback.format_exc())
            continue

    # Chunk our message in order to send everything
    texts = [text[i:i + chat_char_limit] for i in range(0, len(text), chat_char_limit)]

    for text in texts:
        with open(exec_dir, 'w', encoding='utf-8') as f:
            f.write(f'say "{text}"')

        pydirectinput.write(settings['game']['message_bind_key'])
        time.sleep(chat_delay)
