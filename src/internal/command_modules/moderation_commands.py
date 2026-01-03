import discord
import logging
from internal import utils
from datetime import timedelta
from internal.utils import is_authorized_server

# Copyright (c) 2026 Dennis Plischke.
# All rights reserved.

# ================================================================
# Module: Moderation_commands.py
# Description: Discord moderation like kick and ban
# Error handling for permission checks and Discord API calls included
# ================================================================

# ----------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------

# Safe Discord Message Sending with Error Handling
async def safe_send(message_obj, content=None, embed=None, view=None):
    try:
        return await message_obj.channel.send(content=content, embed=embed, view=view)
    except discord.Forbidden:
        logging.error(f"Missing permission to send message in {message_obj.channel}")
        return None
    except discord.HTTPException as e:
        logging.error(f"Failed to send message: {e}")
        return None


# Permission Denied Helper
async def send_permission_denied(message_obj, user_action="execute this command"):
    embed = discord.Embed(
        title="❌ Permission denied",
        description=f"{message_obj.author.mention} You don't have the permission to {user_action}.",
        color=0xff0000
    )
    await safe_send(message_obj, embed=embed)


# Check if user has higher role than target
def has_higher_role(actor, target):
    if actor.guild.owner == actor:
        return True  # Owner always has higher role
    if actor.top_role <= target.top_role:
        return False
    return True


# Validate text length for Discord limits
def validate_text_length(text, max_length=2048, field_name="Text"):
    if len(text) > max_length:
        return False, f"{field_name} too long (max {max_length} characters)"
    return True, None


# ----------------------------------------------------------------
# Component test function for [Moderation Commands]
# ----------------------------------------------------------------

async def component_test():
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
            args = user_message.split(maxsplit=2)
            if len(args) < 2:  # No username/mention provided
                await safe_send(message, content="ℹ️ Please specify a user to kick. Usage: `!kick <username> [reason]`")
                return

            username_to_kick = args[1]  # The username or mention passed as an argument
            reason = args[2] if len(args) > 2 else f"Kicked by {message.author}"
            
            # Validate reason length
            is_valid, error_msg = validate_text_length(reason, max_length=512, field_name="Reason")
            if not is_valid:
                await safe_send(message, content=f"⚠️ {error_msg}")
                return

            try:
                # Search for the member by mention or username
                member = message.guild.get_member_named(username_to_kick) or \
                    discord.utils.get(message.guild.members, mention=username_to_kick)

                if member is None:
                    await safe_send(message, content=f"⚠️ User `{username_to_kick}` not found.")
                    return

                # Prevent kicking yourself or the bot
                if member == message.author:
                    await safe_send(message, content="❌ You cannot kick yourself.")
                    return

                if member == message.guild.me:
                    await safe_send(message, content="❌ I cannot kick myself.")
                    return

                # Check role hierarchy
                if not has_higher_role(message.author, member):
                    await safe_send(message, content="⚠️ You cannot kick a member with an equal or higher role.")
                    logging.warning(f"Role hierarchy check failed for kick command by {message.author}.")
                    return

                # Kick the member
                await member.kick(reason=reason)
                await safe_send(message, content=f"{member.mention} has been kicked. Reason: {reason}")
                logging.info(f"{member.mention} has been kicked by {message.author}. Reason: {reason}")
            except IndexError:
                await safe_send(message, content="ℹ️ Please mention a valid user.")
                logging.warning("Invalid user mention for kick command.")
            except discord.Forbidden:
                await safe_send(message, content="⚠️ I don't have permission to kick members. Please check my role permissions.")
                logging.warning("Permission denied for kick command.")
            except Exception as e:
                await safe_send(message, content="❌ Error kicking member. Make sure I have the proper permissions.")
                logging.error(f"Error kicking member: {e}")
        else:
            await send_permission_denied(message, "kick members")
            logging.warning(f"Permission denied for kick command by {message.author}.")

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
                await safe_send(message, content="ℹ️ Please specify a user to ban. Usage: `!ban <username> [reason]`")
                return

            username_to_ban = args[1]  # Extract the username/mention
            reason = args[2] if len(args) > 2 else f"Banned by {message.author}"  # Extract reason or use default
            
            # Validate reason length
            is_valid, error_msg = validate_text_length(reason, max_length=512, field_name="Reason")
            if not is_valid:
                await safe_send(message, content=f"⚠️ {error_msg}")
                return

            try:
                # Search for the member by mention or username
                member = message.guild.get_member_named(username_to_ban) or \
                    discord.utils.get(message.guild.members, mention=username_to_ban)

                if member is None:
                    await safe_send(message, content=f"⚠️ User `{username_to_ban}` not found.")
                    return

                # Prevent banning yourself or the bot
                if member == message.author:
                    await safe_send(message, content="❌ You cannot ban yourself.")
                    return

                if member == message.guild.me:
                    await safe_send(message, content="❌ I cannot ban myself.")
                    return

                # Check role hierarchy
                if not has_higher_role(message.author, member):
                    await safe_send(message, content="⚠️ You cannot ban a member with an equal or higher role.")
                    logging.warning(f"Role hierarchy check failed for ban command by {message.author}.")
                    return

                # Ban the member with the provided reason
                await member.ban(reason=reason)
                await safe_send(message, content=f"{member.mention} has been banned. Reason: {reason}")
                logging.info(f"{member.mention} has been banned by {message.author}. Reason: {reason}")
            except discord.Forbidden:
                await safe_send(message, content="⚠️ I don't have permission to ban members. Please check my role permissions.")
                logging.warning("Permission denied for ban command.")
            except IndexError:
                await safe_send(message, content="ℹ️ Please mention a valid user.")
                logging.warning("Invalid user mention for ban command.")
            except Exception as e:
                await safe_send(message, content="❌ Error banning member. Make sure I have the proper permissions.")
                logging.error(f"Error banning member: {e}")
        else:
            await send_permission_denied(message, "ban members")
            logging.warning(f"Permission denied for ban command by {message.author}.")

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
                    await safe_send(message, content="ℹ️ Usage: `!unban <user_id> [reason]`")
                    return

                user_id_str = args[1]
                reason = args[2] if len(args) > 2 else "No reason provided"
                
                # Validate reason length
                is_valid, error_msg = validate_text_length(reason, max_length=512, field_name="Reason")
                if not is_valid:
                    await safe_send(message, content=f"⚠️ {error_msg}")
                    return

                # Try to parse user ID
                try:
                    user_id = int(user_id_str)
                except ValueError:
                    await safe_send(message, content="⚠️ Please provide a valid user ID (numeric).")
                    logging.warning(f"Invalid user ID format: {user_id_str}")
                    return

                # Fetch the list of banned users
                banned_users = await message.guild.bans()
                user_to_unban = None

                for ban_entry in banned_users:
                    if ban_entry.user.id == user_id:
                        user_to_unban = ban_entry.user
                        break

                if user_to_unban:
                    # Unban the user
                    await message.guild.unban(user_to_unban, reason=reason)
                    await safe_send(message, content=f"{user_to_unban.mention} has been unbanned. Reason: {reason}")
                    logging.info(f"{user_to_unban.mention} has been unbanned by {message.author}. Reason: {reason}")
                else:
                    await safe_send(message, content=f"⚠️ User ID `{user_id}` not found in the ban list.")
                    logging.warning(f"User ID `{user_id}` not found in the ban list.")
            except Exception as e:
                await safe_send(message, content="❌ An error occurred while unbanning the user.")
                logging.error(f"Error unbanning user: {e}")
        else:
            await send_permission_denied(message, "unban members")
            logging.warning(f"Permission denied for unban command by {message.author}.")

    # ----------------------------------------------------------------
    # Command: !timeout
    # Category: Moderation Commands
    # Type: Full Command
    # Description: Timeout a user for a specified duration
    # ----------------------------------------------------------------
    
    if user_message.startswith('!timeout'):
        if is_authorized_server(message.author, guild_id=message.guild.id):
            # Check if user mentioned someone
            if not message.mentions:
                await safe_send(message, content="ℹ️ Please mention a valid user. Usage: `!timeout @user <duration_in_minutes> [reason]`")
                logging.warning("Invalid user mention for timeout command.")
                return
            
            args = user_message.split(maxsplit=3)  # Split the command into parts
            if len(args) < 3:
                await safe_send(message, content="ℹ️ Usage: `!timeout @username <duration_in_minutes> [reason]`")
                return

            try:
                # Get the mentioned member
                member = message.mentions[0]
                duration = int(args[2])  # Duration in minutes
                reason = args[3] if len(args) > 3 else "No reason provided"
                
                # Validate reason length
                is_valid, error_msg = validate_text_length(reason, max_length=512, field_name="Reason")
                if not is_valid:
                    await safe_send(message, content=f"⚠️ {error_msg}")
                    return
                
                # Validate duration (Discord max is 28 days = 40320 minutes)
                if duration < 1 or duration > 40320:
                    await safe_send(message, content="⚠️ Duration must be between 1 minute and 28 days (40320 minutes).")
                    return
                
                # Prevent timing out yourself or the bot
                if member == message.author:
                    await safe_send(message, content="❌ You cannot timeout yourself.")
                    return
                
                if member == message.guild.me:
                    await safe_send(message, content="❌ I cannot timeout myself.")
                    return
                
                # Check role hierarchy
                if not has_higher_role(message.author, member):
                    await safe_send(message, content="⚠️ You cannot timeout a member with an equal or higher role.")
                    logging.warning(f"Role hierarchy check failed for timeout command by {message.author}.")
                    return

                # Apply timeout
                timeout_duration = timedelta(minutes=duration)
                await member.timeout(timeout_duration, reason=reason)

                await safe_send(message, content=f"{member.mention} has been timed out for {duration} minutes. Reason: {reason}")
                logging.info(f"{member.mention} has been timed out for {duration} minutes by {message.author}. Reason: {reason}")
            except ValueError:
                await safe_send(message, content="ℹ️ Please provide a valid duration in minutes (numeric value).")
                logging.warning("Invalid duration for timeout command.")
            except discord.Forbidden:
                await safe_send(message, content="⚠️ I don't have permission to timeout members. Please check my role permissions.")
                logging.warning("Permission denied for timeout command.")
            except discord.HTTPException as e:
                await safe_send(message, content="❌ An error occurred while applying the timeout.")
                logging.error(f"Discord API error applying timeout: {e}")
            except Exception as e:
                await safe_send(message, content="❌ An error occurred while applying the timeout.")
                logging.error(f"Error applying timeout: {e}")
        else:
            await send_permission_denied(message, "timeout members")
            logging.warning(f"Permission denied for timeout command by {message.author}.")

    # ----------------------------------------------------------------
    # Command: !untimeout
    # Category: Moderation Commands
    # Type: Full Command
    # Description: Remove timeout from a user
    # ----------------------------------------------------------------
    
    if user_message.startswith('!untimeout'):
        if is_authorized_server(message.author, guild_id=message.guild.id):
            # Check if user mentioned someone
            if not message.mentions:
                await safe_send(message, content="ℹ️ Please mention a valid user. Usage: `!untimeout @user`")
                logging.warning("Invalid user mention for untimeout command.")
                return
            
            try:
                # Get the mentioned member
                member = message.mentions[0]
                
                # Prevent removing timeout from yourself or the bot
                if member == message.author:
                    await safe_send(message, content="❌ You cannot remove timeout from yourself.")
                    return
                
                if member == message.guild.me:
                    await safe_send(message, content="❌ I cannot remove timeout from myself.")
                    return
                
                # Check role hierarchy
                if not has_higher_role(message.author, member):
                    await safe_send(message, content="⚠️ You cannot remove timeout from a member with an equal or higher role.")
                    logging.warning(f"Role hierarchy check failed for untimeout command by {message.author}.")
                    return

                await member.timeout_until(None, reason="Timeout removed by moderator")

                await safe_send(message, content=f"{member.mention}'s timeout has been removed.")
                logging.info(f"{member.mention}'s timeout has been removed by {message.author}.")
            except discord.Forbidden:
                await safe_send(message, content="⚠️ I don't have permission to remove timeouts. Please check my role permissions.")
                logging.warning("Permission denied for untimeout command.")
            except Exception as e:
                await safe_send(message, content="❌ An error occurred while removing the timeout.")
                logging.error(f"Error removing timeout: {e}")
        else:
            await send_permission_denied(message, "remove timeouts")
            logging.warning(f"Permission denied for untimeout command by {message.author}.")
            
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
                        
                        await safe_send(message, content="✅ All reaction roles for this server have been cleared.")
                        logging.info(f"Reaction roles cleared for server {guild_id} by {message.author}.")
                    else:
                        await safe_send(message, content="ℹ️ No reaction roles found for this server.")
                    return
                except Exception as e:
                    await safe_send(message, content="❌ An error occurred while clearing reaction roles.")
                    logging.error(f"Error clearing reaction roles: {e}")
                    return
                
            if len(args) < 4:
                await safe_send(message, content="ℹ️ Usage: `!reactionrole <message_id> <emoji> <role_id>` or `!reactionrole clear`")
                return

            message_id = args[1]
            emoji = args[2]
            role_id = args[3]
            
            # Validate message_id format
            try:
                int(message_id)
            except ValueError:
                await safe_send(message, content="⚠️ Message ID must be numeric.")
                return
            
            # Validate role_id format
            try:
                int(role_id)
            except ValueError:
                await safe_send(message, content="⚠️ Role ID must be numeric.")
                return
            
            # Validate emoji (Discord emoji format check)
            if len(emoji) == 0:
                await safe_send(message, content="⚠️ Please provide a valid emoji.")
                return
            
            role = message.guild.get_role(int(role_id))
            if not role:
                await safe_send(message, content="⚠️ Role not found. Please provide a valid role ID.")
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
                    # Check if this emoji/role combination already exists
                    existing_role = next(
                        (role_item for role_item in message_entry["roles"]
                        if role_item["emoji"] == emoji),
                        None
                    )
                    
                    if existing_role:
                        # Update existing emoji with new role
                        existing_role["roleID"] = role_id
                    else:
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

                await safe_send(message,
                    f"✅ Reaction role set up successfully for message ID {message_id} "
                    f"with emoji {emoji} and role ID {role_id}."
                )
                logging.info(
                    f"✅ Reaction role set up successfully for message ID {message_id} "
                    f"with emoji {emoji} and role ID {role_id} by {message.author} "
                    f"in server {guild_id}"
                )

            except discord.NotFound:
                await safe_send(message, content="❌ Message not found. Please provide a valid message ID in the current channel.")
                logging.error("Message not found for reaction role setup.")
            except discord.Forbidden:
                await safe_send(message, content="⚠️ I don't have permission to add reactions. Check my permissions.")
                logging.warning("Permission denied for adding reaction.")
            except Exception as e:
                await safe_send(message, content="An error occurred while setting up the reaction role.")
                logging.error(f"Error setting up reaction role: {e}")
        else:
            await send_permission_denied(message, "set up reaction roles")
            logging.warning(f"Permission denied for reaction role command by {message.author}.")