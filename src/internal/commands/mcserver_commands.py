import os
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from internal.commands.system_commands import is_authorized  # Import the is_authorized function

#
#
# Minecraft Server Commands
#
#

# Load environment variables
load_dotenv()
API_KEY = os.getenv("NITRADO_API_KEY")
SERVICE_ID = os.getenv("NITRADO_SERVICE_ID")

# Base URL for Nitrado API
BASE_URL = f"https://api.nitrado.net/services/{SERVICE_ID}"

async def send_nitrado_request(endpoint, method="GET", data=None):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"  # Content-Type header added
    }
    async with aiohttp.ClientSession() as session:
        try:
            if method == "GET":
                async with session.get(f"{BASE_URL}{endpoint}", headers=headers) as response:
                    if response.status == 404:
                        return {
                            "status": "error",
                            "message": f"Endpoint not found: {endpoint}"
                        }
                    elif response.content_type != "application/json":
                        return {
                            "status": "error",
                            "message": f"Unexpected response from server (Content-Type: {response.content_type})"
                        }
                    return await response.json()
                    
            elif method == "POST":
                # Correct endpoint for Nitrado API
                if endpoint == "/gameservers/shutdown":
                    endpoint = "/gameservers/stop"
                    data = {
                        "message": "Server shutdown requested via Discord Bot",
                        "stop_message": "(Discord Bot): Server is shutting down..."
                    }
                elif endpoint == "/gameservers/restart":
                    endpoint = "/gameservers/restart"
                    data = {
                        "message": "Server restart requested via Discord Bot",
                        "restart_message": "(Discord Bot): Server is restarting..."
                    }
                
                async with session.post(f"{BASE_URL}{endpoint}", headers=headers, json=data) as response:
                    if response.status == 401:
                        return {
                            "status": "error",
                            "message": "API token is invalid or expired."
                        }
                    elif response.status == 429:
                        return {
                            "status": "error",
                            "message": "Too many requests. Please wait a moment."
                        }
                    elif response.status == 503:
                        return {
                            "status": "error",
                            "message": "Maintenance. API temporarily unavailable."
                        }
                    elif response.status == 404:
                        return {
                            "status": "error",
                            "message": f"Endpoint not found: {endpoint}"
                        }
                    
                    try:
                        return await response.json()
                    except aiohttp.ContentTypeError:
                        text = await response.text()
                        return {
                            "status": "error",
                            "message": f"Unexpected response (Status {response.status}): {text[:100]}..."
                        }

        except aiohttp.ClientError as e:
            return {
                "status": "error",
                "message": f"Connection error: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Unexpected error: {str(e)}"
            }

# Command handler
async def handle_mcserver_commands(client, message, user_message):
    # Everyone can use !MCServer status
    if user_message.strip().lower() == "!mcserver status":
        response = await send_nitrado_request("/gameservers")
        if response and response.get("status") == "success":
            server_data = response["data"]["gameserver"]
            online = server_data.get("status", "unknown") == "started"
            ip = server_data.get("ip", "N/A")
            port = server_data.get("port", "N/A")
            ram = server_data.get("memory_mb", "N/A")
            slots = server_data.get("slots", "N/A")
            game = server_data.get("game_human", server_data.get("game", "N/A"))
            label = server_data.get("label", "N/A")
            last_change = server_data.get("last_status_change", None)
            modpack = None
            if "modpacks" in server_data and server_data["modpacks"]:
                for mp in server_data["modpacks"].values():
                    modpack = f"{mp.get('name', '')} {mp.get('modpack_version', '')} (MC {mp.get('game_version', '')})"
                    break

            from datetime import datetime
            last_change_str = (
                datetime.fromtimestamp(last_change).strftime("%d.%m.%Y %H:%M:%S")
                if last_change else "N/A"
            )

            embed = discord.Embed(
                title="🖥️ Minecraft Server Status",
                color=discord.Color.green() if online else discord.Color.red()
            )
            # First row: Online and IP:Port
            embed.add_field(name="Online", value=str(online), inline=True)
            embed.add_field(name="IP:Port", value=f"{ip}:{port}", inline=True)
            embed.add_field(name="", value="", inline=False)  # Empty row
            # Second row: RAM and Slots
            embed.add_field(name="RAM", value=f"{ram} MB", inline=True)
            embed.add_field(name="Slots", value=str(slots), inline=True)
            embed.add_field(name="", value="", inline=False)  # Empty row
            # Game as its own row
            embed.add_field(name="Game", value=game, inline=False)

            # Modpack as its own row (if available)
            if modpack:
                embed.add_field(name="Modpack", value=modpack, inline=False)

            # Last status change
            embed.add_field(name="Last status change", value=last_change_str, inline=False)

            await message.channel.send(embed=embed)

        return

    # Whitelist check for all other commands
    if not is_authorized(message.author):
        embed = discord.Embed(
            title="❌ Permission denied",
            description=f"{message.author.mention} You don't have permission to execute this command.",
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
        if response and response.get("status") == "success":
            await message.channel.send("✅ Server is shutting down.")
        else:
            await message.channel.send(f"❌ Failed to shut down the server: {response}")

    elif action == "restart":
        # Restart the server
        response = await send_nitrado_request("/gameservers/restart", method="POST")
        if response and response.get("status") == "success":
            await message.channel.send("✅ Server is restarting.")
        else:
            await message.channel.send(f"❌ Failed to restart the server: {response}")

    elif action == "status":
        response = await send_nitrado_request("/gameservers")
        if response and response.get("status") == "success":
            server_data = response["data"]["gameserver"]
            online = server_data.get("status", "unknown") == "started"
            ip = server_data.get("ip", "N/A")
            port = server_data.get("port", "N/A")
            ram = server_data.get("memory_mb", "N/A")
            slots = server_data.get("slots", "N/A")
            game = server_data.get("game_human", server_data.get("game", "N/A"))
            label = server_data.get("label", "N/A")
            last_change = server_data.get("last_status_change", None)
            modpack = None
            if "modpacks" in server_data and server_data["modpacks"]:
                for mp in server_data["modpacks"].values():
                    modpack = f"{mp.get('name', '')} {mp.get('modpack_version', '')} (MC {mp.get('game_version', '')})"
                    break

            from datetime import datetime
            last_change_str = (
                datetime.fromtimestamp(last_change).strftime("%d.%m.%Y %H:%M:%S")
                if last_change else "N/A"
            )

            embed = discord.Embed(
                title="🖥️ Minecraft Server Status",
                color=discord.Color.green() if online else discord.Color.red()
            )
            # First row: Online and IP:Port
            embed.add_field(name="Online", value=str(online), inline=True)
            embed.add_field(name="IP:Port", value=f"{ip}:{port}", inline=True)
            embed.add_field(name="", value="", inline=False)  # Empty row
            # Second row: RAM and Slots
            embed.add_field(name="RAM", value=f"{ram} MB", inline=True)
            embed.add_field(name="Slots", value=str(slots), inline=True)
            embed.add_field(name="", value="", inline=False)  # Empty row
            # Game as its own row
            embed.add_field(name="Game", value=game, inline=False)

            # Modpack as its own row (if available)
            if modpack:
                embed.add_field(name="Modpack", value=modpack, inline=False)

            # Last status change
            embed.add_field(name="Last status change", value=last_change_str, inline=False)

            await message.channel.send(embed=embed)

    elif action == "command":
        # Send a command to the server console
        if len(parts) < 3:
            await message.channel.send("❌ Usage: !MCServer command <minecraft_command>")
            return

        minecraft_command = " ".join(parts[2:])
        response = await send_nitrado_request("/gameservers/command", method="POST", data={"command": minecraft_command})
        if response and response.get("status") == "success":
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
            return (
                reaction.message.id == vote_message.id 
                and str(reaction.emoji) == "✅" 
                and not user.bot
            )

        collected_votes = 0
        try:
            while collected_votes < required_votes:
                # Wait for the next reaction
                reaction, user = await client.wait_for(
                    "reaction_add",
                    timeout=60.0,
                    check=check
                )
                collected_votes += 1
                
                # Inform about the progress
                if collected_votes < required_votes:
                    await message.channel.send(f"✅ Vote registered! {required_votes - collected_votes} more votes needed.")
            
            # Enough votes collected
            if action == "shutdown-vote":
                await handle_mcserver_commands(client, message, "!MCServer shutdown")
            else:
                await handle_mcserver_commands(client, message, "!MCServer restart")
                
        except TimeoutError:
            await message.channel.send("❌ Voting timed out.")
            try:
                await vote_message.clear_reactions()
            except:
                pass

    else:
        await message.channel.send("❌ Unknown action. Available actions: shutdown, restart, status, command, shutdown-vote, restart-vote.")