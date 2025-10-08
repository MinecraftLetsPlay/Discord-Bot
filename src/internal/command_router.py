import logging
import inspect
from typing import Any, Awaitable, Callable, Dict, List, Tuple, Union
from internal.commands.calculator import handle_calc_command
from internal.commands.minigames import handle_minigames_commands
from internal.commands.utility_commands import handle_utility_commands
from internal.commands.public_commands import handle_public_commands
from internal.commands.moderation_commands import handle_moderation_commands
from internal.commands.mcserver_commands import handle_mcserver_commands
from internal.commands.sciencecific_commands import handle_sciencecific_commands

#
#
# Passes commands to the appropriate handler based on the command group
#
#

# Type alias for component test function
ComponentTestFunc = Union[
    Callable[[], Dict[str, str]],
    Callable[[], Awaitable[Dict[str, str]]]
]

# Command groups definition
command_groups = {
    'utility': ['!ping', '!uptime', '!weather', '!city', '!time', '!poll', '!reminder'],
    'minigames': ['!rps', '!hangman', '!quiz', '!guess', '!roll', '!scrabble'],
    'public': ['!help', '!info', '!rules', '!userinfo', '!serverinfo', '!catfact'],
    'moderation': ['!kick', '!ban', '!unban', '!timeout', '!untimeout', '!reactionrole'],
    'sciencecific': ['!apod', '!marsphoto', '!asteroids', '!sun', '!exoplanet', '!spacefact'],
    'mcserver': ['!MCServer']
}

# Command handlers mapping
command_handlers = {
    'utility': handle_utility_commands,
    'minigames': handle_minigames_commands,
    'public': handle_public_commands,
    'moderation': handle_moderation_commands,
    'mcserver': handle_mcserver_commands,
    'sciencecific': handle_sciencecific_commands
}

# Commands that cannot be executed in a DM
no_dm_commands = [
    '!kick', '!ban', '!unban', '!timeout', '!untimeout', '!reactionrole',
    '!userinfo', '!rules', '!serverinfo', '!reactionrole', '!scrabble',
    '!whitelist add', '!whitelist remove', '!poll', '!MCServer'
]

# Component test function for all command handlers
async def component_test() -> List[Tuple[str, Dict[str, str]]]:
    """
    Runs a test for each command handler to check if they are properly set up.
    Returns a list of tuples with the command group name and the test result.
    """
    results: List[Tuple[str, Dict[str, str]]] = []
    
    print("Hello from command_router:")
    print("  Status: 🟩 Command router loaded.")
    
    # Component test for calculator module
    try:
        import internal.commands.calculator as calc
        if hasattr(calc, "component_test"):
            result = calc.component_test()
            results.append(("calculator", result))
        else:
            results.append(("calculator", {"status": "🟧", "msg": "No component test found."}))
    except Exception as e:
        results.append(("calculator", {"status": "🟥", "msg": f"Error during loading.: {e}"}))
        
    # Component tests for other modules
    for name, handler in command_handlers.items():
        try:
            mod = handler.__module__
            module = __import__(mod, fromlist=["component_test"])
            if hasattr(module, "component_test"):
                test_func: ComponentTestFunc = getattr(module, "component_test") # type: ignore
                if inspect.iscoroutinefunction(test_func):
                    result: Dict[str, str] = await test_func() # type: ignore
                else:
                    result: Dict[str, str] = test_func() # type: ignore
                results.append((name, result))
            else:
                results.append((name, {"status": "🟧", "msg": "No component test found."}))
        except Exception as e:
            print(f"  Status: 🟥 Error during loading.: {e}")
            results.append((name, {"status": "🟥", "msg": f"Error during loading.: {e}"}))
    return results

# ----------------------------------------------------------------
# Main command handler
# ----------------------------------------------------------------

async def handle_command(client, message):
    user_message = message.content.strip()
    
    # Check if the command can be executed in DM enviroment
    if message.guild is None:
        if any(user_message.startswith(cmd) for cmd in no_dm_commands):
            await message.channel.send("⚠️ This command cannot be executed in a DM enviroment.")
            logging.warning(f"Command '{user_message}' blocked in DM enviroment.")
            return
    
    logging.debug(f"Received command: {user_message}")  # Debug log

    # Handle !calc separately
    if user_message.startswith('!calc'):
        try:
            return await handle_calc_command(client, message, user_message)
        except Exception as e:
            logging.error(f"Error in !calc command handler: {e}", exc_info=True)
            return "⚠️ An error occurred while processing your command."
    
    # Handle other commands
    for group, commands in command_groups.items():
        if any(user_message.startswith(cmd) for cmd in commands):
            handler = command_handlers[group]
            logging.debug(f"Routing command '{user_message}' to handler '{handler.__name__}'")
            try:
                return await command_handlers[group](client, message, user_message)
            except Exception as e:
                logging.error(f"Error in command handler '{group}': {e}", exc_info=True)
                return "⚠️ An error occurred while processing your command."
    
    if user_message.startswith('!'):  # Only log unknown commands that start with !
        logging.warning(f"Unknown command: {user_message}")
        await message.channel.send("❓ Unknown command. Type !help for a list of available commands.")
