import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from internal import utils
from internal import command_router
from internal.commands import logging_setup
import logging
import nacl  # PyNaCl for voice support
import wavelink  # Wavelink for music bot support
from internal.commands.moderation_commands import handle_moderation_commands
from internal.commands.utility_commands import handle_utility_commands

def run_discord_bot():
    # Load environment variables from .env file
    load_dotenv()

    # Load config and get the token from the environment variable or config file
    config = utils.load_config()
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')

    # Get discord intents (rights for the bot)
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True
    intents.voice_states = True  # Wichtig für Musik-Bot
    
    class CustomBot(commands.Bot):
        async def setup_hook(self) -> None:
            """Called when the bot is starting up"""
            try:
                # Create Lavalink node
                node = wavelink.Node(
                    uri='http://127.0.0.1:2333',
                    password='youshallnotpass'
                )
                await wavelink.NodePool.connect(
                    bot=self,
                    nodes=[node]
                )
                await self.load_extension("internal.commands.musicbot")
                logging.info("✅ Music extension loaded successfully")
                self.lavalink_available = True
            except Exception as e:
                logging.error(f"❌ Error setting up music: {e}")
                self.lavalink_available = False
                # Bot startet trotzdem weiter

    bot = CustomBot(command_prefix='!', intents=intents)

    # Check for the bot to be ready
    @bot.event
    async def on_ready():
        logging.info(f'✅ {bot.user} is now running!')
        print()
        logging.debug("--------------------------")
        logging.debug(f"Wavelink version: {wavelink.__version__}")
        logging.debug(f"Discord.py version: {discord.__version__}")
        logging.debug(f"PyNaCl version: {nacl.__version__}")
        logging.debug(f"Application ID: {bot.application_id}")
        logging.debug(f"Logging activated: {config.get('LoggingActivated', True)}")
        logging.debug("--------------------------")
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
        response = await command_router.handle_command(bot, message)
        if response:
            if message.guild is None:
                if LoggingActivated:
                    logging.info(f'{bot.user} said: "{response}" (DM / {channel})')
            else:
                if LoggingActivated:
                    logging.info(f'{bot.user} said: "{response}" ({message.guild.name} / {channel})')
            await message.channel.send(response)

    # Register event listeners for reaction roles
    @bot.event
    async def on_raw_reaction_add(payload):
        # Ignore reactions from the bot itself
        if payload.user_id == bot.user.id:
            return

        # Load the reaction role data
        reaction_role_data = utils.load_reaction_role_data()

        if str(payload.message_id) == reaction_role_data["messageID"]:
            guild = bot.get_guild(int(reaction_role_data["guildID"]))
            # Find the matching role entry
            role_entry = next((role for role in reaction_role_data["roles"] if role["roleID"] and str(payload.emoji) == role["emoji"]), None)
        
            if role_entry:
                role = guild.get_role(int(role_entry["roleID"]))
                member = guild.get_member(payload.user_id)

                if role and member:
                    await member.add_roles(role)
                    logging.info(f"Added role {role.name} to {member.name} for reacting with {payload.emoji}.")

    @bot.event
    async def on_raw_reaction_remove(payload):
        # Ignore reactions from the bot itself
        if payload.user_id == bot.user.id:
            return

        # Load the reaction role data
        reaction_role_data = utils.load_reaction_role_data()

        if str(payload.message_id) == reaction_role_data["messageID"]:
            guild = bot.get_guild(int(reaction_role_data["guildID"]))
            # Find the matching role entry
            role_entry = next((role for role in reaction_role_data["roles"] if role["roleID"] and str(payload.emoji) == role["emoji"]), None)
        
            if role_entry:
                role = guild.get_role(int(role_entry["roleID"]))
                member = guild.get_member(payload.user_id)

                if role and member:
                    await member.remove_roles(role)
                    logging.info(f"Removed role {role.name} from {member.name} for removing reaction {payload.emoji}.")

    # Load system commands
    from internal.commands.system_commands import setup_system_commands
    setup_system_commands(bot)

    bot.run(TOKEN)