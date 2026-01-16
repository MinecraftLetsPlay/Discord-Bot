import discord
import os
import sys
import asyncio
import logging as log_
from dotenv import load_dotenv
from typing import Optional
from discord import app_commands
from datetime import datetime, timedelta
from internal import utils
from internal.utils import is_authorized_global, is_authorized_server
from internal.command_modules.logging_setup import CustomTimedRotatingFileHandler
from internal import rate_limiter

# Copyright (c) 2026 Dennis Plischke.
# All rights reserved.

# ================================================================
# Module: System_commands.py
# Description: Handles system commands like /shutdown 
# and contains authorization and logging mechanisms
# ================================================================

# ----------------------------------------------------------------
# Helper Functions and Initial Setup
# ----------------------------------------------------------------

# Load environment variables from .env file
load_dotenv()

# Store the bot start time
bot_start_time = datetime.now()

last_restart_time = None

log_directory = utils.get_config_value("log_file_location", default="logs")
if not isinstance(log_directory, str) or not log_directory:
    log_directory = "logs"

# Ensure log directory exists
if not os.path.exists(log_directory):
    try:
        os.makedirs(log_directory)
    except PermissionError as e:
        print(f"Permission denied: {e}")
        sys.exit(1)
        
# ----------------------------------------------------------------
# Component test function for [System Commands]
# ----------------------------------------------------------------

def component_test():
    status = "🟩"
    messages = []

    # 1. Load config
    try:
        cfg = utils.load_config()
        if not cfg:
            status = "🟧"
            messages.append("Warning: config.json missing or empty.")
        else:
            messages.append("config.json loaded.")
    except Exception as e:
        status = "🟥"
        messages.append(f"Error loading config.json: {e}")
        
    return {"status": status, "msg": " | ".join(messages)}

# Global variable to control logging
LoggingActivated = utils.get_config_value("LoggingActivated", default=True)

# ----------------------------------------------------------------
# Logging engine (Handels logging and file naming / file deletion)
# ----------------------------------------------------------------

# Setup logging with TimedRotatingFileHandler
log_file = os.path.join(log_directory, 'bot.log')
handler = CustomTimedRotatingFileHandler(
    log_file,
    when="midnight",
    interval=1,
    backupCount=14,
    encoding="utf-8"
)

log_.basicConfig(
    level=log_.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        handler,
        log_.StreamHandler(sys.stdout)
    ]
)

# ----------------------------------------------------------------
# Helper: Blacklist Check for Slash Commands
# ----------------------------------------------------------------

# Check if user or server is blacklisted
async def check_blacklist(interaction: discord.Interaction) -> bool:
    # Check user blacklist
    if utils.is_user_blacklisted(interaction.user.id):
        await interaction.response.send_message(
            "❌ You are blacklisted from using this bot.",
            ephemeral=True
        )
        log_.warning(f"Blocked command from blacklisted user {interaction.user.id}")
        return True
    
    # Check server blacklist
    if interaction.guild and utils.is_server_blacklisted(interaction.guild.id):
        await interaction.response.send_message(
            "❌ This server is blacklisted.",
            ephemeral=True
        )
        log_.warning(f"Blocked command in blacklisted server {interaction.guild.id}")
        return True
    
    return False

# ----------------------------------------------------------------
# Main Command Handler for [System Commands]
# ----------------------------------------------------------------

def setup_system_commands(bot):
    
    # -----------------------------------------------------------------
    # Command: /shutdown
    # Category: System Commands
    # Type: Full Command
    # Description: Shut down the bot
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="shutdown", description="Shut down the bot")
    async def shutdown(interaction: discord.Interaction):
        
        # Check blacklist first
        if await check_blacklist(interaction):
            return
        
        if is_authorized_global(interaction.user):
            await interaction.response.send_message("Shutting down the bot...")
            log_.info(f"System: Shutdown command executed by: {interaction.user.id}")
            
            # Cleanup music before shutdown
            try:
                from internal.command_modules.music.player import cleanup_all_guilds
                await cleanup_all_guilds(bot)
            except Exception as e:
                log_.error(f"Error during music cleanup: {e}")
            
            await bot.close()
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            log_.info(f"Permission denied for shutdown command. User: {interaction.user.id}")

    # -----------------------------------------------------------------
    # Command: /full_shutdown
    # Category: System Commands
    # Type: Full Command
    # Description: Shut down the bot and the Raspberry Pi
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="full_shutdown", description="Shut down the bot and the Raspberry Pi")
    async def full_shutdown(interaction: discord.Interaction):
        
        # Check blacklist first
        if await check_blacklist(interaction):
            return
        
        # Authorization check
        if not is_authorized_global(interaction.user):
            await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
            return

        # Guard: ensure channel is TextChannel (not CategoryChannel, ForumChannel, etc.)
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("❌ This command can only be used in a text channel.", ephemeral=True)
            return

        # Defer the interaction first so we can handle the confirmation later
        await interaction.response.defer()

        try:
            # Send confirmation as normal message so we get a Message object
            channel = interaction.channel
            confirm_msg = await channel.send(
                f"{interaction.user.mention}, react with ✅ to confirm shutdown (30s)."
            )
            
            # Add reaction with error handling
            try:
                await confirm_msg.add_reaction('✅')
            except discord.Forbidden:
                await interaction.followup.send("❌ I don't have permission to add reactions.")
                log_.error(f"System: Missing permission to add reactions in {interaction.channel.name}")
                return

            def check(reaction, user):
                return (user == interaction.user and 
                        reaction.message.id == confirm_msg.id and 
                        str(reaction.emoji) == '✅')

            try:
                await bot.wait_for("reaction_add", timeout=30.0, check=check)
                await interaction.followup.send("Shutting down the bot and the Raspberry Pi...")
                log_.info(f"System: Full shutdown command executed by: {interaction.user.id}")
                
                # Cleanup music before shutdown
                try:
                    from internal.command_modules.music.player import cleanup_all_guilds
                    await cleanup_all_guilds(bot)
                except Exception as e:
                    log_.error(f"Error during music cleanup: {e}")
                
                await bot.close()
                os.system("sudo shutdown now")
            except asyncio.TimeoutError:
                await interaction.followup.send("❌ Shutdown canceled due to no confirmation.")
                log_.info(f"System: Full shutdown canceled. User: {interaction.user.id}")
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {e}")
            log_.error(f"System: Error in full_shutdown command: {e}")

    # -----------------------------------------------------------------
    # Command: /restart
    # Category: System Commands
    # Type: Full Command
    # Description: Restart the bot
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="restart", description="Restart the bot")
    async def restart(interaction: discord.Interaction):
        
        # Check blacklist first
        if await check_blacklist(interaction):
            return
        
        global last_restart_time

        if is_authorized_global(interaction.user):
            current_time = datetime.now()

            if last_restart_time and current_time - last_restart_time < timedelta(seconds=60):
                remaining_time = 60 - int((current_time - last_restart_time).total_seconds())
                await interaction.response.send_message(
                    f"⚠️ The `!restart` command is on cooldown. Please wait {remaining_time} seconds before trying again.", ephemeral=True
                )
                log_.info(f"System: Restart command on cooldown for {remaining_time} seconds by: {interaction.user.id}")
            else:
                last_restart_time = current_time
                await interaction.response.send_message("Restarting the bot...")
                log_.info(f"System: Restart command executed by: {interaction.user.id}")
                
                # Cleanup music before restart
                try:
                    from internal.command_modules.music.player import cleanup_all_guilds
                    await cleanup_all_guilds(bot)
                except Exception as e:
                    log_.error(f"Error during music cleanup: {e}")
                
                os.execv(sys.executable, ['python'] + sys.argv)
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            log_.info(f"Permission denied for restart command. User: {interaction.user.id}")

    # -----------------------------------------------------------------
    # Command: /log
    # Category: System Commands
    # Type: Full Command
    # Description: Get the latest log file
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="log", description="Get the latest log file")
    async def log(interaction: discord.Interaction):
        # Ensure log_directory is a string
        directory = log_directory if isinstance(log_directory, str) else "logs"
    
        # Check blacklist first
        if await check_blacklist(interaction):
            return
        
        if interaction.guild and utils.is_server_blacklisted(interaction.guild.id):
            await interaction.response.send_message("❌ This server is blacklisted.", ephemeral=True)
            log_.warning(f"Permission denied for log command in blacklisted server. Guild: {interaction.guild.id}")
            return
    
        if is_authorized_global(interaction.user):

            # Make sure it's a text channel
            if not isinstance(interaction.channel, discord.TextChannel):
                await interaction.response.send_message("❌ This command can only be used in a text channel.", ephemeral=True)
                return
        
            # Check if directory exists
            if not os.path.exists(directory):
                await interaction.response.send_message(f"⚠️ Log directory does not exist: {directory}")
                log_.warning(f"System: Log directory not found: {directory}")
                return

            # Only match new log format: bot.log-TIMESTAMP.txt
            try:
                log_files = [
                    os.path.join(directory, f)
                    for f in os.listdir(directory)
                    if f.startswith('bot.log-') and f.endswith('.txt')
                ]
            except PermissionError:
                await interaction.response.send_message(f"❌ Permission denied accessing log directory: {directory}")
                log_.error(f"System: Permission denied accessing log directory: {directory}")
                return

            # Sort newest → oldest
            log_files = sorted(log_files, key=os.path.getmtime, reverse=True)

            if log_files:
                latest_log_file = log_files[0]
                await interaction.response.send_message(file=discord.File(latest_log_file))
                log_.info(f"System: Latest log file sent to {interaction.channel.mention} for {interaction.user.id}")
            else:
                await interaction.response.send_message("⚠️ No log files found.")
                log_.info(f"System: No log files found. User: {interaction.user.id}")

        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            log_.info(f"Permission denied for log command. User: {interaction.user.id}")
    
    # -----------------------------------------------------------------
    # Command: /debugmode
    # Category: System Commands
    # Type: Full Command
    # Description: Enable or disable debug mode
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="debugmode", description="Enable or disable debug mode")
    async def debugmode(interaction: discord.Interaction, action: str):
        global config
        
        # Check blacklist first
        if await check_blacklist(interaction):
            return
        
        # Authorization check
        if is_authorized_global(interaction.user):
            if action.lower() == 'on':
                utils.set_config_value("DebugModeActivated", True)
                config = utils.load_config()
                await interaction.response.send_message("✅ Debug mode has been enabled. Please restart the bot for changes to take effect.")
                log_.info(f"System: Debug mode enabled by {interaction.user.id}")
            elif action.lower() == 'off':
                utils.set_config_value("DebugModeActivated", False)
                config = utils.load_config()
                await interaction.response.send_message("✅ Debug mode has been disabled. Please restart the bot for changes to take effect.")
                log_.info(f"System: Debug mode disabled by {interaction.user.id}")
            else:
                await interaction.response.send_message("ℹ️ Usage: `/debugmode on` or `/debugmode off`")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            log_.info(f"Permission denied for debugmode command. User: {interaction.user.id}")

    # -----------------------------------------------------------------
    # Command: /status
    # Category: System Commands
    # Type: Full Command
    # Description: Set the bot activity/status (type + text)
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="status", description="Set the bot activity/status (type + text)")
    @app_commands.describe(
        status_type="Type of activity: playing, listening, watching, competing",
        text="The status text to display"
    )
    async def status(interaction: discord.Interaction, status_type: str, text: str):
        global config
        
        # Check blacklist first
        if await check_blacklist(interaction):
            return
        
        # Authorization check
        if not is_authorized_global(interaction.user):
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            log_.info(f"Permission denied for status command. User: {interaction.user.id}")
            return

        # Normalize and map to discord.ActivityType
        t = status_type.strip().lower()
        mapping = {
            "playing": discord.ActivityType.playing,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "competing": discord.ActivityType.competing
        }
        
        # Validate type
        if t not in mapping:
            await interaction.response.send_message(
                "ℹ️ Invalid status type. Use one of: `playing`, `listening`, `watching`, `competing`",
                ephemeral=True
            )
            return
        
        # Validate text length (Discord limit is ~128 characters for activity names)
        text_stripped = text.strip()
        if not text_stripped:
            await interaction.response.send_message(
                "⚠️ Status text cannot be empty.",
                ephemeral=True
            )
            return
        
        if len(text_stripped) > 128:
            await interaction.response.send_message(
                f"⚠️ Status text is too long ({len(text_stripped)}/128 characters). Please use a shorter text.",
                ephemeral=True
            )
            return
        
        # Set the bot presence
        try:
            await bot.change_presence(activity=discord.Activity(type=mapping[t], name=text_stripped))
            
            # Save to config using utils.set_config_value for global setting
            utils.set_config_value("BotStatus", {"type": t, "text": text_stripped})
            config = utils.load_config()
            
            await interaction.response.send_message(f"✅ Bot status set to: {t} {text_stripped}", ephemeral=True)
            log_.info(f"System: Status set by {interaction.user.id} -> {t}: {text_stripped}")
        except Exception as e:
            await interaction.response.send_message("❌ Failed to set status.", ephemeral=True)
            log_.error(f"System: Failed to set status: {e}")

    # -----------------------------------------------------------------
    # Command: /logging_channel
    # Category: System Commands
    # Type: Full Command
    # Description: Manage channels in enabled/disabled logging lists
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="logging_channel", description="Manage logging channels (enabled/disabled lists)")
    @app_commands.describe(
        action="add or remove",
        channel="Channel to manage",
        list_type="enabled or disabled"
    )
    async def logging_channel(interaction: discord.Interaction, action: str, channel: discord.TextChannel, list_type: str):
        # Must be used in a guild
        if interaction.guild is None:
            await interaction.response.send_message("❌ **This command can only be used in a server.**", ephemeral=True)
            return
        
        # Check blacklist first
        if await check_blacklist(interaction):
            return
        
        # Authorization check
        if not is_authorized_server(interaction.user, guild_id=interaction.guild.id):
            await interaction.response.send_message("❌ **Permission denied.**", ephemeral=True)
            return

        # Validate list_type parameter
        if list_type.lower() not in ["enabled", "disabled"]:
            await interaction.response.send_message("❌ **List type must be 'enabled' or 'disabled'.**", ephemeral=True)
            return

        # Load server config
        server_config = utils.load_server_config(interaction.guild.id)
        
        # Initialize logging_config if not exists
        if "logging_config" not in server_config:
            server_config["logging_config"] = {
                "log_all_by_default": True,
                "enabled_channels": [],
                "disabled_channels": []
            }
        
        logging_config = server_config["logging_config"]
        channel_id = str(channel.id)
        list_type = list_type.lower()

        # Get the appropriate list
        if list_type == "enabled":
            target_list = logging_config.get("enabled_channels", []) or []
            list_name = "✅ Enabled"
        else:  # disabled
            target_list = logging_config.get("disabled_channels", []) or []
            list_name = "🚫 Disabled"

        # --- ADD action ---
        if action.lower() == "add":
            if channel_id in target_list:
                await interaction.response.send_message(
                    f"ℹ️ **Channel {channel.mention} is already in the {list_name} list.**",
                    ephemeral=True
                )
            else:
                target_list.append(channel_id)
                
                # Update the appropriate list in config
                if list_type == "enabled":
                    logging_config["enabled_channels"] = target_list
                else:
                    logging_config["disabled_channels"] = target_list
                
                server_config["logging_config"] = logging_config
                utils.save_server_config(interaction.guild.id, server_config)
                
                await interaction.response.send_message(
                    f"✅ **Channel {channel.mention} added to {list_name} list.**",
                    ephemeral=True
                )
                log_.debug(f"System: Channel {channel.name} ({channel_id}) added to {list_name} list by {interaction.user.id}")

        # --- REMOVE action ---
        elif action.lower() == "remove":
            if channel_id not in target_list:
                await interaction.response.send_message(
                    f"ℹ️ **Channel {channel.mention} is not in the {list_name} list.**",
                    ephemeral=True
                )
            else:
                target_list.remove(channel_id)
                
                # Update the appropriate list in config
                if list_type == "enabled":
                    logging_config["enabled_channels"] = target_list
                else:
                    logging_config["disabled_channels"] = target_list
                
                server_config["logging_config"] = logging_config
                utils.save_server_config(interaction.guild.id, server_config)
                
                await interaction.response.send_message(
                    f"✅ **Channel {channel.mention} removed from {list_name} list.**",
                    ephemeral=True
                )
                log_.debug(f"System: Channel {channel.name} ({channel_id}) removed from {list_name} list by {interaction.user.id}")

        # --- LIST action ---
        elif action.lower() == "list":
            enabled = logging_config.get("enabled_channels", []) or []
            disabled = logging_config.get("disabled_channels", []) or []
            
            # Build mention lists with proper error handling for deleted channels
            enabled_mentions = []
            for cid in enabled:
                try:
                    ch = interaction.guild.get_channel(int(cid))
                    if ch is not None:
                        enabled_mentions.append(f"<#{cid}>")
                    else:
                        # Channel was deleted, mark it
                        enabled_mentions.append(f"<#{cid}> (deleted)")
                except (ValueError, TypeError):
                    log_.warning(f"Invalid channel ID in enabled list: {cid}")
            
            disabled_mentions = []
            for cid in disabled:
                try:
                    ch = interaction.guild.get_channel(int(cid))
                    if ch is not None:
                        disabled_mentions.append(f"<#{cid}>")
                    else:
                        # Channel was deleted, mark it
                        disabled_mentions.append(f"<#{cid}> (deleted)")
                except (ValueError, TypeError):
                    log_.warning(f"Invalid channel ID in disabled list: {cid}")
            
            enabled_text = ", ".join(enabled_mentions) if enabled_mentions else "None"
            disabled_text = ", ".join(disabled_mentions) if disabled_mentions else "None"
            
            embed = discord.Embed(
                title="📊 **Logging Configuration**",
                color=discord.Color.from_rgb(88, 173, 218),
                description=f"Logging channels for **{interaction.guild.name}**"
            )
            
            embed.add_field(
                name="✅ Enabled Channels",
                value=enabled_text,
                inline=False
            )
            
            embed.add_field(
                name="🚫 Disabled Channels",
                value=disabled_text,
                inline=False
            )
            
            embed.add_field(
                name="📝 **Usage:**",
                value="• `/logging_channel add #channel enabled` - Add to enabled list\n"
                      "• `/logging_channel add #channel disabled` - Add to disabled list\n"
                      "• `/logging_channel remove #channel enabled` - Remove from enabled list\n"
                      "• `/logging_channel remove #channel disabled` - Remove from disabled list\n"
                      "• `/logging_channel list` - Show this overview",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            log_.info(f"System: Logging configuration listed by {interaction.user.id}")

        else:
            await interaction.response.send_message(
                "❌ **Action must be 'add', 'remove', or 'list'.**",
                ephemeral=True
            )
    
    # -----------------------------------------------------------------
    # Command: /whitelist (server-scoped)
    # Category: System Commands
    # Type: Full Command
    # Description: Manage server-specific whitelist
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="whitelist", description="Manage server-specific whitelist")
    @app_commands.describe(
        action="add, remove, or list",
        user="User to add/remove (optional for list)"
    )
    async def whitelist(interaction: discord.Interaction, action: str, user: Optional[discord.Member] = None):
        if interaction.guild is None:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        # Check blacklist first
        if await check_blacklist(interaction):
            return
        
        # Authorization check
        if not is_authorized_server(interaction.user, guild_id=interaction.guild.id):
            await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
            return

        server_config = utils.load_server_config(interaction.guild.id)
        whitelist_list = server_config.get("whitelist", [])

        if action.lower() == "add":
            if user is None:
                await interaction.response.send_message("ℹ️ Please specify a user.", ephemeral=True)
                return
            if str(user.id) not in whitelist_list:
                whitelist_list.append(str(user.id))
                server_config["whitelist"] = whitelist_list
                utils.save_server_config(interaction.guild.id, server_config)
                await interaction.response.send_message(f"✅ {user.mention} added to whitelist.", ephemeral=True)
            else:
                await interaction.response.send_message(f"ℹ️ {user.mention} is already whitelisted.", ephemeral=True)

        elif action.lower() == "remove":
            if user is None:
                await interaction.response.send_message("ℹ️ Please specify a user.", ephemeral=True)
                return
            if str(user.id) in whitelist_list:
                whitelist_list.remove(str(user.id))
                server_config["whitelist"] = whitelist_list
                utils.save_server_config(interaction.guild.id, server_config)
                await interaction.response.send_message(f"✅ {user.mention} removed from whitelist.", ephemeral=True)
            else:
                await interaction.response.send_message(f"ℹ️ {user.mention} is not whitelisted.", ephemeral=True)

        elif action.lower() == "list":
            embed = discord.Embed(title="📋 Server Whitelist", color=discord.Color.blue())
            whitelist_mentions = []
            
            for uid in whitelist_list:
                try:
                    # Ensure uid is string format for consistency
                    uid_str = str(uid)
                    fetched_user = await interaction.client.fetch_user(int(uid_str))
                    whitelist_mentions.append(f"{fetched_user.mention} ({fetched_user.name})")
                except (ValueError, TypeError):
                    # Invalid ID format
                    log_.warning(f"Invalid user ID in whitelist: {uid}")
                    whitelist_mentions.append(f"`{uid}` (invalid ID)")
                except discord.NotFound:
                    # User no longer exists
                    whitelist_mentions.append(f"`{uid}` (user deleted)")
                except discord.HTTPException as e:
                    log_.error(f"Error fetching user {uid}: {e}")
                    whitelist_mentions.append(f"`{uid}` (fetch error)")
            
            whitelist_text = " | ".join(whitelist_mentions) if whitelist_mentions else "None"
            embed.add_field(name="Whitelisted Users", value=whitelist_text, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("ℹ️ Usage: `/whitelist add|remove|list @user`", ephemeral=True)

    # -----------------------------------------------------------------
    # Command: /whitelist_add
    # Category: System Commands
    # Type: Full Command
    # Description: Add a user to the whitelist (server-specfifc)
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="whitelist_add", description="Add a user to the whitelist")
    async def whitelist_add(interaction: discord.Interaction, user: discord.Member):
        if interaction.guild is None:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        # Check blacklist first
        if await check_blacklist(interaction):
            return
        
        # Authorization check
        if not is_authorized_server(interaction.user, guild_id=interaction.guild.id):
            await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
            return

        try:
            user_id = str(user.id)
            server_config = utils.load_server_config(interaction.guild.id)
            whitelist_list = server_config.get("whitelist", [])

            if user_id in whitelist_list:
                await interaction.response.send_message(f"ℹ️ {user.mention} is already in the whitelist.", ephemeral=True)
                log_.info(f"System: {user.mention} is already in the whitelist.")
                return

            whitelist_list.append(user_id)
            server_config["whitelist"] = whitelist_list
            utils.save_server_config(interaction.guild.id, server_config)

            await interaction.response.send_message(f"✅ {user.mention} has been added to the whitelist.", ephemeral=True)
            log_.info(f"System: {user.mention} has been added to the whitelist by {interaction.user.id}.")
        except Exception as e:
            await interaction.response.send_message("❌ An error occurred while adding the user to the whitelist.", ephemeral=True)
            log_.error(f"Error adding user to whitelist: {e}")

    # -----------------------------------------------------------------
    # Command: /whitelist_remove
    # Category: System Commands
    # Type: Full Command
    # Description: Remove a user from the whitelist (server-specfifc)
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="whitelist_remove", description="Remove a user from the whitelist")
    async def whitelist_remove(interaction: discord.Interaction, user: discord.Member):
        if interaction.guild is None:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        # Check blacklist first
        if await check_blacklist(interaction):
            return
        
        # Authorization check
        if not is_authorized_server(interaction.user, guild_id=interaction.guild.id):
            await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
            return

        try:
            user_id = str(user.id)
            server_config = utils.load_server_config(interaction.guild.id)
            whitelist_list = server_config.get("whitelist", [])

            if user_id not in whitelist_list:
                await interaction.response.send_message(f"ℹ️ {user.mention} is not in the whitelist.", ephemeral=True)
                log_.info(f"System: {user.mention} is not in the whitelist.")
                return

            whitelist_list.remove(user_id)
            server_config["whitelist"] = whitelist_list
            utils.save_server_config(interaction.guild.id, server_config)

            await interaction.response.send_message(f"✅ {user.mention} has been removed from the whitelist.", ephemeral=True)
            log_.info(f"System: {user.mention} has been removed from the whitelist by {interaction.user.id}.")
        except Exception as e:
            await interaction.response.send_message("❌ An error occurred while removing the user from the whitelist.", ephemeral=True)
            log_.error(f"Error removing user from whitelist: {e}")

    # -----------------------------------------------------------------
    # Command: /logging (works per-guild; falls back to global)
    # Category: System Commands
    # Type: Full Command
    # Description: Enable or disable logging
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="logging", description="Enable or disable logging")
    async def logging(interaction: discord.Interaction, action: str):
        # Check blacklist FIRST
        if await check_blacklist(interaction):
            return
        
        global config
        # If used inside a guild, operate on server config
        if interaction.guild is not None:
            # Authorization check
            if not is_authorized_server(interaction.user, guild_id=interaction.guild.id):
                await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
                return
            server_config = utils.load_server_config(interaction.guild.id)
            if action.lower() == 'on':
                server_config["LoggingActivated"] = True
                utils.save_server_config(interaction.guild.id, server_config)
                await interaction.response.send_message("✅ Command logging has been enabled for this server. (Operational logging like errors cannot be disabled)", ephemeral=True)
                log_.info(f"System: Logging enabled for server {interaction.guild.name} by {interaction.user.id}")
            elif action.lower() == 'off':
                server_config["LoggingActivated"] = False
                utils.save_server_config(interaction.guild.id, server_config)
                await interaction.response.send_message("✅ Command logging has been disabled for this server. (Operational logging like errors remains active)", ephemeral=True)
                log_.info(f"System: Logging disabled for server {interaction.guild.name} by {interaction.user.id}")
            else:
                await interaction.response.send_message("ℹ️ Usage: `/logging on` or `/logging off`", ephemeral=True)
        else:
            # fallback to global config (DM / no guild)
            if not is_authorized_global(interaction.user):
                await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
                return
            if action.lower() == 'on':
                utils.set_config_value("LoggingActivated", True)
                config = utils.load_config()
                await interaction.response.send_message("✅ Global command logging has been enabled. (Operational logging like errors cannot be disabled)", ephemeral=True)
                log_.info(f"System: Global logging enabled by {interaction.user.id}")
            elif action.lower() == 'off':
                utils.set_config_value("LoggingActivated", False)
                config = utils.load_config()
                await interaction.response.send_message("✅ Global command logging has been disabled. (Operational logging like errors remains active)", ephemeral=True)
                log_.info(f"System: Global logging disabled by {interaction.user.id}")
            else:
                await interaction.response.send_message("ℹ️ Usage: `/logging on` or `/logging off`", ephemeral=True)

    # -----------------------------------------------------------------
    # Command: /privacy
    # Category: System Commands
    # Type: Full Command
    # Description: Display privacy and data protection information
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="privacy", description="Privacy & data protection information (DSGVO/GDPR)")
    async def privacy(interaction: discord.Interaction):
        # Check blacklist FIRST
        if await check_blacklist(interaction):
            return
        
        embed = discord.Embed(
            title="🛡️ Privacy & Data Protection",
            description="This bot complies with DSGVO/GDPR and German data protection laws.",
            color=0x0099ff
        )
        
        embed.add_field(
            name="📊 What We Log",
            value="**Controllable Command Logging:**\n"
                  "• User ID, Guild ID, Channel ID\n"
                  "• Command names (not parameters)\n"
                  "→ Can be disabled with `/logging off`\n\n"
                  "**Mandatory Operational Logging:**\n"
                  "• Errors, warnings, system events\n"
                  "→ Cannot be disabled (required for security)",
            inline=False
        )
        
        embed.add_field(
            name="❌ What We DON'T Log",
            value="• Direct Messages (DMs)\n"
                  "• Message content\n"
                  "• Usernames\n"
                  "• Personal information",
            inline=False
        )
        
        embed.add_field(
            name="⏰ Data Retention",
            value="Logs automatically deleted after **14 days**",
            inline=False
        )
        
        embed.add_field(
            name="🔐 Your Rights",
            value="• Access your data (Art. 15)\n"
                  "• Correct your data (Art. 16)\n"
                  "• Delete your data (Art. 17)\n"
                  "• Object to processing (Art. 21)\n\nContact: `dennisplischke755@gmail.com`",
            inline=False
        )
        
        embed.add_field(
            name="📚 More Information",
            value="[Privacy Policy](https://rd-code-forge.net/mclp/privacy.html) | "
                  "[Terms of Service](https://rd-code-forge.net/mclp/tos.html) |\n "
                  "[Dsgvo](https://dsgvo-gesetz.de/) | "
                  "[Gdpr](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)",
            inline=False
        )
        
        embed.set_footer(text="Location: Germany 🇩🇪 | Updated: 2026-01-07")
        
        try:
            await interaction.response.send_message(embed=embed, ephemeral=False)
            log_.debug(f"Privacy information displayed to user {interaction.user.id} in guild {interaction.guild.id if interaction.guild else 'DM'}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ Missing permission to send privacy information.", ephemeral=True)
            log_.error("Missing permission to send privacy embed.")
        except discord.HTTPException as e:
            await interaction.response.send_message("⚠️ Failed to send privacy information.", ephemeral=True)
            log_.error(f"Failed to send privacy embed: {e}")

    # -----------------------------------------------------------------
    # Command: /blacklist
    # Category: System Commands
    # Type: Full Command
    # Description: Manage global blacklists (Owner only)
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="blacklist", description="Manage global blacklists - users & servers (Owner only)")
    @app_commands.describe(
        action="add, remove, or list",
        target_type="user or server",
        target_id="User ID or Server ID (optional for list)"
    )
    async def blacklist(interaction: discord.Interaction, action: str, target_type: str, target_id: str = ""):
        # Check blacklist FIRST
        if await check_blacklist(interaction):
            return
        
        global config
    
        # Owner-only
        if not is_authorized_global(interaction.user):
            await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
            return
    
        action = action.lower()
        target_type = target_type.lower()
    
        if target_type not in ["user", "server"]:
            await interaction.response.send_message("❌ Type must be 'user' or 'server'", ephemeral=True)
            return
    
        # Handle different actions
        if action == "add":
            if not target_id:
                await interaction.response.send_message("❌ You must provide a target ID to add.", ephemeral=True)
                return
            
            if target_type == "user":
                success = utils.add_user_to_blacklist(int(target_id))
                if success:
                    await interaction.response.send_message(f"✅ User `{target_id}` added to blacklist.", ephemeral=True)
                    log_.warning(f"System: User {target_id} blacklisted by {interaction.user.id}")
                else:
                    await interaction.response.send_message(f"ℹ️ User `{target_id}` is already blacklisted.", ephemeral=True)
            
            else:  # server
                success = utils.add_server_to_blacklist(int(target_id))
                if success:
                    await interaction.response.send_message(f"✅ Server `{target_id}` added to blacklist.", ephemeral=True)
                    log_.warning(f"System: Server {target_id} blacklisted by {interaction.user.id}")
                else:
                    await interaction.response.send_message(f"ℹ️ Server `{target_id}` is already blacklisted.", ephemeral=True)
    
        elif action == "remove":
            if not target_id:
                await interaction.response.send_message("❌ You must provide a target ID to remove.", ephemeral=True)
                return
            
            if target_type == "user":
                success = utils.remove_user_from_blacklist(int(target_id))
                if success:
                    await interaction.response.send_message(f"✅ User `{target_id}` removed from blacklist.", ephemeral=True)
                    log_.warning(f"System: User {target_id} un-blacklisted by {interaction.user.id}")
                else:
                    await interaction.response.send_message(f"ℹ️ User `{target_id}` is not in blacklist.", ephemeral=True)
            
            else:  # server
                success = utils.remove_server_from_blacklist(int(target_id))
                if success:
                    await interaction.response.send_message(f"✅ Server `{target_id}` removed from blacklist.", ephemeral=True)
                    log_.warning(f"System: Server {target_id} un-blacklisted by {interaction.user.id}")
                else:
                    await interaction.response.send_message(f"ℹ️ Server `{target_id}` is not in blacklist.", ephemeral=True)
    
        elif action == "list":
            if target_type == "user":
                user_blacklist = utils.get_user_blacklist()
                embed = discord.Embed(title="🚫 Blacklisted Users", color=discord.Color.red())
                
                if user_blacklist:
                    # Split into chunks of 50 for embed field limits
                    blacklist_text = "\n".join([f"`{uid}`" for uid in user_blacklist])
                    if len(blacklist_text) > 1024:
                        # If too long, just show count
                        embed.add_field(name=f"Total Blacklisted Users ({len(user_blacklist)})", 
                                      value="Too many to display. Use database tools for full list.", 
                                      inline=False)
                    else:
                        embed.add_field(name=f"Total Blacklisted Users ({len(user_blacklist)})", 
                                      value=blacklist_text, 
                                      inline=False)
                else:
                    embed.add_field(name="Blacklisted Users", value="None", inline=False)
            
            else:  # server
                server_blacklist = utils.get_server_blacklist()
                embed = discord.Embed(title="🚫 Blacklisted Servers", color=discord.Color.red())
                
                if server_blacklist:
                    blacklist_text = "\n".join([f"`{sid}`" for sid in server_blacklist])
                    if len(blacklist_text) > 1024:
                        embed.add_field(name=f"Total Blacklisted Servers ({len(server_blacklist)})", 
                                      value="Too many to display. Use database tools for full list.", 
                                      inline=False)
                    else:
                        embed.add_field(name=f"Total Blacklisted Servers ({len(server_blacklist)})", 
                                      value=blacklist_text, 
                                      inline=False)
                else:
                    embed.add_field(name="Blacklisted Servers", value="None", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
        else:
            await interaction.response.send_message(
                "ℹ️ Usage: `/blacklist add|remove|list user|server [id]`\n"
                "Examples:\n"
                "• `/blacklist add user 12345`\n"
                "• `/blacklist remove server 67890`\n"
                "• `/blacklist list user`",
                ephemeral=True
            )

    # -----------------------------------------------------------------
    # Command: /emergency-lockdown
    # Category: Emergency Commands
    # Type: Full Command
    # Description: Restrict bot interaction to only owner DMs
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="emergency-lockdown", description="🚨 Restrict bot to owner DMs only")
    @utils.emergency_lockdown_check()
    async def emergency_lockdown(interaction: discord.Interaction):
        # Activate emergency lockdown mode
        from internal import rate_limiter
        
        # Authorization check BEFORE allowing any changes
        if not is_authorized_global(interaction.user):
            await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
            return
        
        # Check if already in lockdown (only the activating owner can toggle)
        if rate_limiter.emergency_lockdown_mode:
            await interaction.response.send_message(
                "⚠️ Emergency lockdown is already **ACTIVE**!\n"
                "Use `/emergency-reset` to deactivate first.",
                ephemeral=True
            )
            return
        
        # Activate lockdown mode
        rate_limiter.emergency_lockdown_mode = True
        rate_limiter.emergency_lockdown_owner_id = interaction.user.id
        rate_limiter.emergency_lockdown_time = datetime.now()
        
        # Change bot status to show lockdown
        try:
            activity = discord.Activity(
                type=discord.ActivityType.playing,
                name="🚨 Emergency Lockdown Active"
            )
            await bot.change_presence(activity=activity, status=discord.Status.dnd)
        except Exception as e:
            log_.warning(f"Could not change bot status: {e}")
        
        await interaction.response.send_message(
            "🚨 **EMERGENCY LOCKDOWN ACTIVATED**\n"
            "├─ Bot now responds ONLY to authorized users (whitelist)\n"
            "├─ All other interactions blocked\n"
            "├─ Bot status changed to show lockdown\n"
            "└─ Use `/emergency-reset` to deactivate",
            ephemeral=True
        )
        log_.critical(f"EMERGENCY LOCKDOWN activated by {interaction.user.id}")

    # -----------------------------------------------------------------
    # Command: /emergency-reset
    # Category: Emergency Commands
    # Type: Full Command
    # Description: Deactivate emergency lockdown and/or global cooldown
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="emergency-reset", description="🔓 Deactivate emergency lockdown/cooldown")
    @utils.emergency_lockdown_check()
    async def emergency_reset(interaction: discord.Interaction):
        # Deactivate emergency lockdown and global cooldown
        from internal import rate_limiter
        
        # Emergency reset requires global authorization (uses whitelist from config.json)
        # During lockdown: ANY authorized user can reset (Dennis or Co-Developer)
        if not is_authorized_global(interaction.user):
            await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
            return
        
        lockdown_was_active = rate_limiter.emergency_lockdown_mode
        cooldown_was_active = rate_limiter.global_cooldown.is_active
        
        # Deactivate both lockdown and global cooldown
        rate_limiter.emergency_lockdown_mode = False
        rate_limiter.global_cooldown.deactivate()
        
        # Reset bot status to normal
        try:
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name="over MCLP"
            )
            await bot.change_presence(activity=activity, status=discord.Status.online)
        except Exception as e:
            log_.warning(f"Could not reset bot status: {e}")
        
        status_msg = ""
        if lockdown_was_active:
            status_msg += "✅ Emergency lockdown **DEACTIVATED**\n"
        if cooldown_was_active:
            status_msg += "✅ Global cooldown **DEACTIVATED**\n"
        if not lockdown_was_active and not cooldown_was_active:
            status_msg = "ℹ️ No emergency measures were active"
        
        await interaction.response.send_message(status_msg, ephemeral=True)
        log_.warning(f"Emergency reset by {interaction.user.id}")

    # -----------------------------------------------------------------
    # Command: /emergency-cooldown
    # Category: Emergency Commands
    # Type: Full Command
    # Description: Activate global cooldown to prevent spam/attacks
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="emergency-cooldown", description="🚨 Activate global command cooldown")
    @utils.emergency_lockdown_check()
    async def emergency_cooldown(interaction: discord.Interaction, duration: int = 60):
        # Activate global cooldown to limit command usage
        from internal import rate_limiter
        
        if not is_authorized_global(interaction.user):
            await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
            return
        
        # Validate duration
        if not 1 <= duration <= 300:
            await interaction.response.send_message(
                "❌ Cooldown must be between 1-300 seconds",
                ephemeral=True
            )
            return
        
        rate_limiter.global_cooldown.activate(
            cooldown_seconds=duration,
            reason=f"Owner ({interaction.user.id}) activated emergency cooldown"
        )
        
        # Change bot status to show cooldown
        try:
            activity = discord.Activity(
                type=discord.ActivityType.playing,
                name=f"⏸️ Global Cooldown: {duration}s"
            )
            await bot.change_presence(activity=activity, status=discord.Status.idle)
        except Exception as e:
            log_.warning(f"Could not change bot status: {e}")
        
        await interaction.response.send_message(
            f"🚨 **GLOBAL COOLDOWN ACTIVATED**\n"
            f"├─ Duration: {duration}s per command\n"
            f"├─ All users affected\n"
            f"├─ Bot status changed to show cooldown\n"
            f"└─ Use `/emergency-reset` to deactivate",
            ephemeral=True
        )
        log_.critical(f"Global cooldown activated ({duration}s) by {interaction.user.id}")

    # -----------------------------------------------------------------
    # Command: /emergency-status
    # Category: Emergency Commands
    # Type: Full Command
    # Description: Check emergency lockdown/cooldown status
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="emergency-status", description="Check emergency system status")
    @utils.emergency_lockdown_check()
    async def emergency_status(interaction: discord.Interaction):
        # Check emergency system status
        from internal import rate_limiter
        
        if not is_authorized_global(interaction.user):
            await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
            return
        
        lockdown_status = (
            f"🔴 **ON** (Owner: <@{rate_limiter.emergency_lockdown_owner_id}>)\n"
            f"├─ Active since: {rate_limiter.emergency_lockdown_time.strftime('%H:%M:%S') if rate_limiter.emergency_lockdown_time else 'Unknown'}"
            if rate_limiter.emergency_lockdown_mode
            else "🟢 **OFF**"
        )
        
        cooldown_status = rate_limiter.global_cooldown.get_status()
        
        embed = discord.Embed(
            title="🚨 Emergency System Status",
            color=discord.Color.red() if rate_limiter.emergency_lockdown_mode else discord.Color.green()
        )
        embed.add_field(name="Emergency Lockdown", value=lockdown_status, inline=False)
        embed.add_field(name="Global Cooldown", value=cooldown_status, inline=False)
        embed.set_footer(text="Use /emergency-reset to deactivate all emergency measures")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
