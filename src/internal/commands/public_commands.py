import discord
import aiohttp
import logging
from internal import utils
from internal.command_router import command_groups

#
#
# Public commands
#
#

# Main def for handling public commands
async def handle_public_commands(client, message, user_message):
    config = utils.load_config()

    # !help command
    if user_message == '!help':
        embed = discord.Embed(title="Help", description="Possible Commands", color=0x00ff00)
        for category, commands in command_groups.items():
            embed.add_field(name=f"[{category.capitalize()}]", value=", ".join(commands), inline=False)
        await message.channel.send(embed=embed)
        logging.info("Displayed help message.")

    # !info command
    if user_message == '!info':
        embed = discord.Embed(title="Info", color=0x00ff00)
        embed.add_field(name="", value="This is a Discord Bot created by Minecraft Lets Play.", inline=False)
        embed.add_field(name="", value="The bot is currently in development and is regularly updated.", inline=False)
        embed.add_field(name="", value="The Bot is mainly developed by myself but there is also a co-developer \n which helps me: little_fox_e", inline=False)
        embed.add_field(name="", value="The bot is hosted inside my home on a Raspberry Pi 3 Model B \n (Quad-Core 64bit 1.2GHz CPU and 1GB of RAM).", inline=False)
        embed.add_field(name="", value="The programming language the Bot is made of is Python. \n It is using the Discord.py API Wrapper.", inline=False)
        embed.add_field(name="", value="Planned features will include: Moderation, different utilities, minigames and more.", inline=False)

        # Create buttons
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Creator's Github", url="https://github.com/MinecraftLetsPlay"))
        view.add_item(discord.ui.Button(label="Contributer's Github", url="https://github.com/olittlefoxE"))
        view.add_item(discord.ui.Button(label="API Wrapper Docs", url="https://discordpy.readthedocs.io/en/stable/"))

        await message.channel.send(embed=embed, view=view)
        logging.info("Displayed info message with buttons.")

    # !rules command
    if user_message == '!rules':
        rules_channel_name = config.get("rules_channel_name", "rules")
        rules_channel = discord.utils.get(message.guild.text_channels, name=rules_channel_name)
        if rules_channel:
            await message.channel.send(f"Please read the rules here: {rules_channel.mention}")
            logging.info("Displayed rules channel mention.")
        else:
            await message.channel.send("ℹ️ Sorry, I couldn't find the rules channel.")
            logging.warning("Rules channel not found.")

    # !userinfo command
    if user_message.startswith('!userinfo'):
        user_identifier = user_message[len('!userinfo '):].strip()

        user = None

        if user_identifier:
            # Check if the identifier is a mention
            if user_identifier.startswith('<@') and user_identifier.endswith('>'):
                user_id = int(user_identifier[2:-1].replace('!', ''))  # Extract ID
                user = message.guild.get_member(user_id)

            # Check if the identifier is a valid numeric ID (for example: '657631926613573632')
            elif user_identifier.isdigit():
                user_id = int(user_identifier)
                user = message.guild.get_member(user_id)

            else:
                # If the identifier has a '#', split into username and discriminator
                if '#' in user_identifier:
                    username, discriminator = user_identifier.split('#', 1)
                    user = discord.utils.get(message.guild.members, name=username, discriminator=discriminator)
                else:
                    # Fallback to search by name only if there's no discriminator
                    user = discord.utils.get(message.guild.members, name=user_identifier)

        else:
            user = message.author  # Default to the author if no input is provided

        if user:
            embed = discord.Embed(title=f"User Info: {user.name}", color=discord.Color.blue())
            embed.add_field(name="Joined at", value=user.joined_at.strftime("%B %d, %Y"))
            roles = " • ".join([role.name for role in user.roles if role.name != "@everyone"])
            embed.add_field(name="Roles", value=roles if roles else "No roles")
            embed.set_thumbnail(url=user.avatar.url)
            await message.channel.send(embed=embed)
            logging.info(f"Displayed user info for {user.name}.")
        else:
            await message.channel.send("⚠️ User not found. Please provide a valid username, mention, or ID.")
            logging.warning("User not found !userinfo command.")

    # !serverinfo command
    if user_message.startswith('!serverinfo'):
        guild = message.guild  # Get the guild (server)
        embed = discord.Embed(title=f"Server Info: {guild.name}", color=discord.Color.blue())

        # Server details
        embed.add_field(name="Server ID", value=guild.id)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%B %d, %Y"))
        embed.add_field(name="Owner", value=guild.owner)
        embed.add_field(name="Member Count", value=guild.member_count)
        embed.add_field(name="Total Channels", value=f"Text: {len(guild.text_channels)}, Voice: {len(guild.voice_channels)}")
        embed.add_field(name="Roles", value=len(guild.roles))

        # Set server icon (if available)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await message.channel.send(embed=embed)
        logging.info(f"Displayed server info for {guild.name}.")

    # !catfact command
    if user_message == '!catfact':
        async def get_catfact():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get('https://catfact.ninja/fact') as response:
                        if response.status == 200:
                            data = await response.json()
                            return data.get('fact')
                        else:
                            logging.warning(f"Failed to fetch cat fact. Status code: {response.status}")
            except aiohttp.ClientError as e:
                logging.error(f"❌ API request failed: {e}")
            return None

        catfact = await get_catfact()
        if catfact:
            await message.channel.send(catfact)
            logging.info("Displayed a cat fact.")
        else:
            await message.channel.send("⚠️ Sorry, I couldn't fetch a cat fact right now.")
            logging.warning("Failed to fetch a cat fact.")
