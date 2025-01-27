import aiohttp # Asynchronous HTTP client library
from datetime import datetime, timedelta # For handling timeouts
import asyncio # For asynchronous programming
import discord # discord.py library
import random # For generating random numbers
import json # For working with JSON data
import os # For interacting with the operating system
import sys # For system-specific parameters and functions
from . import utils # Import the utils module
from internal.commands.minigames import handle_minigames
from internal.commands.moderation_commands import handle_moderation_commands
from internal.commands.public_commands import handle_public_commands
from internal.commands.system_commands import handle_system_commands
from internal.commands.utility_commands import handle_utility_commands

last_restart_time = None

command_handlers = {
    'system': handle_system_commands,
    'moderation': handle_moderation_commands,
    'public': handle_public_commands,
    'utility': handle_utility_commands,
    'minigames': handle_minigames,
}

command_groups = {
    'system': ['!shutdown', '!restart', '!full-shutdown'],
    'moderation': ['!kick', '!ban', '!unban', '!timeout', '!untimeout'],
    'public': ['!help', '!info', '!rules', '!userinfo', '!serverinfo', '!catfact'],
    'utility': ['!ping', '!weather', '!download'],
    'minigames': ['!roll', '!rps'],
}


async def handle_command(client, message):
    user_message = message.content.lower()

    for group, commands in command_groups.items():
        if any(user_message.startswith(cmd) for cmd in commands):
            await command_handlers[group](client, message, user_message)
            return  # Stop checking after finding the matching command

    # Return None for unhandled commands
    return None
