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
            "playing": False
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

    if not state["queue"]:
        state["playing"] = False
        state["current"] = None
        return

    song = state["queue"].pop(0)
    state["current"] = song
    state["playing"] = True

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


def stop(guild_id: int):
    state = music_state.get(guild_id)
    if state and state["voice_client"]:
        state["queue"].clear()
        state["voice_client"].stop()
        state["playing"] = False
        state["current"] = None