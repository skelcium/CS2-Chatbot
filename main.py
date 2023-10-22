from characterai import PyCAI
from util import get_steam_path, read_n_to_last_line, log_and_exit
import pydirectinput
import json
import time

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

chat_char_limit = 244
chat_delay = 0.5
last_log = ''

while True:
    log = read_n_to_last_line(log_dir)
    if log == last_log or " : " not in log:
        continue

    data = log.split(' : ')

    if settings['game']['username'] in data[0]:
        continue

    last_log = log
    message = data[1]

    data = cai_client.chat.send_message(
        history_id, text=message, tgt=tgt
    )

    try:
        name = data['src_char']['participant']['name']
        text = data['replies'][0]['text'].replace('\n', ' ').replace('"', "''")
    except:
        text = "**Message filtered**"

    # Chunk our message in order to send everything
    texts = [text[i:i+chat_char_limit] for i in range(0, len(text), chat_char_limit)]

    for text in texts:
        with open(exec_dir, 'w', encoding='utf-8') as f:
            f.write(f'say "{text}"')

        pydirectinput.write(settings['game']['message_bind_key'])
        time.sleep(chat_delay)
