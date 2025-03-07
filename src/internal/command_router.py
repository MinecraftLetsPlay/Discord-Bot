import logging
from internal.commands.minigames import handle_minigames_commands
from internal.commands.moderation_commands import handle_moderation_commands
from internal.commands.public_commands import handle_public_commands
from internal.commands.utility_commands import handle_utility_commands

# Command handlers for each group
command_handlers = {
    'moderation': handle_moderation_commands,
    'public': handle_public_commands,
    'utility': handle_utility_commands,
    'minigames': handle_minigames_commands
}

# Command groups and their commands
command_groups = {
    'moderation': ['!kick', '!ban', '!unban', '!timeout', '!untimeout', '!reactionrole'],
    'public': ['!help', '!info', '!rules', '!userinfo', '!serverinfo', '!catfact'],
    'utility': ['!ping', '!uptime', '!weather', '!city', '!download', '!time'],
    'minigames': ['!rps', '!guess', '!hangman', '!quiz', '!roll']
}

# Commands that cannot be executed in a DM
no_dm_commands = [
    '!kick', '!ban', '!unban', '!timeout', '!untimeout',
    '!userinfo', '!rules', '!serverinfo', '!reactionrole',
    '!whitelist add', '!whitelist remove'
]

async def handle_command(client, message):
    user_message = message.content.lower()

    # Check if the message is in a DM
    if message.guild is None:
        # Check if the command is not allowed in a DM
        if any(user_message.startswith(cmd) for cmd in no_dm_commands):
            await message.channel.send("⚠️ This command cannot be executed in a DM.")
            logging.warning(f"Command '{user_message}' cannot be executed in a DM. User: (DM) / {message.author}")
            return

    for group, commands in command_groups.items():
        if any(user_message.startswith(cmd) for cmd in commands):
            await command_handlers[group](client, message, user_message)
            return
