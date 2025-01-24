import aiohttp # Asynchronous HTTP client library
from datetime import timedelta # For handling timeouts
import discord # discord.py library
import random
import json
import os
import sys
from . import utils

def is_authorized(user):
    # Checks if the user is on the whitelist
    try:
        config = utils.load_config()  # Load config using utils.py
        whitelist = config.get("whitelist", [])
        return str(user) in whitelist
    except Exception as e:
        print(f"Error checking authorization: {e}")
        return False

async def handle_command(client, message):
    # Handles user commands
    user_message = message.content.lower()

    username = message.author

    # Use message.author.mention to get the @username ping
    username_mention = message.author.mention  # Gives @username

    #
    #
    # Public commands
    #
    #

    # !help command
    if user_message == '!help':
        embed = discord.Embed(title="Help", description="Possible Commands", color=0x00ff00)
        embed.add_field(name="[System]", value="!shutdown, !full-shutdown, !restart", inline=False)
        embed.add_field(name="[Public]", value="!help, !info, !rules, !userinfo, !serverinfo, !catfact", inline=False)
        embed.add_field(name="[Moderation]", value="!kick, !ban, !unban, !timeout, !untimeout", inline=False)
        embed.add_field(name="[Utils]", value="!ping, !weather, !download", inline=False)
        embed.add_field(name="[Minigames]", value="!roll, !rps", inline=False)
        await message.channel.send(embed=embed)

    # !info command
    if user_message == '!info':
        embed = discord.Embed(title="Info", color=0x00ff00)
        embed.add_field(name="", value="This is a Discord Bot created by Minecraft Lets Play.", inline=False)
        embed.add_field(name="", value="The bot is currently in development and is regularly updated.", inline=False)
        embed.add_field(name="", value="Planned features will include: Moderation, different utilities, minigames and more.", inline=False)
        await message.channel.send(embed=embed)

    # !rules command
    if user_message == '!rules':
        rules_channel = discord.utils.get(message.guild.text_channels, name="rules")  # Replace "rules" with the actual name of your rules channel
        if rules_channel:
            await message.channel.send(f"Please read the rules here: {rules_channel.mention}")
        else:
            await message.channel.send("Sorry, I couldn't find a channel named 'rules'.")

    # !userinfo command
    if user_message.startswith('!userinfo'):
        # Get the username after the command
        username = user_message[len('!userinfo '):].strip()

        if username:
            # Search for the user by username in the guild (server)
            user = discord.utils.get(message.guild.members, name=username)

            if user:
                embed = discord.Embed(title=f"User Info: {user.name}", color=discord.Color.blue())
                embed.add_field(name="Joined at", value=user.joined_at.strftime("%B %d, %Y"))

                # Format the roles with backticks
                roles = " • ".join([f"{role.name}" for role in user.roles if role.name != "@everyone"])
                embed.add_field(name="Roles", value=roles)

                embed.set_thumbnail(url=user.avatar.url)
                await message.channel.send(embed=embed)
            else:
                await message.channel.send("Could not find a user with that username.")
        else:
            await message.channel.send("Please provide a valid username.")

    # !serverinfo command
    if user_message.startswith('!serverinfo'):
        guild = message.guild  # Get the guild (server)
        embed = discord.Embed(title=f"Server Info: {guild.name}", color=discord.Color.blue())

        # Add server details to the embed
        embed.add_field(name="Server ID", value=guild.id)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%B %d, %Y"))
        embed.add_field(name="Owner", value=guild.owner)
        embed.add_field(name="Member Count", value=guild.member_count)
        embed.add_field(name="Total Channels", value=len(guild.channels))
        embed.add_field(name="Roles", value=len(guild.roles))

        # Set server icon (if available)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # Send the embed message
        await message.channel.send(embed=embed)

    # Asynchronous function to get a random cat fact
    async def get_catfact():
        async with aiohttp.ClientSession() as session:
            async with session.get('https://catfact.ninja/fact') as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('fact')  # Return the cat fact
        return None

    # Handling the '!catfact' command
    if user_message == '!catfact':
        catfact = await get_catfact()  # Await the asynchronous function
        if catfact:
            await message.channel.send(catfact)  # Send the cat fact to the channel
        else:
            await message.channel.send("Sorry, I couldn't fetch a cat fact right now.")
    
    #
    #
    # Moderation commands
    #
    #

    # !kick command
    if user_message.startswith('!kick'):
        if is_authorized(message.author):
             # Check if a username or mention is provided
            args = user_message.split()
            if len(args) < 2:  # No username/mention provided
                await message.channel.send("Please specify a user to kick. Usage: `!kick <username>`")
                return

            username_to_kick = args[1]  # The username or mention passed as an argument

            try:
                # Search for the member by mention or username
                member = message.guild.get_member_named(username_to_kick) or \
                     discord.utils.get(message.guild.members, mention=username_to_kick)

                if member is None:
                    await message.channel.send(f"User `{username_to_kick}` not found.")
                    return

                # Kick the member
                await member.kick(reason=f"Kicked by {message.author}")
                await message.channel.send(f"{member.mention} has been kicked.")
            except Exception as e:
                await message.channel.send("Error kicking member. Make sure I have the proper permissions.")
                print(f"Error: {e}")  # Log the error for debugging
        else:
            embed = discord.Embed(
                title="Permission denied",
                description=f"{username_mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)

    # !ban command
    if user_message.startswith('!ban'):
        if is_authorized(message.author):
            args = user_message.split(maxsplit=2)  # Split command into parts
            if len(args) < 2:  # Check if a user mention/username is provided
                await message.channel.send("Please specify a user to ban. Usage: `!ban <username> [reason]`")
                return

            username_to_ban = args[1]  # Extract the username/mention
            reason = args[2] if len(args) > 2 else f"Banned by {message.author}"  # Extract reason or use default

            try:
                # Search for the member by mention or username
                member = message.guild.get_member_named(username_to_ban) or \
                     discord.utils.get(message.guild.members, mention=username_to_ban)

                if member is None:
                    await message.channel.send(f"User `{username_to_ban}` not found.")
                    return

                # Ban the member with the provided reason
                await member.ban(reason=reason)
                await message.channel.send(f"{member.mention} has been banned. Reason: {reason}")
            except Exception as e:
                await message.channel.send("Error banning member. Make sure I have the proper permissions.")
                print(f"Error: {e}")  # Log the error for debugging
        else:
            embed = discord.Embed(
                title="Permission denied",
                description=f"{username_mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)

    # !unban command
    if user_message.startswith('!unban'):
        if is_authorized(message.author):
            try:
                args = user_message.split(maxsplit=2)  # Split the command into parts
                if len(args) < 2:
                    await message.channel.send("Usage: `!unban <username#discriminator> [reason]`")
                    return

                # Extract the username and discriminator
                username_discriminator = args[1]
                reason = args[2] if len(args) > 2 else "No reason provided"

                # Fetch the list of banned users
                banned_users = await message.guild.bans()
                user_to_unban = None

                for ban_entry in banned_users:
                    user = ban_entry.user
                    if f"{user.name}#{user.discriminator}" == username_discriminator:
                        user_to_unban = user
                        break

                if user_to_unban:
                    # Unban the user
                    await message.guild.unban(user_to_unban, reason=reason)
                    await message.channel.send(f"{user_to_unban.mention} has been unbanned. Reason: {reason}")
                else:
                    await message.channel.send(f"User `{username_discriminator}` not found in the ban list.")

            except Exception as e:
                await message.channel.send("An error occurred while unbanning the user.")
                print(f"Error: {e}")
        else:
            # Permission denied embed
            username_mention = message.author.mention
            embed = discord.Embed(
                title="Permission denied",
                description=f"{username_mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)

    # !timeout command
    if user_message.startswith('!timeout'):
        if is_authorized(message.author):
            args = user_message.split(maxsplit=3)  # Split the command into parts
            if len(args) < 3:
                await message.channel.send("Usage: `!timeout @username <duration_in_minutes> [reason]`")
                return

            try:
                # Get the mentioned member
                member = message.mentions[0]
                duration = int(args[2])  # Duration in minutes
                reason = args[3] if len(args) > 3 else "No reason provided"

                # Apply timeout
                timeout_duration = timedelta(minutes=duration)
                await member.timeout(timeout_duration, reason=reason)

                await message.channel.send(f"{member.mention} has been timed out for {duration} minutes. Reason: {reason}")

            except IndexError:
                await message.channel.send("Please mention a valid user.")
            except ValueError:
                await message.channel.send("Please provide a valid duration in minutes.")
            except Exception as e:
                await message.channel.send("An error occurred while applying the timeout.")
                print(f"Error: {e}")
        else:
            embed = discord.Embed(
                title="Permission denied",
                description=f"{username_mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)

    # !untimeout command
    if user_message.startswith('!untimeout'):
        if is_authorized(message.author):
            try:
                # Get the mentioned member
                member = message.mentions[0]
                await member.timeout_until(None, reason="Timeout removed by moderator")

                await message.channel.send(f"{member.mention}'s timeout has been removed.")
            except IndexError:
                await message.channel.send("Please mention a valid user.")
            except Exception as e:
                await message.channel.send("An error occurred while removing the timeout.")
                print(f"Error: {e}")
        else:
            embed = discord.Embed(
                title="Permission denied",
                description=f"{username_mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)

    #
    #
    # System commands
    #
    #

    # !shutdown command
    if user_message == '!shutdown':
        if is_authorized(message.author):
            await message.channel.send("Shutting down...")
            await client.close()
        else:
            embed = discord.Embed(
                title="Permission denied",
                description=f"{username_mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)

    # !full-shutdown command
    if user_message == '!full-shutdown':
        if is_authorized(message.author):
            await message.channel.send("Shutting down the bot and the Raspberry Pi...")
            await client.close()
            os.system("sudo shutdown now")
        else:
            embed = discord.Embed(
                title="Permission denied",
                description=f"{username_mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)

    # !restart command
    if user_message == '!restart':
        if is_authorized(message.author):
            await message.channel.send("Restarting...")
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            embed = discord.Embed(
                title="Permission denied",
                description=f"{username_mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            
    #
    #
    # Utility commands
    #
    #
    
    # !ping command
    if user_message == '!ping':
        latency = round(client.latency * 1000)  # Latency in milliseconds
        await message.channel.send(f'Pong! Latency is {latency}ms')
        
    # !weather command
    
    def load_config():
        try:
            with open('config.json', 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading config file: {e}")
            return {}
    
    async def get_weather(location):
        config = utils.load_config()  # Load the config
        api_key = config.get('api_key')  # Get the API key
    
        if not api_key:
            print("API key is missing in the config.")
            return None

        base_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as response:
                return await response.json()

    if user_message.startswith('!weather'):
        location = user_message.split(' ', 1)[1] if len(user_message.split()) > 1 else 'Friedberg'
        weather_data = await get_weather(location)
 
        if weather_data and weather_data['cod'] == 200:
            	# Extract data from the weather response
            city_name = weather_data['name']
            temp = weather_data['main']['temp']
            description = weather_data['weather'][0]['description']
            humidity = weather_data['main']['humidity']
            pressure = weather_data['main']['pressure']
            wind_speed = weather_data['wind']['speed']
            wind_deg = weather_data['wind']['deg']
            
            # Determine embed color based on weather description
            if 'clear' in description or 'sun' in description:
                embed_color = discord.Color.gold()  # Sunny or clear
            elif 'rain' in description:
                embed_color = discord.Color.blue()  # Rainy
            elif 'storm' in description or 'thunder' in description:
                embed_color = discord.Color.dark_gray()  # Thunderstorm
            elif 'cloud' in description:
                embed_color = discord.Color.light_gray()  # Cloudy weather
            elif 'snow' in description:
                embed_color = discord.Color.white()  # Snow
            elif 'fog' in description or 'mist' in description:
                embed_color = discord.Color.light_gray()  # Foggy or misty
            elif 'drizzle' in description:
                embed_color = discord.Color.sky_blue()  # Drizzle
            elif 'extreme' in description or 'hurricane' in description or 'tornado' in description:
                embed_color = discord.Color.purple()  # Extreme weather
            else:
                embed_color = discord.Color.default()  # Default color

            # Sending formatted message
            embed = discord.Embed(title=f"Weather in {city_name}", color=embed_color)
            embed.add_field(name="Temperature", value=f"{temp}°C", inline=False)
            embed.add_field(name="Description", value=description.capitalize(), inline=False)
            embed.add_field(name="Humidity", value=f"{humidity}%", inline=False)
            embed.add_field(name="Pressure", value=f"{pressure} hPa", inline=False)
            embed.add_field(name="Wind", value=f"{wind_speed} m/s, {wind_deg}°", inline=False)
        else:
            await message.channel.send("Could not retrieve weather information. Make sure the location is valid.")

    # Return None for unhandled commands
    return None
