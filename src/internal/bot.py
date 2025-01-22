import discord
import commands
from config import config
import os
import sys

async def send_message(message, user_message, is_private):
    try:
        response = responses.get_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)

    except Exception as e:
        print(e)

def run_discord_bot():
    config = utils.load_config()
    TOKEN = os.getenv('DISCORD_BOT_TOKEN', config['token'])
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        username = str(message.author)
        user_message = str(message.content)
        channel = str(message.channel)
        
        print(f'{username} said: "{user_message}" ({channel})')

            # Process responses from responses.py
            response = commands.get_response(user_message)
            if response:
                print(f'{client.user} said: "{response}" ({channel})')
                await message.channel.send(response)

    client.run(TOKEN)
