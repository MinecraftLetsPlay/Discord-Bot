import random
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
    
    # !help command
    if user_message == '!help':
        return 'Possible Commands: [System]: !shutdown, !restart [Public]: !Roll, !test.'

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
            return "You don't have the permission to execute this command."

    # !restart command
    if user_message == '!restart':
        if is_authorized(message.author):
            await message.channel.send("Restarting...")
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            return "You don't have the permission to execute this command."

    # Return None for unhandled commands
    return None