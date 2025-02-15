import discord
from internal import utils
from internal import command_router
import os
from dotenv import load_dotenv

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
        print(f'✅ {client.user} is now running!')

    # Check for messages
    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        username = str(message.author)
        user_message = str(message.content)
        channel = str(message.channel)

        print(f'{username} said: "{user_message}" ({channel})')

        # Pass the client object to handle_command
        response = await command_router.handle_command(client, message)
        if response:
            print(f'{client.user} said: "{response}" ({channel})')
            await message.channel.send(response)

    client.run(TOKEN)
