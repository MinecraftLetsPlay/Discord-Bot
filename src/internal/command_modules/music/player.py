import discord
import discord.ext.commands
import asyncio
import logging
import yt_dlp
import os
import shutil
from typing import Any, TypedDict, IO, cast

# Copyright (c) 2025 Dennis Plischke.
# All rights reserved.

# ----------------------------------------------------------------
# Module: Player.py
# Description: Music player functionality
# ----------------------------------------------------------------

# ----------------------------------------------------------------
# Helper Functions and Initial Setup
# ----------------------------------------------------------------

VOICE_TIMEOUT = 30.0
FFMPEG_TIMEOUT = 10.0

bot_loop = None
music_state = {}
max_queue_size = 50

class PlayerError(Exception):
    """Raised when playback prerequisites are missing (e.g., ffmpeg)."""

# Setup bot loop
def get_guild_state(guild_id: int):
    if guild_id not in music_state:
        music_state[guild_id] = {
            "queue": [],
            "current": None,
            "voice_client": None,
            "playing": False,
            "repeat_mode": "off"  # off, one, or all
        }
    return music_state[guild_id]

# Youtube-dl and FFMPEG parameter types
YtDlpParams = dict[str, Any]

class FFmpegParams(TypedDict, total=False):
    executable: str
    pipe: bool
    stderr: IO[bytes] | None
    before_options: str
    options: str

# ----------------------------------------------------------------
# yt-dlp Options
# ----------------------------------------------------------------

YTDLP_OPTIONS: YtDlpParams = {
    "format": "bestaudio[ext=m4a]/bestaudio",  # Prefer m4a for better compatibility
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
    "extract_flat": False,
    "skip_download": True,
    "nocheckcertificate": True,
    "retries": 5,  # Increased retries for Pi stability
    "fragment_retries": 5,  # More resilient to network issues
    "concurrent_fragment_downloads": 1,
    "http_chunk_size": 1048576,  # Smaller chunks for Raspberry Pi (1MB instead of 10MB)
    "socket_timeout": 30,  # Add explicit socket timeout
    "extractor_args": {
        "youtube": {
            "player_client": ["web", "tv"],  # More flexible clients
            "skip": ["hls", "dash"],  # Avoid problematic formats on Pi
        }
    },
    "match_filter": {"!is_live": True, "duration": lambda d: d <= 600}
}

BASE_FFMPEG_OPTIONS: FFmpegParams = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 10 -rw_timeout 20000000",
    "options": "-vn -q:a 5",  # -q:a 5 for better quality/speed balance on Pi
}


def resolve_ffmpeg_executable() -> str:
    env_path = os.getenv("FFMPEG_PATH")
    if env_path and shutil.which(env_path):
        return env_path
    for candidate in ("ffmpeg", "ffmpeg.exe"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise PlayerError("ffmpeg was not found. Install ffmpeg or set FFMPEG_PATH.")


def get_ffmpeg_options() -> FFmpegParams:
    executable = resolve_ffmpeg_executable()
    opts: FFmpegParams = {"executable": executable}
    opts.update(BASE_FFMPEG_OPTIONS)
    return opts

# ----------------------------------------------------------------
# Search and Extract
# ----------------------------------------------------------------

# Extract audio information using yt-dlp
def extract_audio(query: str):
    with yt_dlp.YoutubeDL(cast(Any, YTDLP_OPTIONS)) as ydl:
        info = ydl.extract_info(query, download=False)

        if not info:
            raise PlayerError("No results found.")

        if "entries" in info:
            info = info["entries"][0]

        return {
            "title": info.get("title"),
            "url": info.get("url"),
            "webpage_url": info.get("webpage_url"),
            "duration": info.get("duration"),
        }
        
# ------------------------------------------------------------
# Playback Logic
# ------------------------------------------------------------

# Play the next song in the queue
async def play_next(guild: discord.Guild):
    state = get_guild_state(guild.id)
    repeat_mode = state.get("repeat_mode", "off")
    current = state.get("current")

    # Handle repeat modes
    if repeat_mode == "one" and current:
        song = current
    elif repeat_mode == "all" and current and not state["queue"]:
        song = current
    else:
        if not state["queue"]:
            state["playing"] = False
            state["current"] = None
            return
        
        song = state["queue"].pop(0)
    
    state["current"] = song
    state["playing"] = True
    
    # ✅ WICHTIG: Immer guild.voice_client verwenden, nicht state["voice_client"]
    vc = guild.voice_client
    if not vc:
        logging.warning(f"No active voice connection for guild {guild.id}")
        state["playing"] = False
        state["current"] = None
        return
    
    # Cast to VoiceClient for type checking
    voice_client = cast(discord.VoiceClient, vc)
    
    try:
        source = discord.FFmpegPCMAudio(song["url"], **get_ffmpeg_options())
        loop = voice_client.client.loop
        
        def after_play(error):
            if error:
                error_str = str(error).lower()
                # Ignore harmless reconnect messages from FFmpeg
                if "connection reset" in error_str or "io error" in error_str:
                    logging.warning(f"Network blip during playback (expected on unstable connections): {error}")
                else:
                    logging.error(f"Playback error: {error}")
            loop.call_soon_threadsafe(asyncio.create_task, play_next(guild))
        
        voice_client.play(source, after=after_play)
        logging.info(f"Now playing: {song['title']} on guild {guild.id}")
        
    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str or "timeout" in error_str:
            logging.warning(f"Network issue while starting playback: {e}")
            state["playing"] = False
            state["current"] = None
            # Try next song instead of stopping
            await play_next(guild)
        else:
            logging.error(f"Failed to play audio: {e}")
            state["playing"] = False
            state["current"] = None

# Add a song to the queue
async def add_to_queue(guild: discord.Guild, query: str):
    state = get_guild_state(guild.id)

    if len(state["queue"]) >= max_queue_size:
        raise PlayerError(f"Queue limit reached ({max_queue_size} tracks).")

    song = extract_audio(query)
    state["queue"].append(song)

    if not state["playing"]:
        await play_next(guild)

    return song

# ------------------------------------------------------------
# Controls
# ------------------------------------------------------------

# Pause, Resume, Stop

def pause(guild_id: int):
    state = music_state.get(guild_id)
    if state and state["voice_client"]:
        state["voice_client"].pause()


def resume(guild_id: int):
    state = music_state.get(guild_id)
    if state and state["voice_client"]:
        state["voice_client"].resume()

# Graceful Stop
async def stop(guild_id: int):
    state = get_guild_state(guild_id)
    voice_client = state.get("voice_client")
    
    if voice_client:
        try:
            # Give FFmpeg time to gracefully stop
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                
                # Wait for FFmpeg to terminate properly
                import asyncio
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logging.error(f"Error stopping playback: {e}")
    
    # Clear queue and reset state
    state["queue"].clear()
    state["current"] = None
    state["playing"] = False
    logging.info(f"Playback stopped for guild {guild_id}")

# Graceful Disconnect
async def disconnect(guild_id: int):
    state = get_guild_state(guild_id)
    voice_client = state.get("voice_client")
    
    if voice_client:
        try:
            # Stop playback first
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                
                # Give FFmpeg time to terminate
                import asyncio
                await asyncio.sleep(0.5)
            
            # Disconnect
            await voice_client.disconnect(force=True)
            
        except Exception as e:
            logging.error(f"Error disconnecting: {e}")
        finally:
            state["voice_client"] = None
            state["queue"].clear()
            state["current"] = None
            state["playing"] = False
    
    logging.info(f"Disconnected from voice for guild {guild_id}")

async def cleanup_all_guilds(bot: discord.ext.commands.Bot):
    """Cleanup all voice connections and clear music state before shutdown."""
    try:
        for guild in bot.guilds:
            try:
                vc = guild.voice_client
                if vc:
                    await disconnect(guild.id)
                    logging.info(f"Disconnected from voice in guild {guild.id} during cleanup")
            except Exception as e:
                logging.error(f"Error disconnecting from guild {guild.id}: {e}")
        
        # Clear all music states
        music_state.clear()
        logging.info("Music state cleaned up")
    except Exception as e:
        logging.error(f"Error during music cleanup: {e}")