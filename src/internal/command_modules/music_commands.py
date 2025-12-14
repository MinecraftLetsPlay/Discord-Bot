import discord
import logging
from discord.ext import commands
from internal.utils import load_server_config, save_server_config

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
    
    async def set_music_channel(message, user_message):
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

    async def join_voice_channel(message, user_message, client):
        if user_message.startswith("!join"):
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
        
    # ----------------------------------------------------------------
    # Command: !leave
    # Description: Bot leaves the current voice channel
    # ----------------------------------------------------------------

    async def leave_voice_channel(message, user_message):
        if user_message != "!leave":
            return

        if not message.guild:
            return

        if not await is_music_channel(message):
            return

        vc = message.guild.voice_client
        
        if not vc:
            await message.channel.send("❌ Im not connected to any voice channel.")
            logging.debug("Leave command issued but bot is not in a voice channel.")
            return

        await vc.disconnect()
        await message.channel.send("👋 Left the voice channel.")
