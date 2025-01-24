import random
import discord
import os
import sys
from datetime import timedelta
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
    #Handles user commands
    user_message = message.content.lower()

    username = message.author

    # Use message.author.mention to get the @username ping
    username_mention = message.author.mention  # This gives @username
    
    #
    #
    # Public commands
    #
    #

    # !help command
    if user_message == '!help':
        embed = discord.Embed(title="Help", description="Possible Commands", color=0x00ff00)
        embed.add_field(name="[System]", value="!shutdown, !restart", inline=False)
        embed.add_field(name="[Public]", value="!roll, !info, !ping", inline=False)
        embed.add_field(name="[Moderation]", value="!kick, !ban, !unban, !timeout, !untimeout", inline=False)
        await message.channel.send(embed=embed)
        
    # !info command
    if user_message == '!info':
        embed = discord.Embed(title="Info", color=0x00ff00)
        embed.add_field(name="", value="This is a Discord Bot created by Minecraft Lets Play.", inline=False)
        embed.add_field(name="", value="The bot is currently in development and is regularly updated.", inline=False)
        embed.add_field(name="", value="Planned features will include: Moderation, different utilities, minigames and more.", inline=False)
        await message.channel.send(embed=embed)
        
    # !roll command
    if user_message == '!roll':
        return str(random.randint(1, 6))
    
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

    # Return None for unhandled commands
    return None
