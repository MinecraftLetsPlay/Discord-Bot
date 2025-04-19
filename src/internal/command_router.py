import logging
from internal.commands.calculator import handle_calc_command
from internal.commands.minigames import handle_minigames_commands
from internal.commands.utility_commands import handle_utility_commands
from internal.commands.public_commands import handle_public_commands
from internal.commands.moderation_commands import handle_moderation_commands

# Command groups definition
command_groups = {
    'utility': ['!ping', '!uptime', '!weather', '!city', '!time', '!download', '!poll', '!reminder', '!calc'],
    'minigames': ['!rps', '!hangman', '!quiz', '!guess', '!roll'],
    'public': ['!help', '!info', '!rules', '!userinfo', '!serverinfo', '!catfact'],
    'moderation': ['!kick', '!ban', '!unban', '!timeout', '!untimeout', '!reactionrole']
}

# Command handlers mapping
command_handlers = {
    'utility': handle_calc_command,  # Map calculator handler
    'minigames': handle_minigames_commands,
    'public': handle_public_commands,
    'moderation': handle_moderation_commands
}

# Commands that cannot be executed in a DM
no_dm_commands = [
    '!kick', '!ban', '!unban', '!timeout', '!untimeout', '!reactionrole',
    '!userinfo', '!rules', '!serverinfo', '!reactionrole',
    '!whitelist add', '!whitelist remove', '!poll'
]

async def handle_command(client, message):
    user_message = message.content.strip()
    
    logging.debug(f"Received command: {user_message}")  # Debug log
    
    for group, commands in command_groups.items():
        if any(user_message.startswith(cmd) for cmd in commands):
            logging.debug(f"Command matches group: {group}")  # Debug log
            try:
                await command_handlers[group](client, message, user_message)
                return
            except Exception as e:
                logging.error(f"Error in command handler '{group}': {e}", exc_info=True)
                await message.channel.send("⚠️ An error occurred while processing your command.")
                return
    
    if user_message.startswith('!'):  # Only log unknown commands that start with !
        logging.warning(f"Unknown command: {user_message}")
        await message.channel.send("❓ Unknown command. Type !help for a list of available commands.")
