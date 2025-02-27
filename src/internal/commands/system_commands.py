import discord
import os
import sys
import asyncio
import logging
import json
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from internal import utils
from dotenv import load_dotenv
from internal.commands import logging_setup

# Load environment variables from .env file
load_dotenv()

# Load config
config = utils.load_config()
log_directory = config.get("log_file_location")
config_file_path = 'src/internal/data/config.jsonc'  # Ensure the correct path to the config file

# Ensure log directory exists
if not os.path.exists(log_directory):
    try:
        os.makedirs(log_directory)
    except PermissionError as e:
        print(f"Permission denied: {e}")
        sys.exit(1)

# Global variable to control logging
LoggingActivated = config.get("LoggingActivated")

# Setup logging with TimedRotatingFileHandler
log_file = os.path.join(log_directory, 'bot.log')
handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=10, encoding="utf-8")
handler.suffix = "%Y-%m-%d"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    handler,
    logging.StreamHandler(sys.stdout)
])

# Function to rotate logs
def rotate_logs():
    log_files = sorted([f for f in os.listdir(log_directory) if f.startswith('log') and f.endswith('.txt')])
    if len(log_files) >= 10:
        os.remove(os.path.join(log_directory, log_files[0]))
        for i, log_file in enumerate(log_files[1:], start=1):
            os.rename(os.path.join(log_directory, log_file), os.path.join(log_directory, f'log{i:02d}.txt'))

rotate_logs()

# Store the bot start time
bot_start_time = datetime.now()

last_restart_time = None

def is_authorized(user):
    try:
        whitelist = config.get("whitelist", [])
        return str(user) in whitelist
    except Exception as e:
        logging.error(f"Error checking authorization: {e}")
        return False

def add_to_whitelist(user):
    try:
        whitelist = config.get("whitelist", [])
        if str(user) not in whitelist:
            whitelist.append(str(user))
            config["whitelist"] = whitelist
            with open(config_file_path, 'w') as f:
                json.dump(config, f, indent=4)
            logging.info(f"Added {user} to whitelist.")
            return True
        else:
            logging.info(f"{user} is already in the whitelist.")
            return False
    except Exception as e:
        logging.error(f"Error adding to whitelist: {e}")
        return False

def remove_from_whitelist(user):
    try:
        whitelist = config.get("whitelist", [])
        if str(user) in whitelist:
            whitelist.remove(str(user))
            config["whitelist"] = whitelist
            with open(config_file_path, 'w') as f:
                json.dump(config, f, indent=4)
            logging.info(f"Removed {user} from whitelist.")
            return True
        else:
            logging.info(f"{user} is not in the whitelist.")
            return False
    except Exception as e:
        logging.error(f"Error removing from whitelist: {e}")
        return False

# Main def for handling system commands
async def handle_system_commands(client, message, user_message):
    global LoggingActivated

    # !shutdown command
    if user_message == '!shutdown':
        if is_authorized(message.author):
            await message.channel.send("Shutting down the bot...")
            logging.info(f"System: Shutdown command executed by: {message.author}")
            await client.close()
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.info(f"System: Permission denied for shutdown command. User: {message.author}")

    # !full-shutdown command
    if user_message == '!full-shutdown':
        if is_authorized(message.author):
            confirm_message = await message.channel.send(
                f"{message.author.mention}, are you sure you want to **shut down the Raspberry Pi**? React with ✅ to confirm."
            )

            def check(reaction, user):
                return user == message.author and str(reaction.emoji) == '✅'

            try:
                await client.wait_for("reaction_add", timeout=30.0, check=check)
                await message.channel.send("Shutting down the bot and the Raspberry Pi...")
                logging.info(f"System: Full shutdown command executed by: {message.author}")
                await client.close()
                os.system("sudo shutdown now")
            except asyncio.TimeoutError:
                await message.channel.send(f"❌ {message.author.mention}, shutdown canceled due to no confirmation.")
                logging.info(f"System: Full shutdown canceled due to no confirmation. User: {message.author}")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.info(f"System: Permission denied for full shutdown command. User: {message.author}")

    # !restart command
    if user_message == '!restart':
        global last_restart_time

        if is_authorized(message.author):
            current_time = datetime.now()

            if last_restart_time and current_time - last_restart_time < timedelta(seconds=60):
                remaining_time = 60 - (current_time - last_restart_time).seconds
                await message.channel.send(
                    f"⚠️ The `!restart` command is on cooldown. Please wait {remaining_time} seconds before trying again."
                )
                logging.info(f"System: Restart command on cooldown for {remaining_time} seconds by: {message.author}")
            else:
                last_restart_time = current_time
                await message.channel.send("Restarting the bot...")
                if LoggingActivated:
                    logging.info(f"System: Restart command executed by: {message.author}")
                os.execv(sys.executable, ['python'] + sys.argv)
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.info(f"System: Permission denied for restart command. User: {message.author}")
            
    # !log command
    if user_message == ('!log'):
        if is_authorized(message.author):
            log_files = sorted([f for f in os.listdir(log_directory) if f.startswith('log') and f.endswith('.txt')])
            if log_files:
                latest_log_file = os.path.join(log_directory, log_files[-1])
                await message.channel.send(file=discord.File(latest_log_file))
                if LoggingActivated:
                    logging.info(f"System: Log file {latest_log_file} sent to {message.author}")
            else:
                await message.channel.send("⚠️ No log files found.")
                if LoggingActivated:
                    logging.info(f"System: No log files found. User: {message.author}")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.info(f"System: Permission denied for log command. User: {message.author}")

    # !whitelist add <username> command
    if user_message.startswith('!whitelist add'):
        if is_authorized(message.author):
            try:
                user_to_add = user_message.split()[2]
                if add_to_whitelist(user_to_add):
                    await message.channel.send(f"✅ {user_to_add} has been added to the whitelist.")
                else:
                    await message.channel.send(f"ℹ️ {user_to_add} is already in the whitelist.")
            except IndexError:
                await message.channel.send("ℹ️ Please specify a user to add to the whitelist.")
                logging.warning("ℹ️ No user specified for whitelist add command.")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.info(f"System: Permission denied for whitelist add command. User: {message.author}")

    # !whitelist remove <username> command
    if user_message.startswith('!whitelist remove'):
        if is_authorized(message.author):
            try:
                user_to_remove = user_message.split()[2]
                if remove_from_whitelist(user_to_remove):
                    await message.channel.send(f"✅ {user_to_remove} has been removed from the whitelist.")
                else:
                    await message.channel.send(f"ℹ️ {user_to_remove} is not in the whitelist.")
            except IndexError:
                await message.channel.send("ℹ️ Please specify a user to remove from the whitelist.")
                if LoggingActivated:
                    logging.warning("ℹ️ No user specified for whitelist remove command.")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.info(f"System: Permission denied for whitelist remove command. User: {message.author}")

    # !logging command
    if user_message.startswith('!logging'):
        if is_authorized(message.author):
            try:
                action = user_message.split()[1].lower()
                if action == 'on':
                    LoggingActivated = True
                    config["LoggingActivated"] = True
                    with open(config_file_path, 'w') as f:
                        json.dump(config, f, indent=4)
                    await message.channel.send("✅ Logging has been enabled.")
                    logging.info(f"System: Logging enabled by {message.author}")
                elif action == 'off':
                    LoggingActivated = False
                    config["LoggingActivated"] = False
                    with open(config_file_path, 'w') as f:
                        json.dump(config, f, indent=4)
                    await message.channel.send("✅ Logging has been disabled.")
                else:
                    await message.channel.send("ℹ️ Usage: `!logging on` or `!logging off`")
            except IndexError:
                await message.channel.send("ℹ️ Usage: `!logging on` or `!logging off`")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            if LoggingActivated:
                logging.info(f"System: Permission denied for logging command. User: {message.author}")
