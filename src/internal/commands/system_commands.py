import discord
import os
import sys
import asyncio
import logging as log_
import json
from discord import app_commands
from datetime import datetime, timedelta
from internal import utils
from dotenv import load_dotenv
from internal.commands.logging_setup import CustomTimedRotatingFileHandler

# ----------------------------------------------------------------
# Helper Functions and Initial Setup
# ----------------------------------------------------------------

# Load environment variables from .env file
load_dotenv()

# Load config
config = utils.load_config()
log_directory = config.get("log_file_location")
if not isinstance(log_directory, str) or not log_directory:
    log_directory = "logs"

config_file_path = 'src/internal/data/config.json'  # Ensure the correct path to the config file

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
LoggingActivated = config.get("LoggingActivated")

# ----------------------------------------------------------------
# Logging engine (Handels logging and file naming / file deletion)
# ----------------------------------------------------------------

# Setup logging with TimedRotatingFileHandler
log_file = os.path.join(log_directory, 'bot.log')
handler = CustomTimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=10, encoding="utf-8")
handler.suffix = "%d.%m.%Y_%H.%M.%S"

log_.basicConfig(level=log_.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    handler,
    log_.StreamHandler(sys.stdout)
])

# Function to rotate logs
def rotate_logs():
    # Make sure log_directory is a string
    directory = log_directory if isinstance(log_directory, str) else "logs"
    log_files = sorted(
        [f for f in os.listdir(directory) if f.startswith('bot.log') and f.endswith('.txt')],
        key=lambda x: os.path.getmtime(os.path.join(directory, x))
    )
    current_log_file = os.path.join(directory, 'bot.log')
    if os.path.exists(current_log_file):
        log_files.append('bot.log')

    # Check if the number of files exceeds the limit
    if len(log_files) > 10:
        files_to_delete = log_files[:len(log_files) - 10]
        for file in files_to_delete:
            file_path = os.path.join(directory, file)
            try:
                os.remove(file_path)
                log_.info(f"Deleted old log file: {file_path}")
            except Exception as e:
                log_.error(f"Failed to delete log file {file_path}: {e}")

rotate_logs()

# ----------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------

# Store the bot start time
bot_start_time = datetime.now()

last_restart_time = None

def is_authorized(user):
    try:
        config = utils.load_config()
        whitelist = config.get("whitelist", [])
        return str(user.id) in whitelist  # Check the user ID
    except Exception as e:
        log_.error(f"❌ Error checking authorization: {e}")
        return False

def add_to_whitelist(user):
    try:
        whitelist = config.get("whitelist", [])
        if str(user) not in whitelist:
            whitelist.append(str(user))
            config["whitelist"] = whitelist
            with open(config_file_path, 'w') as f:
                json.dump(config, f, indent=4)
            log_.info(f"Added {user} to whitelist.")
            return True
        else:
            log_.info(f"{user} is already in the whitelist.")
            return False
    except Exception as e:
        log_.error(f"❌ Error adding to whitelist: {e}")
        return False

def remove_from_whitelist(user):
    try:
        whitelist = config.get("whitelist", [])
        if str(user) in whitelist:
            whitelist.remove(str(user))
            config["whitelist"] = whitelist
            with open(config_file_path, 'w') as f:
                json.dump(config, f, indent=4)
            log_.info(f"Removed {user} from whitelist.")
            return True
        else:
            log_.info(f"{user} is not in the whitelist.")
            return False
    except Exception as e:
        log_.error(f"❌ Error removing from whitelist: {e}")
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
        if is_authorized(interaction.user):
            await interaction.response.send_message("Shutting down the bot...")
            log_.info(f"System: Shutdown command executed by: {interaction.user}")
            await bot.close()
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            log_.info(f"Permission denied for shutdown command. User: {interaction.user}")

    # -----------------------------------------------------------------
    # Command: /full_shutdown
    # Category: System Commands
    # Type: Full Command
    # Description: Shut down the bot and the Raspberry Pi
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="full_shutdown", description="Shut down the bot and the Raspberry Pi")
    async def full_shutdown(interaction: discord.Interaction):
        if is_authorized(interaction.user):
            confirm_message = await interaction.response.send_message(
                f"{interaction.user.mention}, are you sure you want to **shut down the Raspberry Pi**? React with ✅ to confirm."
            )

            def check(reaction, user):
                return user == interaction.user and str(reaction.emoji) == '✅'

            try:
                await bot.wait_for("reaction_add", timeout=30.0, check=check)
                await interaction.response.send_message("Shutting down the bot and the Raspberry Pi...")
                log_.info(f"System: Full shutdown command executed by: {interaction.user}")
                await bot.close()
                os.system("sudo shutdown now")
            except asyncio.TimeoutError:
                await interaction.response.send_message(f"❌ {interaction.user.mention}, shutdown canceled due to no confirmation.")
                log_.info(f"System: Full shutdown canceled due to no confirmation. User: {interaction.user}")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            log_.info(f"Permission denied for full shutdown command. User: {interaction.user}")

    # -----------------------------------------------------------------
    # Command: /restart
    # Category: System Commands
    # Type: Full Command
    # Description: Restart the bot
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="restart", description="Restart the bot")
    async def restart(interaction: discord.Interaction):
        global last_restart_time

        if is_authorized(interaction.user):
            current_time = datetime.now()

            if last_restart_time and current_time - last_restart_time < timedelta(seconds=60):
                remaining_time = 60 - (current_time - last_restart_time).seconds
                await interaction.response.send_message(
                    f"⚠️ The `!restart` command is on cooldown. Please wait {remaining_time} seconds before trying again."
                )
                log_.info(f"System: Restart command on cooldown for {remaining_time} seconds by: {interaction.user}")
            else:
                last_restart_time = current_time
                await interaction.response.send_message("Restarting the bot...")
                log_.info(f"System: Restart command executed by: {interaction.user}")
                os.execv(sys.executable, ['python'] + sys.argv)
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            log_.info(f"Permission denied for restart command. User: {interaction.user}")

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
        channel = interaction.channel
        if is_authorized(interaction.user):
            log_files = [
                os.path.join(directory, f)
                for f in os.listdir(directory)
                if f.startswith('bot.log') and f.endswith('.txt')
            ]
            log_files = sorted(log_files, key=os.path.getmtime, reverse=True)
            if log_files:
                latest_log_file = log_files[0]
                await interaction.response.send_message(file=discord.File(latest_log_file))
                log_.info(f"System: Latest log file sent to {channel} for {interaction.user}")
            else:
                await interaction.response.send_message("⚠️ No log files found.")
                log_.info(f"System: No log files found. User: {interaction.user}")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            log_.info(f"Permission denied for log command. User: {interaction.user}")

    # -----------------------------------------------------------------
    # Command: /whitelist_add
    # Category: System Commands
    # Type: Full Command
    # Description: Add a user to the whitelist
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="whitelist_add", description="Add a user to the whitelist")
    async def whitelist_add(interaction: discord.Interaction, user: discord.Member):
        if is_authorized(interaction.user):
            try:
                user_id = str(user.id)  # Extract the user ID
                whitelist = config.get("whitelist", [])

                if user_id in whitelist:
                    await interaction.response.send_message(f"ℹ️ {user.mention} is already in the whitelist.")
                    log_.info(f"System: {user.mention} is already in the whitelist.")
                    return

                # Add the user ID to the whitelist
                whitelist.append(user_id)
                config["whitelist"] = whitelist
                with open(config_file_path, 'w') as f:
                    json.dump(config, f, indent=4)

                await interaction.response.send_message(f"✅ {user.mention} has been added to the whitelist.")
                log_.info(f"System: {user.mention} (ID: {user_id}) has been added to the whitelist by {interaction.user}.")
            except Exception as e:
                await interaction.response.send_message("❌ An error occurred while adding the user to the whitelist.")
                log_.error(f"❌ Error adding user to whitelist: {e}")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            log_.info(f"Permission denied for whitelist add command. User: {interaction.user}")

    # -----------------------------------------------------------------
    # Command: /whitelist_remove
    # Category: System Commands
    # Type: Full Command
    # Description: Remove a user from the whitelist
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="whitelist_remove", description="Remove a user from the whitelist")
    async def whitelist_remove(interaction: discord.Interaction, user: discord.Member):
        if is_authorized(interaction.user):
            try:
                user_id = str(user.id)  # Extract the user ID
                whitelist = config.get("whitelist", [])

                if user_id not in whitelist:
                    await interaction.response.send_message(f"ℹ️ {user.mention} is not in the whitelist.")
                    log_.info(f"System: {user.mention} is not in the whitelist.")
                    return

                # Remove the user ID from the whitelist
                whitelist.remove(user_id)
                config["whitelist"] = whitelist
                with open(config_file_path, 'w') as f:
                    json.dump(config, f, indent=4)

                await interaction.response.send_message(f"✅ {user.mention} has been removed from the whitelist.")
                log_.info(f"System: {user.mention} (ID: {user_id}) has been removed from the whitelist by {interaction.user}.")
            except Exception as e:
                await interaction.response.send_message("❌ An error occurred while removing the user from the whitelist.")
                log_.error(f"❌ Error removing user from whitelist: {e}")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            log_.info(f"Permission denied for whitelist remove command. User: {interaction.user}")

    # -----------------------------------------------------------------
    # Command: /logging
    # Category: System Commands
    # Type: Full Command
    # Description: Enable or disable logging
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="logging", description="Enable or disable logging")
    async def logging(interaction: discord.Interaction, action: str):
        global LoggingActivated
        if is_authorized(interaction.user):
            if action.lower() == 'on':
                LoggingActivated = True
                config["LoggingActivated"] = True
                with open(config_file_path, 'w') as f:
                    json.dump(config, f, indent=4)
                await interaction.response.send_message("✅ Logging has been enabled.")
                log_.info(f"System: Logging enabled by {interaction.user}")
            elif action.lower() == 'off':
                LoggingActivated = False
                config["LoggingActivated"] = False
                with open(config_file_path, 'w') as f:
                    json.dump(config, f, indent=4)
                await interaction.response.send_message("✅ Logging has been disabled.")
                log_.info(f"System: Logging disabled by {interaction.user}")
            else:
                await interaction.response.send_message("ℹ️ Usage: `/logging on` or `/logging off`")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            log_.info(f"Permission denied for logging command. User: {interaction.user}")
    
    # -----------------------------------------------------------------
    # Command: /debugmode
    # Category: System Commands
    # Type: Full Command
    # Description: Enable or disable debug mode
    # -----------------------------------------------------------------
    
    @bot.tree.command(name="debugmode", description="Enable or disable debug mode")
    async def debugmode(interaction: discord.Interaction, action: str):
        global config
        if is_authorized(interaction.user):
            if action.lower() == 'on':
                config["DebugModeActivated"] = True
                with open(config_file_path, 'w') as f:
                    json.dump(config, f, indent=4)
                await interaction.response.send_message("✅ Debug mode has been enabled. Please restart the bot for changes to take effect.")
                log_.info(f"System: Debug mode enabled by {interaction.user}")
            elif action.lower() == 'off':
                config["DebugModeActivated"] = False
                with open(config_file_path, 'w') as f:
                    json.dump(config, f, indent=4)
                await interaction.response.send_message("✅ Debug mode has been disabled. Please restart the bot for changes to take effect.")
                log_.info(f"System: Debug mode disabled by {interaction.user}")
            else:
                await interaction.response.send_message("ℹ️ Usage: `/debugmode on` or `/debugmode off`")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            log_.info(f"Permission denied for debugmode command. User: {interaction.user}")

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
        # Permission check
        if not is_authorized(interaction.user):
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{interaction.user.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            log_.info(f"Permission denied for status command. User: {interaction.user}")
            return

        # Normalize and map to discord.ActivityType
        t = status_type.strip().lower()
        mapping = {
            "playing": discord.ActivityType.playing,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "competing": discord.ActivityType.competing
        }

        if t not in mapping:
            await interaction.response.send_message(
                "ℹ️ Invalid status type. Use one of: `playing`, `listening`, `watching`, `competing`",
                ephemeral=True
            )
            return

        try:
            await bot.change_presence(activity=discord.Activity(type=mapping[t], name=text))
            await interaction.response.send_message(f"✅ Bot status set to: {t} {text}", ephemeral=True)
            log_.info(f"System: Status set by {interaction.user} -> {t}: {text}")
        except Exception as e:
            await interaction.response.send_message("❌ Failed to set status.", ephemeral=True)
            log_.error(f"System: Failed to set status: {e}")


