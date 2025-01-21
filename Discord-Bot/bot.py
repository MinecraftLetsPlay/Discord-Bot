import discord
import responses
import os
import sys

async def send_message(message, user_message, is_private):
    try:
        response = responses.get_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)

    except Exception as e:
        print(e)

def run_discord_bot():
    TOKEN = 'MTExMDkzMjg4MzY1MDExNzY0Mg.GKg69F.yRQ7DLKPW9e13dYrItd2tBAvOGIdKvSRUtXv8E'
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

        # Check for commands
        if user_message.lower() == '!shutdown':
            await message.channel.send("Shutting down...")
            await client.close()
            
        elif user_message.lower() == '!restart':
            await message.channel.send("Restarting...")
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            # Process responses from responses.py
            response = responses.get_response(user_message)
            if response:
                print(f'{client.user} said: "{response}" ({channel})')
                await message.channel.send(response)

    client.run(TOKEN)