import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
import asyncio
import random
import time

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

song_queue = {}
idle_timer = {}
loop_song = {}
loop_queue = {}
last_song = {}
active_server = None  # Track the server where a song is currently playing

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'retries': 5,
    'fragment_retries': 5,
    'socket_timeout': 15
}

ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET))


class YTDLSource(discord.PCMVolumeTransformer):
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
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


@bot.event
async def on_ready():
    print(f'Bot is ready and logged in as {bot.user}!')
    await bot.change_presence(activity=discord.Game(name="Idle"))


@bot.command(name='join')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not in a voice channel!")
        return
    channel = ctx.message.author.voice.channel
    await channel.connect()


@bot.command(name='leave')
async def leave(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client:
        await voice_client.disconnect()
        if ctx.guild.id == active_server:
            await update_presence(None)  # Reset presence globally when leaving


# Function to update the bot's rich presence for the active server
async def update_presence(song):
    """Update the bot's presence to reflect the current song in the active server."""
    if song:
        await bot.change_presence(activity=discord.Game(name=f"Now Playing: {song.title}"))
    else:
        await bot.change_presence(activity=discord.Game(name="Idle"))


def play_next(ctx):
    global last_song, active_server
    guild_id = ctx.guild.id
    try:
        if guild_id == active_server:  # Only update presence in the active server
            if loop_song.get(guild_id, False):
                ctx.voice_client.play(last_song[guild_id], after=lambda e: play_next(ctx))
            elif loop_queue.get(guild_id, False) and len(song_queue[guild_id]) > 0:
                song_queue[guild_id].append(last_song[guild_id])
                next_song = song_queue[guild_id].pop(0)
                ctx.voice_client.play(next_song, after=lambda e: play_next(ctx))
                last_song[guild_id] = next_song
            elif len(song_queue[guild_id]) > 0:
                next_song = song_queue[guild_id].pop(0)
                ctx.voice_client.play(next_song, after=lambda e: play_next(ctx))
                last_song[guild_id] = next_song
                asyncio.run_coroutine_threadsafe(update_presence(next_song), bot.loop)  # Update presence
            else:
                idle_timer[guild_id] = bot.loop.call_later(900, lambda: asyncio.run_coroutine_threadsafe(ctx.voice_client.disconnect(), bot.loop))
                asyncio.run_coroutine_threadsafe(update_presence(None), bot.loop)  # Reset presence
    except Exception as e:
        print(f"An error occurred during playback: {e}")
        ctx.send(f"An error occurred: {e}. Skipping to the next song...")
        play_next(ctx)


@bot.command(name='play')
async def play(ctx, *, query):
    global last_song, active_server
    guild_id = ctx.guild.id

    try:
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                return

        voice_channel = ctx.voice_client

        if guild_id not in song_queue:
            song_queue[guild_id] = []

        if guild_id in idle_timer and idle_timer[guild_id]:
            idle_timer[guild_id].cancel()

        results = sp.search(q=query, type='track', limit=1)
        if len(results['tracks']['items']) == 0:
            await ctx.send("No track found on Spotify.")
            return
        
        track = results['tracks']['items'][0]
        track_name = track['name']
        artist_name = track['artists'][0]['name']

        youtube_query = f"{track_name} {artist_name}"

        async with ctx.typing():
            player = await YTDLSource.from_url(youtube_query, loop=bot.loop, stream=True)

            if voice_channel.is_playing():
                song_queue[guild_id].append(player)
                await ctx.send(f"Added to queue: {track_name} by {artist_name}")
            else:
                voice_channel.play(player, after=lambda e: play_next(ctx))
                last_song[guild_id] = player
                await ctx.send(f"Now playing: {track_name} by {artist_name}")
                active_server = guild_id  # Mark this as the active server for presence
                await update_presence(player)  # Update presence for the active server

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command(name='skip')
async def skip(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Song skipped.")
    else:
        await ctx.send("No song is currently playing.")


@bot.command(name='stop')
async def stop(ctx):
    guild_id = ctx.guild.id
    voice_client = ctx.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
    song_queue[guild_id] = []
    await ctx.send("Playback stopped and queue cleared.")
    if guild_id == active_server:
        await update_presence(None)  # Reset presence for this server


@bot.command(name='queue')
async def show_queue(ctx):
    guild_id = ctx.guild.id
    if guild_id in song_queue and len(song_queue[guild_id]) > 0:
        queue_list = [f"{i+1}. {song.title}" for i, song in enumerate(song_queue[guild_id])]
        await ctx.send("Current queue:\n" + "\n".join(queue_list))
    else:
        await ctx.send("The queue is currently empty.")


@bot.command(name='volume')
async def volume(ctx, volume: int):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.source.volume = volume / 100
        await ctx.send(f"Volume set to {volume}%")
    else:
        await ctx.send("No audio is currently playing.")


@bot.command(name='pause')
async def pause(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Playback paused.")
    else:
        await ctx.send("No audio is currently playing.")


@bot.command(name='resume')
async def resume(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Playback resumed.")
    else:
        await ctx.send("No audio is currently paused.")


@bot.command(name='loop')
async def loop(ctx, mode: str = 'off'):
    global loop_song, loop_queue
    guild_id = ctx.guild.id
    if mode == 'song':
        loop_song[guild_id] = True
        loop_queue[guild_id] = False
        await ctx.send("Looping the current song.")
    elif mode == 'queue':
        loop_song[guild_id] = False
        loop_queue[guild_id] = True
        await ctx.send("Looping the queue.")
    else:
        loop_song[guild_id] = False
        loop_queue[guild_id] = False
        await ctx.send("Looping is off.")


@bot.command(name='shuffle')
async def shuffle(ctx):
    guild_id = ctx.guild.id
    if guild_id in song_queue and len(song_queue[guild_id]) > 1:
        random.shuffle(song_queue[guild_id])
        await ctx.send("Queue shuffled.")
    else:
        await ctx.send("Not enough songs in the queue to shuffle.")


@bot.command(name='nowplaying')
async def now_playing(ctx):
    guild_id = ctx.guild.id
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        await ctx.send(f"Now playing: {last_song[guild_id].title}")
    else:
        await ctx.send("No song is currently playing.")


@bot.command(name='search')
async def search_song(ctx, *, query):
    try:
        results = sp.search(q=query, type='track', limit=5)
        if len(results['tracks']['items']) == 0:
            await ctx.send("No track found on Spotify.")
            return
        
        options = []
        for i, track in enumerate(results['tracks']['items']):
            options.append(f"{i + 1}. {track['name']} by {track['artists'][0]['name']}")
        
        await ctx.send(f"Select a song by number:\n" + "\n".join(options))

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= 5

        response = await bot.wait_for('message', check=check)
        selected_track = results['tracks']['items'][int(response.content) - 1]
        
        track_name = selected_track['name']
        artist_name = selected_track['artists'][0]['name']
        youtube_query = f"{track_name} {artist_name}"

        async with ctx.typing():
            player = await YTDLSource.from_url(youtube_query, loop=bot.loop, stream=True)

            voice_channel = ctx.voice_client
            guild_id = ctx.guild.id

            if voice_channel.is_playing():
                song_queue[guild_id].append(player)
                await ctx.send(f"Added to queue: {track_name} by {artist_name}")
            else:
                voice_channel.play(player, after=lambda e: play_next(ctx))
                last_song[guild_id] = player
                active_server = guild_id  
                await update_presence(player)  

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


bot.run(DISCORD_BOT_TOKEN)
