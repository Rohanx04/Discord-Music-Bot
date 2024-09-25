Here is a sample `README.md` file you can use for your GitHub repository:

---

# Discord Music Bot with Rich Presence

## Description

This is a **Discord Music Bot** that allows users to play music in their voice channels, with integrated **Spotify API** for song search. It features **YouTube streaming** via `yt-dlp`, custom command functionality for managing playback, and a **Rich Presence** feature that displays the currently playing song only in the active server where the bot is playing music. When the bot is not playing any music, it displays an "Idle" status.

## Features

- 🎵 **Play Music**: Play music from YouTube or search songs via the Spotify API.
- 📜 **Queue Management**: Add songs to the queue, display the current queue, and shuffle the queue.
- 🔄 **Looping**: Loop the current song or the entire queue.
- ⏯️ **Pause/Resume**: Pause and resume playback.
- ⏭️ **Skip Songs**: Skip to the next song in the queue.
- 🔈 **Volume Control**: Adjust the playback volume.
- ⏹️ **Stop Playback**: Clear the queue and stop the music.
- 👂 **Rich Presence**: The bot displays the currently playing song in the server it is active in, with an idle status when not playing.

## Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Spotify API Client ID and Secret
- FFmpeg installed and accessible via the command line

### Install FFmpeg
You need to have FFmpeg installed and available in your system's PATH. You can download it from [here](https://ffmpeg.org/download.html).

## Setup Instructions

### Clone the Repository
```bash
git clone https://github.com/your-username/your-repository.git
cd your-repository
```

### Install Required Dependencies
Install the required Python dependencies using `pip`:

```bash
pip install -r requirements.txt
```

### Set Up Environment Variables

You will need to create a `.env` file in the root of the project with the following content:

```
DISCORD_BOT_TOKEN=your-discord-bot-token
SPOTIPY_CLIENT_ID=your-spotify-client-id
SPOTIPY_CLIENT_SECRET=your-spotify-client-secret
```

Replace the values with your own **Discord Bot Token** and **Spotify API credentials**.

### Run the Bot

To run the bot, use the following command:

```bash
python bot.py
```

Make sure the bot is connected to a voice channel in your server, and use the commands to start playing music!

## Commands

### General Commands
- `!join` - The bot joins your current voice channel.
- `!leave` - The bot leaves the current voice channel.
- `!play <song>` - Search for a song and play it from YouTube.
- `!pause` - Pause the current song.
- `!resume` - Resume the paused song.
- `!stop` - Stop playback and clear the queue.
- `!skip` - Skip to the next song in the queue.
- `!queue` - Show the current song queue.
- `!volume <volume>` - Set the playback volume (0-100).
- `!loop <song|queue|off>` - Loop the current song, the entire queue, or turn off looping.
- `!shuffle` - Shuffle the current queue.
- `!nowplaying` - Show the currently playing song.

### Rich Presence Behavior
- The bot will display the **currently playing song** in the Discord Rich Presence when active in a server.
- When the bot is not playing any song, it will show an **"Idle"** status.
- The presence is updated only for the server where music is being played, and the bot will remain idle in other servers.

## Troubleshooting

### Common Issues
- **Bot Not Playing Music**: Ensure FFmpeg is installed and added to the system's PATH.
- **Spotify API Errors**: Ensure your Spotify API credentials are correct and the environment variables are set up properly.
- **Rich Presence Not Updating**: Discord limits how often bot presences can be updated. If the presence isn't updating as expected, ensure your bot is following the correct update logic.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Feel free to replace the placeholders such as `your-username` and `your-repository` with the actual repository URL and customize the details as necessary.