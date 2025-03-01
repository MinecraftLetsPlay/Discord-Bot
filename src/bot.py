import discord
from discord.ext import commands
from internal import utils
from internal import command_router
import os
from dotenv import load_dotenv
from internal.commands import logging_setup
import logging

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

    bot = commands.Bot(command_prefix='!', intents=intents)

    # Check for the bot to be ready
    @bot.event
    async def on_ready():
        logging.info(f'✅ {bot.user} is now running!')
        # Set the bot's status to "listening to euren Befehlen zu"
        activity = discord.Activity(type=discord.ActivityType.listening, name="euren Befehlen")
        await bot.change_presence(activity=activity)
        # Sync the slash commands with Discord
        await bot.tree.sync()
        logging.info('Slash commands synchronized.')

    # Check for messages
    @bot.event
    async def on_message(message):
        config = utils.load_config()
        LoggingActivated = config.get("LoggingActivated", True)
        
        if message.author == bot.user:
            return
        
        if message.guild is None:  # This means it's a DM
            if LoggingActivated:
                logging.info(f"📩 DM from {message.author}: {message.content}")
            username = str(message.author)
            user_message = str(message.content)
            channel = str(message.channel)
            if LoggingActivated:
                logging.info(f'{username} said: "{user_message}" (DM / {channel})')
        else:
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

    # Load system commands
    from internal.commands.system_commands import setup_system_commands
    setup_system_commands(bot)

    bot.run(TOKEN)
