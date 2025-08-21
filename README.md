# CS2-Chatbot

Automatically respond to in-game messages in Counter-Strike 2

![image](https://github.com/skelcium/CS2-Chatbot/assets/141345390/aaaea781-60a2-4fcb-881b-178f3c0b621d)
![image](https://github.com/skel-sys/CS2-Chatbot/assets/141345390/9b8a3948-cf43-4960-a786-b87e83be4abb)

## Setup

1. Add `-condebug` to your CS2 launch options
2. In CS2, run `bind p "exec message.cfg"`

## Requirements

- A [character.ai](https://character.ai/) account in order to fetch an API token

## I can't find my API token

1. Log into [character.ai](https://character.ai/) and make sure you're signed in
2. Open your browser's Developer Tools (F12)
3. Go to the **Application** tab (Chrome) or **Storage** tab (Firefox)
4. Click on **Cookies** in the left sidebar
5. Select the Character.AI domain from the list
6. Look for a cookie named `HTTP_AUTHORIZATION`
7. Copy the value after "Token " (the long string of letters and numbers)
8. That's your API token!

## Can I be banned for this?

No
