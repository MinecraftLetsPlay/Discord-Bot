import discord
import logging
import os
import sys
import nacl
import asyncio
import time
from dotenv import load_dotenv
from discord.ext import commands
from internal import utils
from internal import command_router

# ================================================================
# Module: Bot.py
# Description: Main loop and handlers for messages and reactions
# Error Handling: Strategic Try-Catch blocks only where needed
# ================================================================

# ----------------------------------------------------------------
# Bot startup and configuration
# ----------------------------------------------------------------

start = time.perf_counter()

def run_discord_bot():
    
    # Load environment variables
    load_dotenv()

    # Config loading
    try:
        DebugModeActivated = utils.get_config_value("DebugModeActivated", default=False)
        TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    except Exception as e:
        logging.critical(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # CRITICAL: Security Check - MUST NOT BE SKIPPED
    if not TOKEN:
        logging.critical("DISCORD_BOT_TOKEN is missing. Please set it in the .env file.")
        sys.exit(1)

    # Discord Intents
    try:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
    except Exception as e:
        logging.critical(f"Failed to setup Discord intents: {e}")
        sys.exit(1)

    # Bot Creation
    try:
        bot = commands.Bot(command_prefix='!', intents=intents)
    except Exception as e:
        logging.critical(f"Failed to create bot instance: {e}")
        sys.exit(1)
    
    # Component Tests
    async def run_component_tests():
        try:
            print()
            print("──────────────────────────────")
            print(" Startup Component Summary")
            print("──────────────────────────────")
            results = await command_router.component_test()
            
            for name, result in results:
                display_name = name.capitalize()
                status = result.get('status', '🟥')
                msg = result.get('msg', 'Unknown error')
                
                if DebugModeActivated:
                    print(f"Hello from {display_name}:")
                    print(f"  Status: {status} {msg}")
                else:
                    if status in ["🟩", "🟨", "🟧", "🟥"]:
                        print(f"{status} {display_name}" + (f" ({msg})" if status != "🟩" else ""))
            
            print("──────────────────────────────")
            print()
        except Exception as e:
            logging.error(f"Error running component tests: {e}", exc_info=True)
            print("⚠️ Component tests failed\n")
    
    try:
        asyncio.run(run_component_tests())
    except Exception as e:
        logging.error(f"Critical error during component tests: {e}", exc_info=True)

    # ------------------------------------------------------------
    # BOT EVENTS
    # ------------------------------------------------------------

    @bot.event
    async def on_ready():
        try:
            duration = time.perf_counter() - start
            logging.info(f"Bot ready after {duration:.2f} seconds.")
            print()
            logging.info(f'{bot.user} is now running!')
            print()
            logging.info("-" * 26)
            logging.info(f"Python version: {sys.version.split()[0]}")
            logging.info(f"Discord.py version: {discord.__version__}")
            logging.info(f"PyNaCl version: {nacl.__version__}")
            logging.info(f"Application ID: {bot.application_id}")
            logging.info(f"Logging activated: {utils.get_config_value('LoggingActivated', default=True)}")
            logging.info(f"Debug mode activated: {DebugModeActivated}")
            logging.info("-" * 26)
            print()
        except Exception as e:
            logging.error(f"Error logging startup info: {e}")

        # Sync slash commands globally
        try:
            await bot.tree.sync()
            logging.info('Slash commands synchronized globally.')
        except discord.Forbidden:
            logging.error('No permission to sync slash commands globally.')
        except discord.HTTPException as e:
            logging.error(f'Failed to sync slash commands: {e}')

        # Sync commands per guild
        try:
            for guild in bot.guilds:
                try:
                    await bot.tree.sync(guild=discord.Object(id=guild.id))
                except discord.Forbidden:
                    logging.warning(f'No permission to sync commands in guild {guild.name}')
                except discord.HTTPException as e:
                    logging.warning(f'Failed to sync commands in guild {guild.name}: {e}')
            logging.info('Slash commands synchronized per guild.')
        except Exception as e:
            logging.error(f'Error iterating guilds: {e}')

        # Load bot status
        try:
            bot_status = utils.get_config_value("BotStatus", default=None)
            
            if bot_status and isinstance(bot_status, dict) and "type" in bot_status and "text" in bot_status:
                status_type = bot_status["type"].lower()
                status_text = bot_status["text"]
                
                mapping = {
                    "playing": discord.ActivityType.playing,
                    "listening": discord.ActivityType.listening,
                    "watching": discord.ActivityType.watching,
                    "competing": discord.ActivityType.competing
                }
                
                if status_type not in mapping:
                    logging.warning(f"Invalid status type in config: {status_type}")
                else:
                    try:
                        await bot.change_presence(
                            activity=discord.Activity(type=mapping[status_type], name=status_text)
                        )
                        logging.info(f"Bot status set: {status_type} {status_text}")
                    except discord.HTTPException as e:
                        logging.warning(f"Failed to set bot status: {e}")
            else:
                logging.info("No saved bot status found in config.")
        except Exception as e:
            logging.error(f"Error loading bot status: {e}")

    @bot.event
    async def on_message(message):
        # Check to prevent bot responding to itself
        if message.author == bot.user:
            return
        
        # Config loading
        try:
            if message.guild:
                LoggingActivated = utils.get_config_value(
                    "LoggingActivated", 
                    guild_id=message.guild.id, 
                    default=True
                )
                is_logged = utils.is_channel_logged(message.guild.id, message.channel.id)
            else:
                LoggingActivated = utils.get_config_value("LoggingActivated", default=True)
                is_logged = LoggingActivated
        except Exception as e:
            logging.error(f"Error loading server config: {e}")
            LoggingActivated = True
            is_logged = True
        
        # Log user message
        if LoggingActivated and is_logged:
            username = str(message.author)
            user_message = str(message.content)
            if message.guild:
                logging.info(f'{username}: "{user_message}" ({message.guild.name})')
            else:
                logging.info(f'📩 DM from {username}: "{user_message}"')

        # Command handling (send to router)
        try:
            response = await command_router.handle_command(bot, message)
            
            if response is not None:
                if LoggingActivated and is_logged:
                    logging.info(f'Bot replied: "{response}"')
                
                # Send response
                try:
                    await message.channel.send(response)
                except discord.Forbidden:
                    logging.error(f"No permission to send in {message.channel}")
                except discord.HTTPException as e:
                    logging.error(f"Failed to send message: {e}")
        
        except Exception as e:
            logging.error(f"Error handling command: {e}", exc_info=True)
            try:
                await message.channel.send("⚠️ An error occurred. Please try again.")
            except Exception:
                logging.error("Could not send error notification")
            
    # Reaction Role Handler
    async def handle_reaction_role(payload, action):
        try:
            reaction_role_data = utils.load_reaction_role_data()
        except Exception as e:
            logging.error(f"Failed to load reaction role data: {e}")
            return
        
        guild_id = str(payload.guild_id)
        if guild_id not in reaction_role_data:
            logging.debug(f"Guild {guild_id} has no reaction roles")
            return
        
        # Find matching role data
        matching_role = None
        for message_data in reaction_role_data[guild_id]:
            if message_data.get("messageID") == str(payload.message_id):
                for role_data in message_data.get("roles", []):
                    if str(payload.emoji) == role_data.get("emoji"):
                        matching_role = role_data
                        break
                if matching_role:
                    break
        
        if not matching_role:
            logging.debug(f"No matching reaction role for {payload.emoji}")
            return
        
        # Get Discord objects
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            logging.error(f"Guild {guild_id} not found")
            return
        
        role_id = matching_role.get("roleID")
        if not role_id:
            logging.error("Role ID missing in reaction role data")
            return
        
        try:
            role = guild.get_role(int(role_id))
        except (ValueError, TypeError) as e:
            logging.error(f"Invalid role ID format: {role_id}")
            return
        
        if not role:
            logging.error(f"Role {role_id} not found in guild {guild.name}")
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            logging.error(f"Member {payload.user_id} not found in guild {guild.name}")
            return
        
        # Add or remove role (Reactionrole action)
        try:
            if action == "add":
                await member.add_roles(role)
                logging.info(f"Added role {role.name} to {member.name}")
            elif action == "remove":
                await member.remove_roles(role)
                logging.info(f"Removed role {role.name} from {member.name}")
        except discord.Forbidden:
            logging.error(f"No permission to modify roles for {member.name}")
        except discord.HTTPException as e:
            logging.error(f"Failed to modify roles: {e}")
            
    @bot.event
    # Prevent bot reacting to its own reactions
    async def on_raw_reaction_add(payload):
        if bot.user and payload.user_id == bot.user.id:
            return
        await handle_reaction_role(payload, "add")
        
    @bot.event
    # Prevent bot reacting to its own reactions
    async def on_raw_reaction_remove(payload):
        if bot.user and payload.user_id == bot.user.id:
            return
        await handle_reaction_role(payload, "remove")
    
    # Start Bot and test for common startup errors
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        logging.critical("Invalid token. Check DISCORD_BOT_TOKEN.")
        sys.exit(1)
    except discord.PrivilegedIntentsRequired:
        logging.critical("Required intents not enabled in Discord Developer Portal.")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Bot shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Failed to run bot: {e}")
        sys.exit(1)
