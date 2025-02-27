import discord
from internal import utils
from internal import command_router
import os
from dotenv import load_dotenv
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

    client = discord.Client(intents=intents)

    # Check for the bot to be ready
    @client.event
    async def on_ready():
        logging.info(f'✅ {client.user} is now running!')

    # Check for messages
    @client.event
    async def on_message(message):
        config = utils.load_config()
        LoggingActivated = config.get("LoggingActivated")
        
        if message.author == client.user:
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
        response = await command_router.handle_command(client, message)
        if response:
            if message.guild is None:
                if LoggingActivated:
                    logging.info(f'{client.user} said: "{response}" (DM / {channel})')
            else:
                if LoggingActivated:
                    logging.info(f'{client.user} said: "{response}" ({message.guild.name} / {channel})')
            await message.channel.send(response)

    client.run(TOKEN) # Start the Bot
