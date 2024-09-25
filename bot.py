import discord
from discord.ext import commands
import youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
import asyncio  

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

youtube_dl.utils.bug_reports_message = lambda: ''

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

@bot.command(name='join')
async def join(ctx):
    """Joins the voice channel"""
    if not ctx.message.author.voice:
        await ctx.send("You are not in a voice channel!")
        return
    channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='leave')
async def leave(ctx):
    """Leaves the voice channel"""
    voice_client = ctx.guild.voice_client
    if voice_client:
        await voice_client.disconnect()

@bot.command(name='play')
async def play(ctx, *, query):
    """Plays music from Spotify by querying song name and artist"""
    try:
        server = ctx.message.guild
        voice_channel = server.voice_client

        # Search on Spotify
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
            voice_channel.play(player, after=lambda e: print(f"Player error: {e}") if e else None)

        await ctx.send(f'Now playing: {track_name} by {artist_name}')
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command(name='stop')
async def stop(ctx):
    """Stops playing music"""
    voice_client = ctx.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()

bot.run(DISCORD_BOT_TOKEN)
