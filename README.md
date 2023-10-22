## CS2-Chatbot
Automatically respond to in-game messages

<img src="https://gyazo.com/9c9f653b963142812cf47dc997e795ee.png">

## Setup
1. Add `-condebug` to your CS2 launch options
2. In CS2, bind `exec message.cfg` to the same key as `message_bind_key` in the chatbot's settings.json file
3. Set your username in the settings.json file in order to not reply to yourself

## Requirements
- A [character.ai](https://c.ai/) account in order to fetch the API key that'll you'll have to set in the settings.json file
- A character id in order to set the character used to reply to messages, this can be found at the end of the character chat url and will have to be set in the settings.json file
