import discord
import logging
import os
import sys
import nacl
import asyncio
import time
from dotenv import load_dotenv
from discord.ext import commands
from internal import utils
from internal import command_router

# ----------------------------------------------------------------
# Module: Bot.py
# Description: Main loop and handlers for messages and reactions
# ----------------------------------------------------------------

start = time.perf_counter()

def run_discord_bot():
    
    # Load environment variables from .env file
    load_dotenv()

    # Load config and get the token from the environment variable or config file
    config = utils.load_config()
    DebugModeActivated = config.get("DebugModeActivated", False)
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not TOKEN:
        logging.critical("❌ DISCORD_BOT_TOKEN is missing. Please set it in the .env file.")
        sys.exit(1)

    # Get discord intents (rights for the bot)
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True

    bot = commands.Bot(command_prefix='!', intents=intents)
    
    # Run component tests before starting the bot
    async def run_component_tests():
        print()
        print("──────────────────────────────")
        print(" Startup Component Summary")
        print("──────────────────────────────")
        results = await command_router.component_test()
        for name, result in results:
            display_name = name.capitalize()
            status = result['status']
            msg = result['msg']
            
            # Detailed output in debug mode
            if DebugModeActivated:
                print(f"Hello from {display_name}:")
                print(f"  Status: {status} {msg}")
                
            # Summary output if debug mode is not activated
            else:
                if status == "🟩":
                    print(f"{status} {display_name}")
                elif status == "🟨":
                    print(f"{status} {display_name} ({msg})")
                elif status == "🟧":
                    print(f"{status} {display_name} ({msg})")
                elif status == "🟥":
                    print(f"{status} {display_name} (Error: {msg})")
        print("──────────────────────────────")
        print()
        return results
    
    asyncio.run(run_component_tests())

    # Check for the bot to be ready
    @bot.event
    async def on_ready():
        duration = time.perf_counter() - start
        logging.info(f"Bot ready after {duration:.2f} seconds.")
        print()
        logging.info(f'✅ {bot.user} is now running!')
        print()
        logging.info("--------------------------")
        logging.info(f"Python version: {sys.version.split()[0]}")
        logging.info(f"Discord.py version: {discord.__version__}")
        logging.info(f"PyNaCl version: {nacl.__version__}")
        logging.info(f"Application ID: {bot.application_id}")
        logging.info(f"Logging activated: {config.get('LoggingActivated', True)}")
        logging.info(f"Debug mode activated: {config.get('DebugModeActivated', False)}")
        logging.info("--------------------------")
        print()
        
        # Set the bots status to "Listening to your commands"
        activity = discord.Activity(type=discord.ActivityType.listening, name="euren Befehlen")
        await bot.change_presence(activity=activity)
        # Sync the slash commands with Discord
        await bot.tree.sync()
        logging.info('Slash commands synchronized.')

    # Check for messages
    @bot.event
    async def on_message(message):
        config = utils.load_config()
        LoggingActivated = config.get("LoggingActivated", True) # Check if logging is activated in the config file
        
        if message.author == bot.user: # Ignore messages from the bot itself
            return
        
        if message.guild is None:  # This means it's a DM
            if LoggingActivated:
                logging.info(f"📩 DM from {message.author}: {message.content}")
            username = str(message.author)
            user_message = str(message.content)
            channel = str(message.channel)
            if LoggingActivated:
                logging.info(f'{username} said: "{user_message}" (DM / {message.author})')
        else: # Server enviroment
            username = str(message.author)
            user_message = str(message.content)
            channel = str(message.channel)
            if LoggingActivated:
                logging.info(f'{username} said: "{user_message}" ({message.guild.name} / {channel})')

        # Pass the client object to handle_command
        try:
            response = await command_router.handle_command(bot, message)
            if response is not None:  # Check for a valid response
                # Log the response based on channel type
                if message.guild is None:  # DM
                    if LoggingActivated:
                        logging.info(f'{bot.user} said: "{response}" (DM / {message.author})')
                else:  # Server
                    if LoggingActivated:
                        logging.info(f'{bot.user} said: "{response}" ({message.guild.name} / {channel})')
                # Send the response
                await message.channel.send(response)
        except Exception as e:
            logging.error(f"❌ Error handling message: {e}")
            
    # Reaction role handling
    async def handle_reaction_role(payload, action):
        try:
            # Load reaction role data
            reaction_role_data = utils.load_reaction_role_data()
            guild_id = str(payload.guild_id)
            if guild_id not in reaction_role_data:
                logging.debug(f"Guild ID {guild_id} not found in reaction role data.")
                return
            
            # Find the matching message and emoji
            for message_data in reaction_role_data[guild_id]:
                if message_data["messageID"] == str(payload.message_id):
                    for role_data in message_data["roles"]:
                        if str(payload.emoji) == role_data["emoji"]:
                            guild = bot.get_guild(payload.guild_id)
                            # Check for missig data
                            if not guild:
                                logging.error(f"Guild {guild_id} not found.")
                                return
                            role = guild.get_role(int(role_data["roleID"]))
                            if not role:
                                logging.error(f"Role ID {role_data['roleID']} not found in guild {guild.name}.")
                                return
                            member = guild.get_member(payload.user_id)
                            if not member:
                                logging.error(f"Member ID {payload.user_id} not found in guild {guild.name}.")
                                return
                            # Add or remove the role based on the action
                            if action == "add":
                                await member.add_roles(role)
                                logging.info(f"Added role {role.name} to {member.name}")
                            elif action == "remove":
                                await member.remove_roles(role)
                                logging.info(f"Removed role {role.name} from {member.name}")
                            return
            logging.warning(f"No matching reaction role found for message {payload.message_id} and emoji {payload.emoji}.")
        except Exception as e:
            logging.error(f"Error in handle_reaction_role ({action}): {e}")
            
    # Bot event reaction add
    @bot.event
    async def on_raw_reaction_add(payload):
        if bot.user is not None and payload.user_id == bot.user.id:
            return
        await handle_reaction_role(payload, "add")
        
    # Bot event reaction remove
    @bot.event
    async def on_raw_reaction_remove(payload):
        if bot.user is not None and payload.user_id == bot.user.id:
            return
        await handle_reaction_role(payload, "remove")

    # Load system commands
    from internal.commands.system_commands import setup_system_commands
    setup_system_commands(bot)
    
    # Load /download command
    from internal.commands.utility_commands import setup_utility_commands
    setup_utility_commands(bot)
    
    bot.run(TOKEN)
