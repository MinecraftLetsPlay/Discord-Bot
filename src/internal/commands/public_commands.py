import discord
import aiohttp

    #
    #
    # Public commands
    #
    #
    
# Main def for handling public commands
async def handle_public_commands(client, message, user_message):

    # !help command
    if user_message == '!help':
        embed = discord.Embed(title="Help", description="Possible Commands", color=0x00ff00)
        embed.add_field(name="[System]", value="!shutdown, !full-shutdown, !restart", inline=False)
        embed.add_field(name="[Public]", value="!help, !info, !rules, !userinfo, !serverinfo, !catfact", inline=False)
        embed.add_field(name="[Moderation]", value="!kick, !ban, !unban, !timeout, !untimeout", inline=False)
        embed.add_field(name="[Utils]", value="!ping, !weather, !city, !download", inline=False)
        embed.add_field(name="[Minigames]", value="!roll, !rps, !quiz, !hangman", inline=False)
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
        # Remove the command part
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
        else:
            await message.channel.send("User not found. Please provide a valid username, mention, or ID.")

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
