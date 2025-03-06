import discord
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def send_message():
    await client.wait_until_ready()

    while True:
        # Run input() in a separate thread to avoid blocking
        message_text = await asyncio.to_thread(input, "Enter message (or type 'exit' to stop): ")
        message_text = message_text.strip()

        if message_text.lower() == "exit":
            print("Stopping console message sender.")
            await client.close()
            break

        channel_id = await asyncio.to_thread(input, "Enter channel ID (or press Enter to use default): ")
        channel_id = channel_id.strip()

        if not channel_id:
            channel_id = "1331341040673751124"  # Replace with your default channel ID

        try:
            channel = client.get_channel(int(channel_id))
            if channel:
                await channel.send(message_text)
                print(f"✅ Sent message to {channel.name} (ID: {channel.id})")
            else:
                print("❌ Invalid channel ID. Make sure the bot has access to the channel.")
        except ValueError:
            print("❌ Invalid input. Channel ID must be a number.")

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')
    
    # List all channels the bot has access to
    for guild in client.guilds:
        print(f"Guild: {guild.name} (ID: {guild.id})")
        for channel in guild.text_channels:
            print(f"  Channel: {channel.name} (ID: {channel.id})")
            
    asyncio.create_task(send_message())  # Start message loop

client.run(TOKEN)