import discord # Discord API
import logging # Logging support
import os
import sys
import nacl  # PyNaCl for voice support
from dotenv import load_dotenv
from discord.ext import commands
from internal import utils
from internal import command_router

#
#
# Main Discord Bot Functionality - Core Functions
#
#

def run_discord_bot():
    # Load environment variables from .env file
    load_dotenv()

    # Load config and get the token from the environment variable or config file
    config = utils.load_config()
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

    # Check for the bot to be ready
    @bot.event
    async def on_ready():
        logging.info(f'✅ {bot.user} is now running!')
        print()
        logging.info("--------------------------")
        logging.info(f"Python version: {sys.version.split()[0]}")
        logging.info(f"Discord.py version: {discord.__version__}")
        logging.info(f"PyNaCl version: {nacl.__version__}")
        logging.info(f"Application ID: {bot.application_id}")
        logging.info(f"Logging activated: {config.get('LoggingActivated', True)}")
        logging.info("--------------------------")
        print()
        # Set the bot's status to "hört euren Befehlen zu"
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
                logging.info(f'{username} said: "{user_message}" (DM / {channel})')
        else: # Server enviroment
            username = str(message.author)
            user_message = str(message.content)
            channel = str(message.channel)
            if LoggingActivated:
                logging.info(f'{username} said: "{user_message}" ({message.guild.name} / {channel})')

        # Pass the client object to handle_command
        try:
            response = await command_router.handle_command(bot, message)
            if response is not None:  # Prüfe explizit auf None
                if message.guild is None:
                    if LoggingActivated:
                        logging.info(f'{bot.user} said: "{response}" (DM / {channel})')
                else:
                    if LoggingActivated:
                        logging.info(f'{bot.user} said: "{response}" ({message.guild.name} / {channel})')
                await message.channel.send(response)
        except Exception as e:
            logging.error(f"❌ Error handling message: {e}")

    # Register event listeners for reaction roles
    @bot.event
    async def on_raw_reaction_add(payload):
        if bot.user is not None and payload.user_id == bot.user.id:
            return

        reaction_role_data = utils.load_reaction_role_data()
        guild_id = str(payload.guild_id)

        if guild_id in reaction_role_data:
            # Suche nach der richtigen Nachricht
            for message_data in reaction_role_data[guild_id]:
                if message_data["messageID"] == str(payload.message_id):
                    # Suche nach der passenden Rolle
                    for role_data in message_data["roles"]:
                        if str(payload.emoji) == role_data["emoji"]:
                            guild = bot.get_guild(payload.guild_id)
                            if guild:
                                role = guild.get_role(int(role_data["roleID"]))
                                member = guild.get_member(payload.user_id)
                                if role and member:
                                    await member.add_roles(role)
                                    logging.info(f"Added role {role.name} to {member.name}")
                                    return

    @bot.event
    async def on_raw_reaction_remove(payload):
        # Ignore reactions from the bot itself
        if bot.user is not None and payload.user_id == bot.user.id:
            return

        reaction_role_data = utils.load_reaction_role_data()
        guild_id = str(payload.guild_id)

        if guild_id in reaction_role_data:
            # Suche nach der richtigen Nachricht
            for message_data in reaction_role_data[guild_id]:
                if message_data["messageID"] == str(payload.message_id):
                    # Suche nach der passenden Rolle
                    for role_data in message_data["roles"]:
                        if str(payload.emoji) == role_data["emoji"]:
                            guild = bot.get_guild(payload.guild_id)
                            if guild:
                                role = guild.get_role(int(role_data["roleID"]))
                                member = guild.get_member(payload.user_id)
                                if role and member:
                                    await member.remove_roles(role)
                                    logging.info(f"Removed role {role.name} from {member.name}")
                                    return

    # Load system commands
    from internal.commands.system_commands import setup_system_commands
    setup_system_commands(bot)
    
    # Load /download command
    from internal.commands.utility_commands import setup_utility_commands
    setup_utility_commands(bot)

    bot.run(TOKEN)
