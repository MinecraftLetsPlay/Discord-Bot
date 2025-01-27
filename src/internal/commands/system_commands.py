import discord
import os
import sys
import asyncio
from datetime import datetime, timedelta
from internal import utils

    #
    #
    # System commands
    #
    #
    
last_restart_time = None
    
def is_authorized(user):
    # Checks if the user is on the whitelist
    try:
        config = utils.load_config()  # Load config using utils.py
        whitelist = config.get("whitelist", []) # Get the whitelist from the config
        return str(user) in whitelist
    except Exception as e:
        print(f"Error checking authorization: {e}")
        return False
    
# Main def for handling system commands
async def handle_system_commands(client, message, user_message):
    # !shutdown command
    if user_message == '!shutdown':
        if is_authorized(message.author):
            await message.channel.send("Shutting down the bot...")
            print(f"[System] Shutdown command executed by: {message.author}")
            await client.close()
        else:
            embed = discord.Embed(
                title="Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)

    # !full-shutdown command
    if user_message == '!full-shutdown':
        if is_authorized(message.author):
            # Add a confirmation step to prevent accidental shutdown
            confirm_message = await message.channel.send(
                f"{message.author.mention}, are you sure you want to **shut down the Raspberry Pi**? React with ✅ to confirm."
            )

            def check(reaction, user):
                return user == message.author and str(reaction.emoji) == '✅'

            try:
                await client.wait_for("reaction_add", timeout=30.0, check=check)
                await message.channel.send("Shutting down the bot and the Raspberry Pi...")
                print(f"[System] Full shutdown command executed by: {message.author}")
                await client.close()
                os.system("sudo shutdown now")
            except asyncio.TimeoutError:
                await message.channel.send(f"{message.author.mention}, shutdown canceled due to no confirmation.")
        else:
            embed = discord.Embed(
                title="Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)

    # !restart command
    if user_message == '!restart':
        global last_restart_time

        if is_authorized(message.author):
            current_time = datetime.now()

            # Check if the last restart was within the cooldown period
            if last_restart_time and current_time - last_restart_time < timedelta(seconds=60):
                remaining_time = 60 - (current_time - last_restart_time).seconds
                await message.channel.send(
                    f"The `!restart` command is on cooldown. Please wait {remaining_time} seconds before trying again."
                )
            else:
                last_restart_time = current_time  # Update the last restart time
                await message.channel.send("Restarting the bot...")
                print(f"[System] Restart command executed by: {message.author}")
                os.execv(sys.executable, ['python'] + sys.argv)
        else:
            embed = discord.Embed(
                title="Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)