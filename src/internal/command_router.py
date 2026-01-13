import logging
import inspect
from typing import Any, Awaitable, Callable, Dict, List, Tuple, Union
from internal import utils
from internal import rate_limiter
from internal.command_modules.calculator import handle_calc_command
from internal.command_modules.minigames import handle_minigames_commands
from internal.command_modules.utility_commands import handle_utility_commands
from internal.command_modules.public_commands import handle_public_commands
from internal.command_modules.moderation_commands import handle_moderation_commands
from internal.command_modules.sciencecific_commands import handle_sciencecific_commands
from internal.command_modules.music.music_commands import handle_music_commands

# Copyright (c) 2026 Dennis Plischke.
# All rights reserved.

# ================================================================
# Module: Command_router.py
# Description: Appends the right command handler based on the command
# Error handling for command routing and component tests included
# =========================================================================

# ----------------------------------------------------------------
# Type definitions
# ----------------------------------------------------------------

config = utils.load_config()
DebugModeActivated = config.get("DebugModeActivated", False)

# Type alias for component test function
ComponentTestFunc = Union[
    Callable[[], Dict[str, str]],
    Callable[[], Awaitable[Dict[str, str]]]
]

# Command groups definition
command_groups = {
    'utility': ['!ping', '!uptime', '!weather', '!city', '!time', '!poll', '!reminder'],
    'minigames': ['!rps', '!hangman', '!quiz', '!guess', '!roll'],
    'public': ['!help', '!info', '!rules', '!userinfo', '!serverinfo', '!catfact'],
    'moderation': ['!kick', '!ban', '!unban', '!timeout', '!untimeout', '!reactionrole'],
    'sciencecific': ['!apod', '!marsphoto', '!asteroids', '!sun', '!exoplanet', '!spacefact'],
    'music': ['!music-channel', '!join', '!leave', '!play', '!pause', '!resume', '!skip', '!last', '!stop', '!repeat', '!queue', '!nowplaying'],
}

# Command handlers mapping
command_handlers = {
    'utility': handle_utility_commands,
    'minigames': handle_minigames_commands,
    'public': handle_public_commands,
    'moderation': handle_moderation_commands,
    'sciencecific': handle_sciencecific_commands,
    'music': handle_music_commands,
}

# Commands that cannot be executed in a DM
no_dm_commands = [
    '!kick', '!ban', '!unban', '!timeout', '!untimeout', '!reactionrole',
    '!userinfo', '!rules', '!serverinfo', '!reactionrole', '!poll',
    '!whitelist add', '!whitelist remove', '!music-channel','!join', 
    '!leave', '!play', '!pause', '!resume', '!skip', '!last', '!stop',
    '!queue', '!nowplaying'
]

# ----------------------------------------------------------------
# Component test function for command handlers
# ----------------------------------------------------------------

# Component test function for all command handlers
async def component_test() -> List[Tuple[str, Dict[str, str]]]:
    results: List[Tuple[str, Dict[str, str]]] = []
    
    results.append(("command_router", {"status": "🟩", "msg": "Command router loaded."}))
    
    # Rate Limiter Component Test (add FIRST)
    try:
        import internal.rate_limiter as rate_lim
        if hasattr(rate_lim, "component_test"):
            result = rate_lim.component_test()
            results.append(("rate_limiter", result))
        else:
            results.append(("rate_limiter", {"status": "🟧", "msg": "No component test found."}))
    except Exception as e:
        results.append(("rate_limiter", {"status": "🟥", "msg": f"Error during loading: {e}"}))

    # Component test for calculator module
    try:
        import internal.command_modules.calculator as calc
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
# Main command handler for routing commands
# ----------------------------------------------------------------

async def handle_command(client, message) -> Union[str, None]:
    user_message = message.content.strip()
    
    # Check if the command can be executed in DM enviroment
    if message.guild is None:
        if any(user_message.startswith(cmd) for cmd in no_dm_commands):
            await message.channel.send("⚠️ This command cannot be executed in a DM enviroment.")
            logging.warning(f"Command '{user_message}' blocked in DM enviroment.")
            return None
    
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
    
    return None
