import discord
import discord.ext.commands
import asyncio
import logging
import yt_dlp
import os
import shutil
from yt_dlp.utils import DownloadError, ExtractorError
from typing import Any, TypedDict, IO, cast

# Copyright (c) 2026 Dennis Plischke.
# All rights reserved.

# ================================================================
# Module: Player.py
# Description: Music player functionality
# Error handling for ffmpeg and yt-dlp operations included
# ================================================================

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

# Helper to detect Node.js runtime
def get_js_runtime() -> str | None:
    # Auto-detect JavaScript runtime for yt-dlp
    # Try Node.js first (most common)
    node_candidates = ["node", "node.exe", "nodejs"]
    for candidate in node_candidates:
        runtime = shutil.which(candidate)
        if runtime:
            return runtime
    return None

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
            "player_client": ["web", "tv", "android"],  # More flexible clients
            "skip": ["hls", "dash"],  # Avoid problematic formats on Pi
        }
    },
    "match_filter": {"!is_live": True, "duration": lambda d: d <= 600},
    # YouTube Bot Detection Bypass
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    # JavaScript Runtime for signature solving
    "js_interpreter": get_js_runtime(),  # Auto-detect Node.js
}

BASE_FFMPEG_OPTIONS: FFmpegParams = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 10 -rw_timeout 20000000",
    "options": "-vn -q:a 5",  # -q:a 5 for better quality/speed balance on Pi
}


def resolve_ffmpeg_executable() -> str:
# Resolve the ffmpeg executable path with error handling

    # Check environment variable first
    env_path = os.getenv("FFMPEG_PATH")
    if env_path:
        if os.path.isfile(env_path):
            return env_path
        else:
            raise PlayerError(f"FFMPEG_PATH is set to '{env_path}' but file not found. Check the path.")
    
    # Check PATH for ffmpeg
    for candidate in ("ffmpeg", "ffmpeg.exe"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    
    # Detailed error message with instructions
    error_msg = (
        "ffmpeg not found. Please install ffmpeg:\n"
        "  - Linux: sudo apt install ffmpeg\n"
        "  - macOS: brew install ffmpeg\n"
        "  - Windows: Download from https://ffmpeg.org/download.html\n"
        "  - Or set FFMPEG_PATH environment variable"
    )
    raise PlayerError(error_msg)


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
    """Extract audio information from a query using yt-dlp with error handling."""

    try:
        with yt_dlp.YoutubeDL(cast(Any, YTDLP_OPTIONS)) as ydl:
            try:
                info = ydl.extract_info(query, download=False)
            except DownloadError as e:
                error_str = str(e)
                # YouTube Bot Detection - provide helpful message
                if "Sign in to confirm you're not a bot" in error_str:
                    raise PlayerError(
                        "YouTube blocked this video (bot detection). "
                        "Please try another video or wait a few minutes. "
                        "Ensure Node.js is installed for better YouTube access."
                    )
                # Video not found, age-restricted, or removed
                raise PlayerError(f"Cannot download: {error_str[:100]}")
            except ExtractorError as e:
                error_str = str(e)
                # Signature solving issues
                if "Signature solving failed" in error_str or "n challenge solving failed" in error_str:
                    raise PlayerError(
                        "YouTube signature solving failed. "
                        "Ensure Node.js is installed: `npm install -g node` "
                        "or check: https://github.com/yt-dlp/yt-dlp/wiki/EJS"
                    )
                # Extractor-specific error (wrong platform, auth required, etc.)
                raise PlayerError(f"Extractor error: {error_str[:100]}")
            except (TimeoutError, Exception) as e:
                # Network timeout or connection error
                raise PlayerError(f"Network timeout while searching: {str(e)[:100]}")

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
    except PlayerError:
        raise  # Re-raise PlayerError as-is
    except Exception as e:
        logging.error(f"Unexpected error during audio extraction: {e}")
        raise PlayerError(f"Audio extraction failed: {str(e)[:100]}")
        
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
        # Validate song URL before creating FFmpeg source
        if not song.get("url"):
            logging.error(f"Invalid song: no URL available for '{song.get('title', 'Unknown')}'")
            # Skip to next song instead of stopping
            await play_next(guild)
            return
        
        # Create FFmpeg source with timeout handling
        try:
            source = discord.FFmpegPCMAudio(song["url"], **get_ffmpeg_options())
        except FileNotFoundError as e:
            raise PlayerError(f"ffmpeg executable not found: {e}")
        except ValueError as e:
            # Invalid URL or codec
            logging.warning(f"Invalid audio source for '{song.get('title', 'Unknown')}': {e}")
            raise PlayerError(f"Invalid audio source: {str(e)[:100]}")
        
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
        
    except PlayerError as e:
        logging.error(f"Player error: {e}")
        state["playing"] = False
        state["current"] = None
        # Try next song instead of stopping
        await play_next(guild)
    except discord.ClientException as e:
        logging.error(f"Discord error while playing: {e}")
        state["playing"] = False
        state["current"] = None
        # Try next song
        await play_next(guild)
    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str or "timeout" in error_str:
            logging.warning(f"Network issue while starting playback: {e}")
        else:
            logging.error(f"Unexpected error during playback: {e}")
        state["playing"] = False
        state["current"] = None
        # Try next song instead of stopping
        await play_next(guild)

# Add a song to the queue
async def add_to_queue(guild: discord.Guild, query: str):
# Add a song to the queue with error handling.

    state = get_guild_state(guild.id)

    if len(state["queue"]) >= max_queue_size:
        raise PlayerError(f"Queue limit reached ({max_queue_size} tracks).")

    try:
        song = extract_audio(query)
    except PlayerError as e:
        # Re-raise player errors (already formatted)
        raise
    except Exception as e:
        logging.error(f"Unexpected error extracting audio: {e}")
        raise PlayerError(f"Failed to add track: {str(e)[:100]}")
    
    state["queue"].append(song)

    if not state["playing"]:
        await play_next(guild)

    return song

# ------------------------------------------------------------
# Controls
# ------------------------------------------------------------

# Pause, Resume, Stop

def pause(guild_id: int):
# Pause playback with error handling.

    state = music_state.get(guild_id)
    if not state:
        logging.warning(f"No music state for guild {guild_id}")
        return
    
    voice_client = state.get("voice_client")
    if not voice_client:
        logging.warning(f"No voice client for guild {guild_id}")
        return
    
    try:
        if voice_client.is_playing():
            voice_client.pause()
            logging.info(f"Playback paused for guild {guild_id}")
        else:
            logging.debug(f"Nothing playing to pause in guild {guild_id}")
    except discord.ClientException as e:
        logging.error(f"Discord error while pausing: {e}")
    except Exception as e:
        logging.error(f"Unexpected error while pausing: {e}")


def resume(guild_id: int):
# Resume playback with error handling.

    state = music_state.get(guild_id)
    if not state:
        logging.warning(f"No music state for guild {guild_id}")
        return
    
    voice_client = state.get("voice_client")
    if not voice_client:
        logging.warning(f"No voice client for guild {guild_id}")
        return
    
    try:
        if voice_client.is_paused():
            voice_client.resume()
            logging.info(f"Playback resumed for guild {guild_id}")
        else:
            logging.debug(f"Playback not paused in guild {guild_id}")
    except discord.ClientException as e:
        logging.error(f"Discord error while resuming: {e}")
    except Exception as e:
        logging.error(f"Unexpected error while resuming: {e}")

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
# Cleanup all voice connections and clear music state before shutdown.

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