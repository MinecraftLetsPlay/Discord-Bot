import discord
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
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
    "extract_flat": False,
    "skip_download": True,
    "nocheckcertificate": True,
    "retries": 3,
    "fragment_retries": 3,
    "concurrent_fragment_downloads": 1,
    "http_chunk_size": 10485760,
    "js_runtimes": {"node": {}},
    "remote_components": ["ejs:github"],
    "match_filter": {"!is_live": True, "duration": lambda d: d <= 600}
}

BASE_FFMPEG_OPTIONS: FFmpegParams = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
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
        # Repeat current song: re-add it to front of queue
        song = current
    elif repeat_mode == "all" and current and not state["queue"]:
        # Repeat all queue: if queue is empty and we had a song, restart
        song = current
    else:
        # Normal playback: get next song from queue
        if not state["queue"]:
            state["playing"] = False
            state["current"] = None
            return
        
        song = state["queue"].pop(0)
    
    state["current"] = song
    state["playing"] = True
    
    # Get or reuse voice client
    vc = state["voice_client"] or guild.voice_client
    if not vc:
        logging.warning(f"No voice client for guild {guild.id}, stopping playback.")
        state["playing"] = False
        state["current"] = None
        return

    voice_client = cast(discord.VoiceClient, vc)
    state["voice_client"] = voice_client

    source = discord.FFmpegPCMAudio(song["url"], **get_ffmpeg_options())
    loop = vc.client.loop  # use bot loop for thread-safe scheduling

    def after_play(error):
        if error:
            logging.error(f"Playback error: {error}")
        loop.call_soon_threadsafe(asyncio.create_task, play_next(guild))

    voice_client.play(source, after=after_play)

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