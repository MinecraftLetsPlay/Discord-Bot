import discord
import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from internal import utils
from dotenv import load_dotenv
import logging_setup  # Import the logging setup

# Load environment variables from .env file
load_dotenv()

# Load config
config = utils.load_config()
log_directory = config.get("log_file_location")

# Ensure log directory exists
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Setup logging
log_file = os.path.join(log_directory, 'log01.txt')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(log_file),
    logging.StreamHandler()
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

# Main def for handling system commands
async def handle_system_commands(client, message, user_message):
    logging.info(f"User message from {message.author}: {user_message}")

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
            logging.info(f"System: Permission denied for shutdown command by: {message.author}")

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
                logging.info(f"System: Full shutdown canceled due to no confirmation by: {message.author}")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.info(f"System: Permission denied for full shutdown command by: {message.author}")

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
                logging.info(f"System: Restart command executed by: {message.author}")
                os.execv(sys.executable, ['python'] + sys.argv)
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.info(f"System: Permission denied for restart command by: {message.author}")
            
    # !log command
    if user_message.startswith('!log'):
        if is_authorized(message.author):
            log_files = sorted([f for f in os.listdir(log_directory) if f.startswith('log') and f.endswith('.txt')])
            if log_files:
                latest_log_file = os.path.join(log_directory, log_files[-1])
                await message.channel.send(file=discord.File(latest_log_file))
                logging.info(f"System: Log file {latest_log_file} sent to {message.author}")
            else:
                await message.channel.send("⚠️ No log files found.")
                logging.info(f"System: No log files found for {message.author}")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.info(f"System: Permission denied for log command by: {message.author}")

# Example of logging bot messages
async def send_bot_message(channel, content):
    await channel.send(content)
    logging.info(f"Bot message: {content}")
