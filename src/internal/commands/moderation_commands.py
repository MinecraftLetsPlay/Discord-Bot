import discord
import logging
from internal import utils
from datetime import timedelta
from internal.commands.system_commands import is_authorized_server

# ----------------------------------------------------------------
# Component test function for [Moderation Commands]
# ----------------------------------------------------------------

def component_test():
    status = "🟩"
    messages = ["Moderation commands module loaded."]

    # Test 1: Check if config.json exists and is valid
    try:
        config = utils.load_config()
        if not config:
            status = "🟧"
            messages.append("Warning: config.json is missing or empty.")
        else:
            messages.append("config.json loaded.")
    except Exception as e:
        status = "🟥"
        messages.append(f"Error loading config.json: {e}")

    # Test 2: Check if reactionrole.json exists and is valid
    try:
        reaction_role_data = utils.load_reaction_role_data()
        if reaction_role_data is None:
            status = "🟧"
            messages.append("Warning: reactionrole.json is missing or empty.")
        else:
            messages.append("reactionrole.json loaded.")
    except Exception as e:
        status = "🟥"
        messages.append(f"Error loading reactionrole.json: {e}")

    return {"status": status, "msg": " | ".join(messages)}

# ----------------------------------------------------------------
# Main command handler for [Moderation Commands]
# ----------------------------------------------------------------

# Main def for handling moderation commands
async def handle_moderation_commands(client, message, user_message):

    # ----------------------------------------------------------------
    # Command: !kick
    # Category: Moderation Commands
    # Type: Full Command
    # Description: Kick a user from the server
    # ----------------------------------------------------------------
    
    # check if the message starts with !kick
    if user_message.startswith('!kick'):
        if is_authorized_server(message.author, guild_id=message.guild.id):
            # Check if a username or mention is provided
            args = user_message.split()
            if len(args) < 2:  # No username/mention provided
                await message.channel.send("ℹ️ Please specify a user to kick. Usage: `!kick <username>`")
                return

            username_to_kick = args[1]  # The username or mention passed as an argument

            try:
                # Search for the member by mention or username
                member = message.guild.get_member_named(username_to_kick) or \
                    discord.utils.get(message.guild.members, mention=username_to_kick)

                if member is None:
                    await message.channel.send(f"⚠️ User `{username_to_kick}` not found.")
                    return

                # Prevent kicking yourself or the bot
                if member == message.author:
                    await message.channel.send("❌ You cannot kick yourself.")
                    return

                if member == message.guild.me:
                    await message.channel.send("❌ I cannot kick myself.")
                    return

                # Kick the member
                await member.kick(reason=f"Kicked by {message.author}")
                await message.channel.send(f"{member.mention} has been kicked.")
                logging.info(f"{member.mention} has been kicked by {message.author}.")
            except IndexError:
                await message.channel.send("ℹ️ Please mention a valid user.")
                logging.warning("ℹ️ Invalid user mention for kick command.")
            except discord.Forbidden:
                await message.channel.send("⚠️ I don't have permission to kick members. Please check my role permissions.")
                logging.warning("⚠️ Permission denied for kick command.")
            except Exception as e:
                await message.channel.send("❌ Error kicking member. Make sure I have the proper permissions.")
                logging.error(f"❌ Error kicking member: {e}")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.warning(f"❌ Permission denied for kick command by {message.author}.")

    # ----------------------------------------------------------------
    # Command: !ban
    # Category: Moderation Commands
    # Type: Full Command
    # Description: Ban a user from the server
    # ----------------------------------------------------------------
    
    if user_message.startswith('!ban'):
        if is_authorized_server(message.author, guild_id=message.guild.id):
            args = user_message.split(maxsplit=2)  # Split command into parts
            if len(args) < 2:  # Check if a user mention/username is provided
                await message.channel.send("ℹ️ Please specify a user to ban. Usage: `!ban <username> [reason]`")
                return

            username_to_ban = args[1]  # Extract the username/mention
            reason = args[2] if len(args) > 2 else f"Banned by {message.author}"  # Extract reason or use default

            try:
                # Search for the member by mention or username
                member = message.guild.get_member_named(username_to_ban) or \
                    discord.utils.get(message.guild.members, mention=username_to_ban)

                if member is None:
                    await message.channel.send(f"⚠️ User `{username_to_ban}` not found.")
                    return

                # Prevent banning yourself or the bot
                if member == message.author:
                    await message.channel.send("❌ You cannot ban yourself.")
                    return

                if member == message.guild.me:
                    await message.channel.send("❌ I cannot ban myself.")
                    return

                # Ban the member with the provided reason
                await member.ban(reason=reason)
                await message.channel.send(f"{member.mention} has been banned. Reason: {reason}")
                logging.info(f"{member.mention} has been banned by {message.author}. Reason: {reason}")
            except discord.Forbidden:
                await message.channel.send("⚠️ I don't have permission to ban members. Please check my role permissions.")
                logging.warning("⚠️ Permission denied for ban command.")
            except IndexError:
                await message.channel.send("ℹ️ Please mention a valid user.")
                logging.warning("ℹ️ Invalid user mention for ban command.")
            except Exception as e:
                await message.channel.send("❌ Error banning member. Make sure I have the proper permissions.")
                logging.error(f"❌ Error banning member: {e}")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.warning(f"❌ Permission denied for ban command by {message.author}.")

    # ----------------------------------------------------------------
    # Command: !unban
    # Category: Moderation Commands
    # Type: Full Command
    # Description: Unban a user from the server
    # ----------------------------------------------------------------
    
    if user_message.startswith('!unban'):
        if is_authorized_server(message.author, guild_id=message.guild.id):
            try:
                args = user_message.split(maxsplit=2)  # Split the command into parts
                if len(args) < 2:
                    await message.channel.send("ℹ️ Usage: `!unban <username> [reason]`")
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
                    logging.info(f"{user_to_unban.mention} has been unbanned by {message.author}. Reason: {reason}")
                else:
                    await message.channel.send(f"⚠️ User `{username_discriminator}` not found in the ban list.")
                    logging.warning(f"⚠️ User `{username_discriminator}` not found in the ban list.")
            except Exception as e:
                await message.channel.send("❌ An error occurred while unbanning the user.")
                logging.error(f"❌ Error unbanning user: {e}")
        else:
            # Permission denied embed
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.warning(f"❌ Permission denied for unban command by {message.author}.")

    # ----------------------------------------------------------------
    # Command: !timeout
    # Category: Moderation Commands
    # Type: Full Command
    # Description: Timeout a user for a specified duration
    # ----------------------------------------------------------------
    
    if user_message.startswith('!timeout'):
        if is_authorized_server(message.author, guild_id=message.guild.id):
            args = user_message.split(maxsplit=3)  # Split the command into parts
            if len(args) < 3:
                await message.channel.send("ℹ️ Usage: `!timeout @username <duration_in_minutes> [reason]`")
                return

            try:
                # Get the mentioned member
                member = message.mentions[0]
                duration = int(args[2])  # Duration in minutes
                reason = args[3] if len(args) > 3 else "No reason provided"
                
                if duration < 1 or duration > 40320:  # 40320 Minutes = 28 Days
                    await message.channel.send("⚠️ Duration must be between 1 minute and 28 days.")
                    return

                # Apply timeout
                timeout_duration = timedelta(minutes=duration)
                await member.timeout(timeout_duration, reason=reason)

                await message.channel.send(f"{member.mention} has been timed out for {duration} minutes. Reason: {reason}")
                logging.info(f"{member.mention} has been timed out for {duration} minutes by {message.author}. Reason: {reason}")
            except IndexError:
                await message.channel.send("ℹ️ Please mention a valid user.")
                logging.warning("ℹ️ Invalid user mention for timeout command.")
            except ValueError:
                await message.channel.send("ℹ️ Please provide a valid duration in minutes.")
                logging.warning("ℹ️ Invalid duration for timeout command.")
            except discord.Forbidden:
                await message.channel.send("⚠️ I don't have permission to timeout members. Please check my role permissions.")
                logging.warning("⚠️ Permission denied for timeout command.")
            except Exception as e:
                await message.channel.send("❌ An error occurred while applying the timeout.")
                logging.error(f"❌ Error applying timeout: {e}")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.warning(f"❌ Permission denied for timeout command by {message.author}.")

    # ----------------------------------------------------------------
    # Command: !untimeout
    # Category: Moderation Commands
    # Type: Full Command
    # Description: Remove timeout from a users
    # ----------------------------------------------------------------
    
    if user_message.startswith('!untimeout'):
        if is_authorized_server(message.author, guild_id=message.guild.id):
            try:
                # Get the mentioned member
                member = message.mentions[0]
                await member.timeout_until(None, reason="Timeout removed by moderator")

                await message.channel.send(f"{member.mention}'s timeout has been removed.")
                logging.info(f"{member.mention}'s timeout has been removed by {message.author}.")
            except IndexError:
                await message.channel.send("ℹ️ Please mention a valid user.")
                logging.warning("ℹ️ Invalid user mention for untimeout command.")
            except discord.Forbidden:
                await message.channel.send("⚠️ I don't have permission to untimeout members. Please check my role permissions.")
                logging.warning("⚠️ Permission denied for untimeout command.")
            except Exception as e:
                await message.channel.send("❌ An error occurred while removing the timeout.")
                logging.error(f"❌ Error removing timeout: {e}")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.warning(f"❌ Permission denied for untimeout command by {message.author}.")
            
    # -----------------------------------------------------------------------------
    # Command: !reactionrole
    # Category: Moderation Commands
    # Type: Full Command
    # Description: Set up reaction roles or clear all reaction roles for the server
    # -----------------------------------------------------------------------------
    
    if user_message.startswith('!reactionrole'):
        if is_authorized_server(message.author, guild_id=message.guild.id):
            args = user_message.split(maxsplit=3)
            
            # Check for clear command
            if len(args) == 2 and args[1].lower() == "clear":
                try:
                    reaction_role_data = utils.load_reaction_role_data()
                    guild_id = str(message.guild.id)
                    
                    # Only clear reaction roles for this server
                    if guild_id in reaction_role_data:
                        for message_data in reaction_role_data[guild_id]:
                            try:
                                channel = client.get_channel(int(message_data["channelID"]))
                                if channel:
                                    msg = await channel.fetch_message(int(message_data["messageID"]))
                                    await msg.clear_reactions()
                            except:
                                logging.warning(f"Could not clear reactions from message {message_data['messageID']}")
                    
                        # Only delete the entry for this server
                        del reaction_role_data[guild_id]
                        utils.save_reaction_role_data(reaction_role_data)
                        
                        await message.channel.send("✅ All reaction roles for this server have been cleared.")
                        logging.info(f"✅ Reaction roles cleared for server {guild_id} by {message.author}.")
                    else:
                        await message.channel.send("ℹ️ No reaction roles found for this server.")
                    return
                except Exception as e:
                    await message.channel.send("❌ An error occurred while clearing reaction roles.")
                    logging.error(f"❌ Error clearing reaction roles: {e}")
                    return
                
            if len(args) < 4:
                await message.channel.send("ℹ️ Usage: `!reactionrole <message_id> <emoji> <role_id>`")
                return

            message_id = args[1]
            emoji = args[2]
            role_id = args[3]
            
            role = message.guild.get_role(int(role_id))
            if not role:
                await message.channel.send("⚠️ Role not found. Please provide a valid role ID.")
                return

            try:
                channel = message.channel
                target_message = await channel.fetch_message(message_id)
                await target_message.add_reaction(emoji)

                # Load existing reaction role data
                reaction_role_data = utils.load_reaction_role_data()
                guild_id = str(message.guild.id)

                # Create a new entry if it doesn't exist
                if guild_id not in reaction_role_data:
                    reaction_role_data[guild_id] = []

                # Add or update the reaction role entry
                new_entry = {
                    "messageID": message_id,
                    "channelID": str(channel.id),
                    "roles": [{
                        "emoji": emoji,
                        "roleID": role_id
                    }]
                }

                # Check if the message already exists in the data
                message_entry = next(
                    (item for item in reaction_role_data[guild_id] 
                    if item["messageID"] == message_id), 
                    None
                )

                if message_entry:
                    # Add the new role to the existing message entry
                    message_entry["roles"].append({
                        "emoji": emoji,
                        "roleID": role_id
                    })
                else:
                    # Add a new message entry
                    reaction_role_data[guild_id].append(new_entry)

                # Save the updated reaction role data
                utils.save_reaction_role_data(reaction_role_data)

                await message.channel.send(
                    f"✅ Reaction role set up successfully for message ID {message_id} "
                    f"with emoji {emoji} and role ID {role_id}."
                )
                logging.info(
                    f"✅ Reaction role set up successfully for message ID {message_id} "
                    f"with emoji {emoji} and role ID {role_id} by {message.author} "
                    f"in server {guild_id}"
                )

            except discord.NotFound:
                await message.channel.send("❌ Message not found. Please provide a valid message ID.")
                logging.error("❌ Message not found for reaction role setup.")
            except discord.Forbidden:
                await message.channel.send("⚠️ I don't have permission to add reactions.")
                logging.warning("⚠️ Permission denied for adding reaction.")
            except Exception as e:
                await message.channel.send("❌ An error occurred while setting up the reaction role.")
                logging.error(f"❌ Error setting up reaction role: {e}")
        else:
            embed = discord.Embed(
                title="❌ Permission denied",
                description=f"{message.author.mention} You don't have the permission to execute this command.",
                color=0xff0000
            )
            await message.channel.send(embed=embed)
            logging.warning(f"❌ Permission denied for reaction role command by {message.author}.")
