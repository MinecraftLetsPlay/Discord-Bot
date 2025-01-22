import random
import discord
import os
import sys
from internal import utils  # Assuming utils.py is in the internal directory

def is_authorized(user):
    """Checks if the user is authorized for system commands."""
    try:
        config = utils.load_config()  # Load config using utils
        whitelist = config.get("whitelist", [])
        return str(user) in whitelist
    except Exception as e:
        print(f"Error checking authorization: {e}")
        return False

async def handle_command(client, message):
    """Handles user commands."""
    user_message = message.content.lower()
    
    username = message.author
    
    # !help command
    if user_message == '!help':
        embed = discord.Embed(title="Help", description="Possible Commands", color=0x00ff00)
        embed.add_field(name="[System]", value="!shutdown, !restart", inline=False)
        embed.add_field(name="[Public]", value="!roll, !test, !info, !ping", inline=False)
        await message.channel.send(embed=embed)
    
    if user_message == '!info':
        embed = discord.Embed(title="Info", description="This is a Discord bot created for demonstration purposes.", color=0x00ff00)
        await message.channel.send(embed=embed)

    # !test command
    if user_message == '!test':
        return 'Hello! I am online and ready...'

    # !roll command
    if user_message == '!roll':
        return str(random.randint(1, 6))
    
    # !shutdown command
    if user_message == '!shutdown':
        if is_authorized(message.author):
            await message.channel.send("Shutting down...")
            await client.close()
        else:
            embed = discord.Embed(
                title="Permission denied", 
                description=f"@{username} You don't have the permission to execute this command.", 
                color=0xff0000
            )
            await message.channel.send(embed=embed)

    # !restart command
    if user_message == '!restart':
        if is_authorized(message.author):
            await message.channel.send("Restarting...")
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            embed = discord.Embed(
                title="Permission denied", 
                description=f"@{username} You don't have the permission to execute this command.", 
                color=0xff0000
            )
            await message.channel.send(embed=embed)

    # Return None for unhandled commands
    return None