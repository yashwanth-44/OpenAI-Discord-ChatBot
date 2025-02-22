import asyncio
from asyncio import tasks
from collections import deque
import nextcord
import os
from nextcord.ext import commands, tasks
from gtts import gTTS
from g4f.client import Client
from googletrans import Translator
import yt_dlp as youtube_dl
import random
from dotenv import load_dotenv

load_dotenv(".env")
TOKEN = os.getenv("BOT_TOKEN")

intents = nextcord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="nm", intents=intents)

# test command
@bot.command(name="hi")
async def send_message(ctx):
    await ctx.send("hello.")

# TTS command
@bot.command(name="tts")
async def tts(ctx, *args):
    text = " ".join(args)
    user = ctx.message.author

    if user.voice is not None:
        try:
            print("Connecting to voice channel...")
            vc = await user.voice.channel.connect()
            print("Connected to voice channel.")
        except nextcord.ClientException:
            vc = ctx.voice_client
        except Exception as e:
            await ctx.send(f"Error connecting to voice channel: {str(e)}")
            return

        sound = gTTS(text=text, lang="en-us", slow=False)
        sound.save("tts-audio.mp3")
        print("TTS audio saved as tts-audio.mp3")

        if vc.is_playing():
            vc.stop()

        ffmpeg_path = "C:/ffmpeg/bin/ffmpeg.exe"
        print(f"playing audio using FFmpeg at path: {ffmpeg_path}")
        source = nextcord.FFmpegPCMAudio("tts-audio.mp3", executable=ffmpeg_path)
        vc.play(source)

        while vc.is_playing():
            await nextcord.utils.sleep_until(nextcord.utils.utcnow() + nextcord.utils.timedelta(seconds=1))

        await vc.disconnect()
        print("disconnected from voice channel.")
        os.remove("tts-audio.mp3")

    else:
        await ctx.send("join a voice channel first.")
        
# Chat command
@bot.command(name="c")
async def send_message(ctx, *args):
    prompt = " ".join(args)
    user = ctx.message.author
    
    client = Client()
    
    spam_start = "sorry, 您的ip"
    
    def get_valid_response():
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "you are not an ai. you are a human with emotions", "content": f"lets roleplay im a person and i say {prompt} answer to me in a as a cute little kittens tone dont add any body movements or narrative dont ever use emojis"}],
            web_search=False
        )
        
        resp = response.choices[0].message.content
        print(resp)
    
        return resp
    
    resp = get_valid_response()
    await ctx.send(resp)
    
# Respond to prompt on VC
@bot.command(name="ttv")
async def send_message(ctx, *args):
    prompt = " ".join(args)
    
    translator = Translator()
    client = Client()

    spam_start = "sorry, 您的ip"

    def get_valid_response():
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "you are not an ai. you are a human with emotions", "content": f"lets roleplay im a person and i say {prompt} answer to me in a as a cute little kittens tone dont add any body movements or narrative dont ever use emojis"}],
            web_search=False
        )
        
        resp = response.choices[0].message.content
        print(resp)
        
        return resp

    response_text = get_valid_response()

    # Convert response_text to speech
    tts = gTTS(text=response_text, lang='en-us')
    tts.save("response.mp3")
    
    # Join voice channel and play the response
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        vc = await channel.connect()
        
        vc.play(nextcord.FFmpegPCMAudio("response.mp3"), after=lambda e: print("Finished playing"))
        
        # Disconnect after the audio is played
        while vc.is_playing():
            await asyncio.sleep(1)  # Use asyncio.sleep instead of nextcord.utils.sleep
        
        await vc.disconnect()
        
        # Clean up the saved audio file
        os.remove("response.mp3")
    else:
        await ctx.send("You are not in a voice channel!")
            
        
# 
# IMAGE GENERATOR (Fixed)
# 

@bot.command("gen")
async def send_message(ctx, *args):
    prompt = " ".join(args)
    
    try:
        client = Client()
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, lambda: client.images.generate(
            model="flux",
            prompt=prompt,
            response_format="url"
        ))

        if response and response.data:
            image_url = response.data[0].url

            # Force Discord to embed the image
            embed = nextcord.Embed(title="Generated Image", description=f"Prompt: {prompt}")
            embed.set_image(url=image_url)

            await ctx.send(embed=embed)
        else:
            await ctx.send("No image was generated.")
    
    except Exception as e:
        print(f"An error occurred: {e}")
        await ctx.send("Sorry, something went wrong while generating the image.")
    
# 
# YTDL 
# 

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' 
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(nextcord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # Take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(nextcord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def from_search(cls, search, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{search}", download=not stream))

        if 'entries' in data:
            # Take first item from a search result
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(nextcord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

queue = deque()

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')
    keep_alive.start()

async def play_next(ctx):
    if queue:
        player = queue.popleft()
        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(f'**Now playing:** {player.title}')
    else:
        await ctx.voice_client.disconnect()

@bot.command(name='play', help='To play song')
async def play(ctx, *, search):
    if ctx.author.voice is None:
        await ctx.send("You are not connected to a voice channel!")
        return

    if ctx.voice_client is None:
        channel = ctx.author.voice.channel
        await channel.connect()

    async with ctx.typing():
        player = await YTDLSource.from_search(search, loop=bot.loop, stream=True)
        queue.append(player)

    if not ctx.voice_client.is_playing():
        await play_next(ctx)
    else:
        await ctx.send(f'**Added to queue:** {player.title}')

@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
        queue.clear()
    else:
        await ctx.send("The bot is not connected to a voice channel.")

@bot.command(name='skip', help='Skip the current song')
async def skip(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
    else:
        await ctx.send("The bot is not playing anything at the moment.")

@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
    else:
        await ctx.send("The bot is not playing anything at the moment.")

@tasks.loop(seconds=15)
async def keep_alive():
    for vc in bot.voice_clients:
        if vc.is_connected():
            try:
                await vc.guild.me.edit(nick=vc.guild.me.nick)  # send no-op command to keep the connection alive
            except nextcord.HTTPException:
                pass

keep_alive.start()


# 
# BLACKJACK
# 


suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']


def create_deck():
    deck = []
    for suit in suits:
        for rank in ranks:
            deck.append(f'{rank} of {suit}')
    random.shuffle(deck)
    return deck


def calculate_hand_value(hand):
    value = 0
    ace_count = 0
    for card in hand:
        rank = card.split()[0]
        if rank.isdigit():
            value += int(rank)
        elif rank in ['Jack', 'Queen', 'King']:
            value += 10
        elif rank == 'Ace':
            ace_count += 1
            value += 11  

   
    while ace_count > 0 and value > 21:
        value -= 10  
        ace_count -= 1

    return value


def deal_initial_hands(deck):
    player_hand = [deck.pop(), deck.pop()]
    bot_hand = [deck.pop(), deck.pop()]
    return player_hand, bot_hand


def is_blackjack(hand):
    return len(hand) == 2 and calculate_hand_value(hand) == 21

@bot.command(name='bj', help='play a game of Blackjack against the bot')
async def blackjack(ctx):
    deck = create_deck()
    player_hand, bot_hand = deal_initial_hands(deck)
    player_turn = True

    player_value = calculate_hand_value(player_hand)
    bot_value = calculate_hand_value(bot_hand)

    await ctx.send(f'Your hand: {", ".join(player_hand)}\nYour total: {player_value}')
    await ctx.send(f"nee mummy's hand: {bot_hand[0]}, Hidden Card")

    if is_blackjack(player_hand):
        await ctx.send("You got Blackjack! You win!")
        return

    while player_turn:
        await ctx.send("Hit or Stand? (Type 'hit' or 'stand')")
        try:
            response = await bot.wait_for('message', check=lambda message: message.author == ctx.author and message.content.lower() in ['hit', 'stand'], timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("Timeout! Game over.")
            return

        if response.content.lower() == 'hit':
            player_hand.append(deck.pop())
            player_value = calculate_hand_value(player_hand)
            await ctx.send(f'Your hand: {", ".join(player_hand)}\nYour total: {player_value}')
            if player_value > 21:
                await ctx.send("Busted! You lose.")
                return
        else:
            player_turn = False

    while bot_value < 17:
        bot_hand.append(deck.pop())
        bot_value = calculate_hand_value(bot_hand)

    await ctx.send(f"nee mummy's hand: {', '.join(bot_hand)}\nnee mummy's total: {bot_value}")

    if bot_value > 21:
        await ctx.send("nee mummy busted! You win!")
    elif bot_value > player_value:
        await ctx.send("nee mummy wins!")
    elif bot_value < player_value:
        await ctx.send("You win!")
    else:
        await ctx.send("It's a tie!")

# 
# ON EVENT / START
# 

@bot.event
async def on_ready():
    print(f"{bot.user.name} has logged in.")

if __name__ == '__main__':
    bot.run(TOKEN)
