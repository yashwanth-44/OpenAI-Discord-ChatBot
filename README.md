# OpenAPI Discord Bot

## Overview

This is a multifunctional Discord bot built using `nextcord`, designed to provide various utilities such as text-to-speech (TTS), AI-powered chat responses, YouTube audio playback, and a simple Blackjack game.

## Features

- **General Commands**
  - `nmhi` - Sends a simple "hello" message.
    
- **Text-to-Speech (TTS)**
  - `nmtts <text>` - Converts the provided text into speech and plays it in the user's voice channel.
    
- **AI Chatbot**
  - `nmc <prompt>` - Generates a response using OpenAI's GPT-3.5.
  - `nmttv <prompt>` - Generates an AI response, converts it to speech, and plays it in the voice channel.
    
- **YouTube Audio Player**
  - `nmplay <song name/URL>` - Searches for a song and plays it in the voice channel.
  - `nmskip` - Skips the current song.
  - `nmstop` - Stops the song.
  - `nmleave` - Makes the bot leave the voice channel.
    
- **Blackjack Game**
  - `nmbj` - Play a game of Blackjack against the bot.

## Installation & Setup

1. Clone this repository:
   ```sh
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   ```
   
2. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```
   
3. Set up a `.env` file and add your bot token:
   ```env
   BOT_TOKEN=your_discord_bot_token
   ```
   
4. Run the bot:
   ```sh
   python bot.py
   ```

## Dependencies

- `nextcord`
- `gtts`
- `g4f`
- `googletrans`
- `yt_dlp`
- `python-dotenv`

## Notes

- Ensure `ffmpeg` is installed and the correct path is set.
- The bot requires message content intents enabled in the Discord Developer Portal.

