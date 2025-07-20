import discord
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True  # Damit der Bot Nachrichten-Inhalte empfangen kann
client = discord.Client(intents=intents)

async def send_message():
    await client.wait_until_ready()

    while True:
        action = await asyncio.to_thread(input, "Aktion wählen: [send/react/exit]: ")
        action = action.strip().lower()

        if action == "exit":
            print("Stopping console message sender.")
            await client.close()
            break
        elif action == "send":
            message_text = await asyncio.to_thread(input, "Enter message: ")
            channel_id = await asyncio.to_thread(input, "Enter channel ID (or press Enter to use default): ")
            channel_id = channel_id.strip() or "1331341040673751124"
            try:
                channel = client.get_channel(int(channel_id))
                if isinstance(channel, discord.TextChannel):
                    await channel.send(message_text)
                    print(f"✅ Sent message to {channel.name} (ID: {channel.id})")
                else:
                    print("❌ Invalid channel ID or not a text channel.")
            except ValueError:
                print("❌ Invalid input. Channel ID must be a number.")
        elif action == "react":
            channel_id = await asyncio.to_thread(input, "Enter channel ID: ")
            message_id = await asyncio.to_thread(input, "Enter message ID: ")
            emoji = await asyncio.to_thread(input, "Enter emoji to react with: ")
            await react_to_message_by_id(channel_id, message_id, emoji)
        else:
            print("❌ Unknown action.")

async def react_to_message_by_id(channel_id, message_id, emoji):
    channel = client.get_channel(int(channel_id))
    if not isinstance(channel, discord.TextChannel):
        print("❌ Channel not found or not a text channel.")
        return
    try:
        message = await channel.fetch_message(int(message_id))
        await message.add_reaction(emoji)
        print(f"✅ Added reaction {emoji} to message {message_id} in channel {channel_id}")
    except Exception as e:
        print(f"❌ Error: {e}")

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')
    
    # List all channels the bot has access to
    for guild in client.guilds:
        print(f"Guild: {guild.name} (ID: {guild.id})")
        for channel in guild.text_channels:
            print(f"  Channel: {channel.name} (ID: {channel.id})")
            
    asyncio.create_task(send_message())  # Start message loop

if TOKEN is None:
    print("❌ DISCORD_BOT_TOKEN is not set in your .env file!")
else:
    client.run(TOKEN)