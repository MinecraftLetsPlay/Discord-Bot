import logging
from internal.commands.minigames import handle_minigames_commands
from internal.commands.moderation_commands import handle_moderation_commands
from internal.commands.public_commands import handle_public_commands
from internal.commands.system_commands import handle_system_commands
from internal.commands.utility_commands import handle_utility_commands

# Command handlers for each group
command_handlers = {
    'system': handle_system_commands,
    'moderation': handle_moderation_commands,
    'public': handle_public_commands,
    'utility': handle_utility_commands,
    'minigames': handle_minigames_commands
}

# Command groups and their commands
command_groups = {
    'system': ['!shutdown', '!restart', '!full-shutdown'],
    'moderation': ['!kick', '!ban', '!unban', '!timeout', '!untimeout'],
    'public': ['!help', '!info', '!rules', '!userinfo', '!serverinfo', '!catfact'],
    'utility': ['!ping', '!weather', '!city', '!download'],
    'minigames': ['!rps', '!guess', '!hangman', '!quiz']
}

async def handle_command(client, message):
    user_message = message.content.lower()

    for group, commands in command_groups.items():
        if any(user_message.startswith(cmd) for cmd in commands):
            await command_handlers[group](client, message, user_message)
            return
