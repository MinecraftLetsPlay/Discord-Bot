import os
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from internal.commands.system_commands import is_authorized  # Import the is_authorized function

# Load environment variables
load_dotenv()
API_KEY = os.getenv("NITRADO_API_KEY")
SERVICE_ID = os.getenv("NITRADO_SERVICE_ID")

# Base URL for Nitrado API
BASE_URL = f"https://api.nitrado.net/services/{SERVICE_ID}"

async def send_nitrado_request(endpoint, method="GET", data=None):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with aiohttp.ClientSession() as session:
        if method == "GET":
            async with session.get(f"{BASE_URL}{endpoint}", headers=headers) as response:
                return await response.json()
        elif method == "POST":
            async with session.post(f"{BASE_URL}{endpoint}", headers=headers, json=data) as response:
                return await response.json()

# Command handler
async def handle_mcserver_commands(client, message, user_message):
    # Check if the user is authorized
    if not is_authorized(message.author):
        embed = discord.Embed(
            title="❌ Permission denied",
            description=f"{message.author.mention} You don't have the permission to execute this command.",
            color=0xff0000
        )
        await message.channel.send(embed=embed)
        return

    if not API_KEY or not SERVICE_ID:
        await message.channel.send("❌ API key or Service ID is missing. Please configure the .env file.")
        return

    parts = user_message.split()
    if len(parts) < 2:
        await message.channel.send("❌ Usage: !MCServer <action>")
        return

    action = parts[1].lower()

    if action == "shutdown":
        # Shutdown the server
        response = await send_nitrado_request("/gameservers/shutdown", method="POST")
        if response.get("status") == "success":
            await message.channel.send("✅ Server is shutting down.")
        else:
            await message.channel.send(f"❌ Failed to shut down the server: {response}")

    elif action == "restart":
        # Restart the server
        response = await send_nitrado_request("/gameservers/restart", method="POST")
        if response.get("status") == "success":
            await message.channel.send("✅ Server is restarting.")
        else:
            await message.channel.send(f"❌ Failed to restart the server: {response}")

    elif action == "status":
        # Get server status
        response = await send_nitrado_request("/gameservers")
        if response.get("status") == "success":
            server_data = response["data"]["gameserver"]
            online = server_data["status"] == "online"
            players_online = server_data["players"]["current"]
            player_list = server_data["players"]["list"]

            embed = discord.Embed(
                title="🖥️ Minecraft Server Status",
                color=discord.Color.green() if online else discord.Color.red()
            )
            embed.add_field(name="Online", value=str(online), inline=True)
            embed.add_field(name="Players Online", value=str(players_online), inline=True)
            embed.add_field(name="Player List", value=", ".join(player_list) if player_list else "None", inline=False)

            await message.channel.send(embed=embed)
        else:
            await message.channel.send(f"❌ Failed to fetch server status: {response}")

    elif action == "command":
        # Send a command to the server console
        if len(parts) < 3:
            await message.channel.send("❌ Usage: !MCServer command <minecraft_command>")
            return

        minecraft_command = " ".join(parts[2:])
        response = await send_nitrado_request("/gameservers/command", method="POST", data={"command": minecraft_command})
        if response.get("status") == "success":
            await message.channel.send(f"✅ Command '{minecraft_command}' sent to the server.")
        else:
            await message.channel.send(f"❌ Failed to send command: {response}")

    elif action in ["shutdown-vote", "restart-vote"]:
        # Voting logic
        if len(parts) < 3:
            await message.channel.send(f"❌ Usage: !MCServer {action} <number_of_users>")
            return

        try:
            required_votes = int(parts[2])
            if required_votes < 1:
                raise ValueError("Number of users must be at least 1.")
        except ValueError:
            await message.channel.send("❌ Invalid number of users. Please provide a valid integer.")
            return

        vote_message = await message.channel.send(
            f"🗳️ Vote to {'shutdown' if action == 'shutdown-vote' else 'restart'} the server. "
            f"React with ✅ to vote. {required_votes} votes required."
        )
        await vote_message.add_reaction("✅")

        def check(reaction, user):
            return reaction.message.id == vote_message.id and str(reaction.emoji) == "✅"

        try:
            reaction, users = await client.wait_for(
                "reaction_add",
                timeout=60.0,
                check=lambda reaction, user: check(reaction, user) and not user.bot
            )
            if reaction.count - 1 >= required_votes:
                if action == "shutdown-vote":
                    await handle_mcserver_commands(client, message, "!MCServer shutdown")
                elif action == "restart-vote":
                    await handle_mcserver_commands(client, message, "!MCServer restart")
            else:
                await message.channel.send("❌ Not enough votes to proceed.")
        except TimeoutError:
            await message.channel.send("❌ Voting timed out.")

    else:
        await message.channel.send("❌ Unknown action. Available actions: shutdown, restart, status, command, shutdown-vote, restart-vote.")