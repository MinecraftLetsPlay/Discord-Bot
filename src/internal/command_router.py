from internal.commands.minigames import Minigames, handle_minigames
from internal.commands.moderation_commands import handle_moderation_commands
from internal.commands.public_commands import handle_public_commands
from internal.commands.system_commands import handle_system_commands
from internal.commands.utility_commands import handle_utility_commands

# Grouped commands into files... Those are the command handlers
command_handlers = {
    'system': handle_system_commands,
    'moderation': handle_moderation_commands,
    'public': handle_public_commands,
    'utility': handle_utility_commands,
    'minigames': handle_minigames,
}

# To specify the command groups and their commands
command_groups = {
    'system': ['!shutdown', '!restart', '!full-shutdown'],
    'moderation': ['!kick', '!ban', '!unban', '!timeout', '!untimeout'],
    'public': ['!help', '!info', '!rules', '!userinfo', '!serverinfo', '!catfact'],
    'utility': ['!ping', '!weather', '!city', '!download'],
    'minigames': ['!roll', '!rps'],
}

async def handle_minigames(client, message, user_message):
    minigames = Minigames()

    if user_message.startswith('!rps'):
        await minigames.play("rps", client, message)

    elif user_message.startswith('!guess'):
        await minigames.play("guess", client, message)

    elif user_message.startswith('!hangman'):
        await minigames.play("hangman", client, message)

# Function to handle the commands
async def handle_command(client, message):
    user_message = message.content.lower()

    for group, commands in command_groups.items():
        if any(user_message.startswith(cmd) for cmd in commands):
            await command_handlers[group](client, message, user_message)
            return  # Stop checking after finding the matching command

    # Return None for unhandled commands
    return None
