import discord
import logging
from internal.utils import load_server_config, save_server_config
from internal.command_modules.music import player

# Copyright (c) 2025 Dennis Plischke.
# All rights reserved.

# ----------------------------------------------------------------
# Module: Music_commands.py
# Description: Handles music related commands
# ----------------------------------------------------------------

# ----------------------------------------------------------------
# Helper Functions and Initial Setup
# ----------------------------------------------------------------

# Helper function to check if command is used in the designated music channel
async def is_music_channel(message):
    if not message.guild:
        return False  # keine DMs

    cfg = load_server_config(message.guild.id)
    music_channel_id = cfg.get("music_channel_id")

    if music_channel_id is None:
        await message.channel.send("❌ Music channel is not set. Please set it using !music-channel command.")
        logging.warning(f"Music channel not set for guild {message.guild.id}")
        return False

    if message.channel.id != int(music_channel_id):
        await message.channel.send(
            f"❌ Please use the designated Music-Channel <#{music_channel_id}>."
        )
        logging.debug(f"Wrong music channel used: {message.channel.id} (expected {music_channel_id})")
        return False

    return True

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
            await message.channel.send("❌ Please specify a voice channel name or ID to join.")
            logging.debug("No voice channel specified in !join command.")
            return
        
        try:
            channel_id = int(parts[1])
        except ValueError:
            await message.channel.send("❌ Invalid channel ID. Please provide a numeric channel ID.")
            logging.debug(f"Invalid channel ID provided: {parts[1]}")
            return
        
        channel = message.guild.get_channel(channel_id)
        
        if channel is None or not isinstance(channel, discord.VoiceChannel):
            await message.channel.send("❌ Specified channel is not a valid voice channel.")
            logging.debug(f"Channel ID {channel_id} is not a valid voice channel.")
            return
        
        if message.guild.voice_client:
            await message.guild.voice_client.disconnect()
            
        await channel.connect()
        await message.channel.send(f"Joined voice channel: {channel.name}")
        vc = message.guild.voice_client
        state = player.get_guild_state(message.guild.id)
        state["voice_client"] = vc

        
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
        await vc.disconnect()
        state = player.get_guild_state(message.guild.id)
        state["voice_client"] = None
        state["playing"] = False
        state["current"] = None
        state["queue"].clear()
        await message.channel.send("👋 Left the voice channel.")
        return

    # ----------------------------------------------------------------
    # Command: !play <query or URL>
    # ----------------------------------------------------------------
    if user_message.startswith("!play"):
        if not message.guild or not await is_music_channel(message):
            return
        vc = message.guild.voice_client
        if not vc:
            await message.channel.send("❌ I'm not connected to a voice channel. Use !join first.")
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
            await message.channel.send("❌ Could not add the track. Check the query/URL.")

    # ----------------------------------------------------------------
    # Command: !pause / !resume
    # ----------------------------------------------------------------
    if user_message == "!pause":
        if message.guild and await is_music_channel(message):
            player.pause(message.guild.id)
            await message.channel.send("⏸️ Paused.")
        return

    if user_message == "!resume":
        if message.guild and await is_music_channel(message):
            player.resume(message.guild.id)
            await message.channel.send("▶️ Resumed.")
        return

    # ----------------------------------------------------------------
    # Command: !skip (stop current, continue queue)
    # ----------------------------------------------------------------
    if user_message == "!skip":
        if not message.guild or not await is_music_channel(message):
            return
        vc = message.guild.voice_client
        if not vc or not vc.is_playing():
            await message.channel.send("ℹ️ Nothing is playing.")
            return
        vc.stop()  # triggers after-callback to play_next
        await message.channel.send("⏭️ Skipped.")
        return

    # ----------------------------------------------------------------
    # Command: !stop (clear queue + stop)
    # ----------------------------------------------------------------
    if user_message == "!stop":
        if message.guild and await is_music_channel(message):
            player.stop(message.guild.id)
            await message.channel.send("⏹️ Stopped and cleared the queue.")
        return

    # ----------------------------------------------------------------
    # Command: !queue
    # ----------------------------------------------------------------
    if user_message == "!queue":
        if not message.guild or not await is_music_channel(message):
            return
        state = player.get_guild_state(message.guild.id)
        if not state["queue"]:
            await message.channel.send("📭 Queue is empty.")
            return
        lines = [f"{idx+1}. {item['title']}" for idx, item in enumerate(state['queue'])]
        await message.channel.send("📜 Queue:\n" + "\n".join(lines))
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
            await message.channel.send("ℹ️ Nothing is playing.")
            return
        await message.channel.send(f"🎶 Now playing: **{current['title']}**")
        return
