import discord
import asyncio

TOKEN = "MTExMDkzMjg4MzY1MDExNzY0Mg.GKg69F.yRQ7DLKPW9e13dYrItd2tBAvOGIdKvSRUtXv8E"  # Replace with your bot token

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
    asyncio.create_task(send_message())  # Start message loop

client.run(TOKEN)