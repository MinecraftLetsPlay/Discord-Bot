from internal.commands.minigames import Minigames
from internal.commands.moderation_commands import handle_moderation_commands
from internal.commands.public_commands import handle_public_commands
from internal.commands.system_commands import handle_system_commands
from internal.commands.utility_commands import handle_utility_commands

# Function to handle the minigames commands
async def handle_minigames(client, message, user_message):
    minigames = Minigames()

    # Check which minigame is being requested
    game_map = {
        "!rps": "rps",
        "!guess": "guess",
        "!hangman": "hangman",
        "!quiz": "quiz"
    }
    
    # Loop through the game_map to find the corresponding minigame
    for cmd, game_name in game_map.items():
        if user_message.startswith(cmd):
            if game_name == "quiz":
                # Extract the category after the command
                parts = user_message.split(" ", 1)
                category = parts[1] if len(parts) > 1 else None
                
                await minigames.play(game_name, client, message, category=category)
            else:
                await minigames.play(game_name, client, message)
            return
        
# Grouped commands into files... Those are the command handlers
command_handlers = {
    'system': handle_system_commands,
    'moderation': handle_moderation_commands,
    'public': handle_public_commands,
    'utility': handle_utility_commands,
    'minigames': handle_minigames
}

# To specify the command groups and their commands
command_groups = {
    'system': ['!shutdown', '!restart', '!full-shutdown'],
    'moderation': ['!kick', '!ban', '!unban', '!timeout', '!untimeout'],
    'public': ['!help', '!info', '!rules', '!userinfo', '!serverinfo', '!catfact'],
    'utility': ['!ping', '!weather', '!city', '!download'],
    'minigames': ['!rps', '!guess', '!hangman', "!quiz"]
}

# Function to handle the commands
async def handle_command(client, message):
    user_message = message.content.lower()

    # Handle each command group by checking if the message starts with any of the group's commands
    for group, commands in command_groups.items():
        if any(user_message.startswith(cmd) for cmd in commands):
            # Handle the appropriate group of commands
            if group in ['public', 'moderation', 'system', 'utility']:
                await command_handlers[group](client, message, user_message)
                return  # Stop after finding the matching group

            # If it's minigames, handle separately
            elif group == 'minigames':
                await handle_minigames(client, message, user_message)
                return

    # Return None for unhandled commands
    return None
