import discord
import logging
from discord import ui
from internal.utils import load_server_config, save_server_config
from internal.command_modules.music import player
from internal.command_modules.music.player import PlayerError

# Copyright (c) 2025 Dennis Plischke.
# All rights reserved.

# ----------------------------------------------------------------
# Module: Music_commands.py
# Description: Handles music related commands
# ----------------------------------------------------------------

# ----------------------------------------------------------------
# Helper Functions and Initial Setup
# ----------------------------------------------------------------

# Constants for queue pagination
QUEUE_ITEMS_PER_PAGE = 10

# Use a Discord UI View for queue pagination
class QueueView(ui.View):
    
    # Initialize the view with buttons
    def __init__(self, guild_id: int, current_page: int = 0):
        super().__init__(timeout=180)  # 3 minutes timeout
        self.guild_id = guild_id
        self.current_page = current_page
        self._update_button_states()
    
    # Update button states based on current page
    def _update_button_states(self):
        state = player.get_guild_state(self.guild_id)
        queue = state.get("queue", [])
        total_pages = (len(queue) + QUEUE_ITEMS_PER_PAGE - 1) // QUEUE_ITEMS_PER_PAGE if queue else 1
        
        # Disable buttons at boundaries
        for item in self.children:
            if hasattr(item, 'label') and hasattr(item, 'disabled'):
                if item.label == "⬅️ Previous":  # type: ignore
                    item.disabled = self.current_page <= 0  # type: ignore
                elif item.label == "➡️ Next":  # type: ignore
                    item.disabled = self.current_page >= total_pages - 1  # type: ignore
    
    # Previous page button
    @ui.button(label="⬅️ Previous", style=discord.ButtonStyle.blurple)
    async def previous_page(self, interaction: discord.Interaction, button: ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)
    
    # Netx page button
    @ui.button(label="➡️ Next", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: ui.Button):
        state = player.get_guild_state(self.guild_id)
        queue = state.get("queue", [])
        total_pages = (len(queue) + QUEUE_ITEMS_PER_PAGE - 1) // QUEUE_ITEMS_PER_PAGE if queue else 1
        
        if self.current_page < total_pages - 1:
            self.current_page += 1
            await self.update_message(interaction)
    
    # Update the message with new page content
    async def update_message(self, interaction: discord.Interaction):
        embed = create_queue_embed(self.guild_id, self.current_page)
        self._update_button_states()
        await interaction.response.edit_message(embed=embed, view=self)
    
    # Disable buttons on timeout
    async def on_timeout(self):
        for item in self.children:
            if hasattr(item, 'disabled'):
                item.disabled = True  # type: ignore

# Create embed for queue display
def create_queue_embed(guild_id: int, page: int = 0) -> discord.Embed:
    state = player.get_guild_state(guild_id)
    queue = state.get("queue", [])
    current = state.get("current")
    
    # Calculate pagination information
    total_items = len(queue)
    total_pages = (total_items + QUEUE_ITEMS_PER_PAGE - 1) // QUEUE_ITEMS_PER_PAGE if total_items > 0 else 1
    start_idx = page * QUEUE_ITEMS_PER_PAGE
    end_idx = min(start_idx + QUEUE_ITEMS_PER_PAGE, total_items)
    
    # Create the embed
    embed = discord.Embed(
        title="🎵 Music Queue",
        color=discord.Color.from_rgb(88, 173, 218),  # Nice blue
        description="Current playback queue"
    )
    
    # Currently playing song
    if current:
        duration_str = ""
        if current.get("duration"):
            mins, secs = divmod(current["duration"], 60)
            duration_str = f" | ⏱️ {mins}:{secs:02d}"
        embed.add_field(
            name="▶️ Now Playing",
            value=f"**{current['title']}**{duration_str}",
            inline=False
        )
    
    # Queue items
    if total_items == 0:
        embed.add_field(
            name="📭 Queue is empty",
            value="Use `!play [Song/URL]` to add music!",
            inline=False
        )
    else:
        # Build queue text for current page
        queue_text = ""
        for idx in range(start_idx, end_idx):
            item = queue[idx]
            duration_str = ""
            if item.get("duration"):
                mins, secs = divmod(item["duration"], 60)
                duration_str = f" | ⏱️ {mins}:{secs:02d}"
            queue_text += f"{idx+1}. **{item['title']}**{duration_str}\n"
        
        embed.add_field(
            name=f"📜 Queue ({start_idx+1}-{end_idx} of {total_items})",
            value=queue_text,
            inline=False
        )
    
    # Footer with page info
    embed.set_footer(text=f"Page {page+1}/{total_pages}")
    
    return embed

# Create embed for now playing display
def create_nowplaying_embed(guild_id: int) -> discord.Embed:
    state = player.get_guild_state(guild_id)
    current = state.get("current")
    voice_client = state.get("voice_client")
    
    # If nothing is playing
    if not current:
        embed = discord.Embed(
            title="🎶 Now Playing",
            color=discord.Color.from_rgb(88, 173, 218),
            description="Nothing is playing."
        )
        return embed
    
    # Extract song information
    title = current.get("title", "Unknown")
    duration = current.get("duration", 0)
    thumbnail = current.get("thumbnail", "")
    webpage_url = current.get("webpage_url", "")
    
    # Create embed with title and description
    embed = discord.Embed(
        title="🎶 Now Playing",
        description=f"**{title}**",
        color=discord.Color.from_rgb(88, 173, 218),
        url=webpage_url if webpage_url else None
    )
    
    # Add thumbnail if available
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    # Add duration field
    if duration > 0:
        total_mins, total_secs = divmod(duration, 60)
        time_str = f"⏱️ `{total_mins}:{total_secs:02d}`"
        embed.add_field(
            name="Duration",
            value=time_str,
            inline=False
        )
    else:
        embed.add_field(
            name="⏱️ Duration",
            value="Unknown duration",
            inline=False
        )
    
    # Add status
    if voice_client:
        if voice_client.is_playing():
            status = "▶️ Playing"
        elif voice_client.is_paused():
            status = "⏸️ Paused"
        else:
            status = "⏹️ Stopped"
    else:
        status = "⏹️ Not connected"
    
    embed.add_field(
        name="Status",
        value=status,
        inline=True
    )
    
    # Add queue position
    queue = state.get("queue", [])
    queue_position = len(queue)
    embed.add_field(
        name="Queue",
        value=f"**{queue_position}** song(s) in queue",
        inline=True
    )
    
    return embed

# Helper function to check if command is used in the designated music channel
async def is_music_channel(message):
    if not message.guild:
        return False  # No DMs
    
    # Load server config
    cfg = load_server_config(message.guild.id)
    music_channel_id = cfg.get("music_channel_id")
    
    # If no music channel set
    if music_channel_id is None:
        await message.channel.send("❌ Music channel is not set. Please set it using !music-channel command.")
        logging.warning(f"Music channel not set for guild {message.guild.id}")
        return False
    
    # Check if used in the correct channel
    if message.channel.id != int(music_channel_id):
        await message.channel.send(
            f"❌ Please use the designated music channel <#{music_channel_id}>."
        )
        logging.debug(f"Wrong music channel used: {message.channel.id} (expected {music_channel_id})")
        return False

    return True

# ----------------------------------------------------------------
# Component test function for [Music Commands]
# ----------------------------------------------------------------

async def component_test():
    status = "🟩"
    messages = ["Music commands module loaded."]

    # Test 1: Check if ffmpeg is available
    try:
        from internal.command_modules.music.player import resolve_ffmpeg_executable
        ffmpeg_exec = resolve_ffmpeg_executable()
        if ffmpeg_exec:
            messages.append(f"FFmpeg found: {ffmpeg_exec}")
        else:
            status = "🟧"
            messages.append("Warning: FFmpeg not found.")
    except PlayerError as e:
        status = "🟧"
        messages.append(f"Warning: {e}")
    except Exception as e:
        status = "🟧"
        messages.append(f"Warning: FFmpeg check failed: {e}")

    # Test 2: Check music channel config
    try:
        from internal.utils import load_config
        cfg = load_config()
        messages.append("Config loaded.")
    except Exception as e:
        status = "🟧"
        messages.append(f"Warning: Config load failed: {e}")
    
    # Test 3: Check if player.py module is functional
    try:
        test_guild_id = 0  # Dummy guild ID for testing
        state = player.get_guild_state(test_guild_id)
        if isinstance(state, dict):
            messages.append("Player module functional.")
        else:
            status = "🟧"
            messages.append("Warning: Player module returned invalid state.")
    except Exception as e:
        status = "🟧"
        messages.append(f"Warning: Player module test failed: {e}")

    return {"status": status, "msg": " | ".join(messages)}

# ----------------------------------------------------------------
# Main command handler for music commands
# ----------------------------------------------------------------

async def handle_music_commands(client, message, user_message):
    # ----------------------------------------------------------------
    # Command: !music-channel
    # Description: Sets the current channel as the music channel
    # ----------------------------------------------------------------
    
    if user_message.startswith("!music-channel"):
        if not message.guild:
            return
    
        guild_id = message.guild.id
        cfg = load_server_config(guild_id)
    
        cfg["music_channel_id"] = message.channel.id
        save_server_config(guild_id, cfg)
    
        await message.channel.send(f"Music channel has been set to <#{message.channel.id}>.")
        logging.debug(f"Set music channel to {message.channel.id} for guild {guild_id}.")
        
    # ----------------------------------------------------------------
    # Command: !join <channel_id>
    # Description: Bot joins the specified voice channel
    # ----------------------------------------------------------------

    if user_message == "!join" or user_message.startswith("!join"):
        if not message.guild:
            return

        if not await is_music_channel(message):
            return
        
        parts = user_message.split()
        
        if len(parts) < 2:
            # No channel ID provided, use author's current voice channel
            if message.author.voice and message.author.voice.channel:
                channel = message.author.voice.channel
            else:
                await message.channel.send("❌ Join a voice channel or specify one.")
                return
        else:
            # Channel ID provided
            try:
                channel_id = int(parts[1])
            except ValueError:
                await message.channel.send("❌ Invalid channel ID. Please provide a numeric channel ID.")
                logging.debug(f"Invalid channel ID provided: {parts[1]}")
                return
            
            channel = message.guild.get_channel(channel_id)
            
            # Validate channel
            if channel is None or not isinstance(channel, discord.VoiceChannel):
                await message.channel.send("❌ Specified channel is not a valid voice channel.")
                logging.debug(f"Channel ID {channel_id} is not a valid voice channel.")
                return
        
        if message.guild.voice_client:
            await message.guild.voice_client.disconnect()
            
        await channel.connect()
        await message.channel.send(f"**Joined voice channel: {channel.name}**")
        vc = message.guild.voice_client
        state = player.get_guild_state(message.guild.id)
        state["voice_client"] = vc
        return

    # ----------------------------------------------------------------
    # Command: !leave
    # Description: Bot leaves the current voice channel
    # ----------------------------------------------------------------

    if user_message == "!leave":
        if not message.guild:
            return
        if not await is_music_channel(message):
            return
        
        vc = message.guild.voice_client
        if not vc:
            await message.channel.send("❌ I'm not connected to a voice channel.")
            return
        
        # Use new graceful disconnect function
        await player.disconnect(message.guild.id)
        await message.channel.send("👋 **Left the voice channel.**")
        return

    # ----------------------------------------------------------------
    # Command: !play <query or URL>
    # ----------------------------------------------------------------
    
    if user_message.startswith("!play"):
        if not message.guild or not await is_music_channel(message):
            return
        
        # ✅ Prüfe ob Bot wirklich verbunden ist
        vc = message.guild.voice_client
        if not vc or not vc.is_connected():
            await message.channel.send("❌ Bot is not connected. Use `!join` first.")
            logging.warning(f"Play attempted without voice connection in guild {message.guild.id}")
            return
        
        query = user_message[len("!play"):].strip()
        if not query:
            await message.channel.send("❌ Please provide a search query or URL.")
            return
        
        try:
            song = await player.add_to_queue(message.guild, query)
            await message.channel.send(f"▶️ Added to queue: **{song['title']}**")
        except player.PlayerError as e:
            logging.error(f"Play failed: {e}")
            await message.channel.send(f"❌ {e}")
        except Exception as e:
            logging.error(f"Play failed: {e}")
            await message.channel.send("❌ Could not add the track.")

    # ----------------------------------------------------------------
    # Command: !pause / !resume
    # ----------------------------------------------------------------
    
    if user_message == "!pause":
        if not message.guild or not await is_music_channel(message):
            return

        state = player.get_guild_state(message.guild.id)
        vc = state.get("voice_client")

        if not vc or not vc.is_playing():
            await message.channel.send("ℹ️ **Nothing is playing.**")
            return

        player.pause(message.guild.id)
        await message.channel.send("⏸️ **Paused.**")
        return

    if user_message == "!resume":
        if not message.guild or not await is_music_channel(message):
            return

        state = player.get_guild_state(message.guild.id)
        vc = state.get("voice_client")
        if not vc or not vc.is_paused():
            await message.channel.send("ℹ️ **Nothing to resume.**")
            return

        player.resume(message.guild.id)
        await message.channel.send("▶️ **Resumed.**")
        return

    # ----------------------------------------------------------------
    # Command: !skip (stop current, continue queue)
    # ----------------------------------------------------------------
    
    if user_message == "!skip":
        if not message.guild or not await is_music_channel(message):
            return
        vc = message.guild.voice_client
        if not vc or not vc.is_playing():
            await message.channel.send("ℹ️ **Nothing is playing.**")
            return
        vc.stop()  # triggers after-callback to play_next
        await message.channel.send("⏭️ **Skipped.**")
        return

    # ----------------------------------------------------------------
    # Command: !stop (clear queue + stop)
    # ----------------------------------------------------------------
    
    if user_message == "!stop":
        if not message.guild or not await is_music_channel(message):
            return

        state = player.get_guild_state(message.guild.id)
        vc = state.get("voice_client")

        if not vc:
            await message.channel.send("ℹ️ **Nothing to stop.**")
            return

        await player.stop(message.guild.id)

        if vc.is_playing() or vc.is_paused():
            vc.stop()

        await message.channel.send("⏹️ **Stopped playback and cleared the queue.**")
        return
    
    # ----------------------------------------------------------------
    # Command: !queue
    # ----------------------------------------------------------------
    
    if user_message == "!queue" or user_message.startswith("!queue "):
        if not message.guild or not await is_music_channel(message):
            return
        
        state = player.get_guild_state(message.guild.id)
        queue = state.get("queue", [])
        
        # Check if there is a page parameter
        page = 0
        if user_message.startswith("!queue "):
            try:
                page = int(user_message.split()[1]) - 1  # User provides 1-based page number
                if page < 0:
                    page = 0
            except (ValueError, IndexError):
                pass
        
        if not queue and not state.get("current"):
            await message.channel.send("📭 **Queue is empty.**")
            return
        
        # Create embed and view
        embed = create_queue_embed(message.guild.id, page)
        view = QueueView(message.guild.id, page)
        
        await message.channel.send(embed=embed, view=view)
        return

    # ----------------------------------------------------------------
    # Command: !nowplaying
    # ----------------------------------------------------------------
    
    if user_message == "!nowplaying":
        if not message.guild or not await is_music_channel(message):
            return
        
        state = player.get_guild_state(message.guild.id)
        current = state.get("current")
        
        if not current:
            await message.channel.send("📭 **Nothing is playing.**")
            return
        
        # Create and send the nowplaying embed
        embed = create_nowplaying_embed(message.guild.id)
        await message.channel.send(embed=embed)
        return
    
    # ----------------------------------------------------------------
    # Command: !repeat
    # ----------------------------------------------------------------
    
    if user_message == "!repeat" or user_message.startswith("!repeat "):
        if not message.guild or not await is_music_channel(message):
            return
        
        state = player.get_guild_state(message.guild.id)
        
        # Get repeat mode (one/all/off)
        mode = "all"  # Default: repeat all queue
        if user_message.startswith("!repeat "):
            mode = user_message.split()[1].lower()
        
        if mode not in ["one", "all", "off"]:
            await message.channel.send("❌ Invalid repeat mode. Use: `!repeat one`, `!repeat all`, or `!repeat off`")
            return
        
        state["repeat_mode"] = mode
        
        # Send feedback
        if mode == "one":
            await message.channel.send("🔂 **Repeat: Current song**")
        elif mode == "all":
            await message.channel.send("🔁 **Repeat: Entire queue**")
        else:
            await message.channel.send("⏹️ **Repeat: Off**")
        
        logging.debug(f"Repeat mode set to: {mode}")
        return

