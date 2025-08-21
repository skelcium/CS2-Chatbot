## CS2-Chatbot
Automatically respond to in-game messages in Counter-Strike 2

![image](https://github.com/skelcium/CS2-Chatbot/assets/141345390/aaaea781-60a2-4fcb-881b-178f3c0b621d)
![image](https://github.com/skel-sys/CS2-Chatbot/assets/141345390/9b8a3948-cf43-4960-a786-b87e83be4abb)

## Setup
1. Add `-condebug` to your CS2 launch options
2. In CS2, run `bind p "exec message.cfg"`

## Requirements
- An [old.character.ai](https://old.character.ai/) account in order to fetch an API key

## I can't find my API key
Log into [old.character.ai](https://old.character.ai/), open your browser's developer console, enter `console.log(JSON.parse(localStorage.getItem("char_token")).value)` and copy the result

## Can I be banned for this?
No
