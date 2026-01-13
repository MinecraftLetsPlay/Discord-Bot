import discord
import asyncio
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv
import os

# Load environment variables (searches current dir and parent dirs)
load_dotenv()

log = logging.getLogger(__name__)

class BroadcastSender:
    # Send broadcast messages to Discord channels
    
    def __init__(self, token: Optional[str] = None):
        # Initialize sender with Discord bot token
        self.token: str = token or os.getenv('DISCORD_BOT_TOKEN') or ""
        
        if not self.token:
            raise ValueError(
                "DISCORD_BOT_TOKEN not found in environment!\n"
                "Ensure your .env file has: DISCORD_BOT_TOKEN=your_token_here"
            )
        
        # Validate token format (Discord tokens are usually 70+ chars)
        if len(self.token.strip()) < 50:
            raise ValueError(
                f"Token appears invalid (too short: {len(self.token)} chars)\n"
                "Make sure you copied the full token correctly"
            )
        
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.client = discord.Client(intents=self.intents)
        
        self.results = {
            "success": [],
            "failed": [],
            "skipped": []
        }
        
        log.info("BroadcastSender initialized")
    
    async def send_broadcasts(self, targets: List[Dict], message: str) -> Dict:
        # Send the broadcast message to all target channels
        async with self.client:
            try:
                # Start the bot in background task
                bot_task = asyncio.create_task(self.client.start(self.token))
                
                # Wait for bot to be ready (with timeout)
                try:
                    await asyncio.wait_for(self.client.wait_until_ready(), timeout=30.0)
                except asyncio.TimeoutError:
                    # Cancel the bot task on timeout
                    bot_task.cancel()
                    try:
                        await bot_task
                    except asyncio.CancelledError:
                        pass
                    
                    log.error("Discord bot failed to connect within 30 seconds")
                    print("❌ ERROR: Discord bot failed to connect!")
                    print("   Possible causes:")
                    print("   • Invalid DISCORD_BOT_TOKEN")
                    print("   • Bot not invited to the servers")
                    print("   • Network connection issues")
                    print("   • Discord API issues")
                    
                    for target in targets:
                        self.results["failed"].append({
                            "guild_id": target['guild_id'],
                            "channel_id": target['channel_id'],
                            "error": "Connection timeout (30s)"
                        })
                    return self.results
            
                print(f"\n📤 Starting broadcast to {len(targets)} channels...\n")
                log.info(f"Starting broadcast to {len(targets)} targets")
                
                # Send messages while bot is connected
                for i, target in enumerate(targets, 1):
                    guild_id = target['guild_id']
                    channel_id = target['channel_id']
                    
                    await self._send_to_channel(guild_id, channel_id, message, i, len(targets))
                    
                    # Small delay between sends (rate limiting)
                    await asyncio.sleep(0.5)
                
                # Close bot connection
                bot_task.cancel()
                try:
                    await bot_task
                except asyncio.CancelledError:
                    pass
                    
            except Exception as e:
                log.error(f"Failed during broadcast: {e}", exc_info=True)
                print(f"❌ ERROR: {e}")
                
                # Mark all targets as failed
                for target in targets:
                    self.results["failed"].append({
                        "guild_id": target['guild_id'],
                        "channel_id": target['channel_id'],
                        "error": str(e)
                    })
        return self.results
    
    async def _send_to_channel(self, guild_id: int, channel_id: int, message: str, current: int, total: int) -> bool:
        # Send message to a specific channel, handle errors
        try:
            channel = self.client.get_channel(channel_id)
            
            if not channel:
                log.warning(f"Channel {channel_id} not found or inaccessible (Guild: {guild_id})")
                self.results["skipped"].append({
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "reason": "Channel not found"
                })
                print(f"[{current}/{total}] ⏭️  Guild {guild_id}: Channel not found")
                return False
            
            if not isinstance(channel, discord.TextChannel):
                log.warning(f"Channel {channel_id} is not a text channel (Guild: {guild_id})")
                self.results["skipped"].append({
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "reason": "Not a text channel"
                })
                print(f"[{current}/{total}] ⏭️  Guild {guild_id}: Not a text channel")
                return False
            
            # Check permissions - get guild member to verify permissions
            guild = self.client.get_guild(guild_id)
            if not guild:
                log.warning(f"Guild {guild_id} not found or bot not a member")
                self.results["skipped"].append({
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "reason": "Guild not accessible"
                })
                print(f"[{current}/{total}] 🚫 Guild {guild_id}: Guild not accessible")
                return False
            
            # Get bot member to check permissions
            bot_member = guild.get_member(self.client.user.id) if self.client.user else None
            if not bot_member:
                log.warning(f"Bot not a member of guild {guild_id}")
                self.results["skipped"].append({
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "reason": "Bot not a guild member"
                })
                print(f"[{current}/{total}] 🚫 Guild {guild_id}: Bot not a guild member")
                return False
            
            # Check if bot has send permission
            if not channel.permissions_for(bot_member).send_messages:
                log.warning(f"No permission to send in channel {channel_id} (Guild: {guild_id})")
                self.results["skipped"].append({
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "reason": "No send permissions"
                })
                print(f"[{current}/{total}] 🚫 Guild {guild_id}: No send permissions")
                return False
            
            # Send message with embed for better formatting
            embed = discord.Embed(
                title="📢 Bot Update",
                description=message,
                color=discord.Color.blue()
            )
            embed.set_footer(text="MCLP Bot • Automated maintainer announcement")
            
            await channel.send(embed=embed)
            
            self.results["success"].append({
                "guild_id": guild_id,
                "channel_id": channel_id
            })
            print(f"[{current}/{total}] ✅ Guild {guild_id}: Message sent")
            log.info(f"Broadcast sent to guild {guild_id}, channel {channel_id}")
            return True
        
        except discord.Forbidden:
            log.error(f"Permission denied for channel {channel_id} (Guild: {guild_id})")
            self.results["failed"].append({
                "guild_id": guild_id,
                "channel_id": channel_id,
                "error": "Permission denied"
            })
            print(f"[{current}/{total}] ❌ Guild {guild_id}: Permission denied")
            return False
        
        except discord.HTTPException as e:
            log.error(f"HTTP error sending to channel {channel_id} (Guild: {guild_id}): {e}")
            self.results["failed"].append({
                "guild_id": guild_id,
                "channel_id": channel_id,
                "error": str(e)
            })
            print(f"[{current}/{total}] ❌ Guild {guild_id}: HTTP error")
            return False
        
        except Exception as e:
            log.error(f"Unexpected error sending to channel {channel_id} (Guild: {guild_id}): {e}")
            self.results["failed"].append({
                "guild_id": guild_id,
                "channel_id": channel_id,
                "error": str(e)
            })
            print(f"[{current}/{total}] ❌ Guild {guild_id}: Error")
            return False
    
    def print_summary(self):
        # Print a summary of the broadcast results
        success = len(self.results["success"])
        failed = len(self.results["failed"])
        skipped = len(self.results["skipped"])
        total = success + failed + skipped
        
        print("\n" + "="*60)
        print("📊 BROADCAST SUMMARY")
        print("="*60)
        print(f"✅ Successful:  {success}/{total}")
        print(f"❌ Failed:      {failed}/{total}")
        print(f"⏭️  Skipped:     {skipped}/{total}")
        print("="*60)
        
        if failed > 0:
            print(f"\n⚠️  Failed channels:")
            for item in self.results["failed"][:10]:
                print(f"   • Guild {item['guild_id']}: {item['error']}")
            if failed > 10:
                print(f"   ... and {failed - 10} more")
        
        if skipped > 0:
            print(f"\n⏭️  Skipped channels:")
            for item in self.results["skipped"][:10]:
                print(f"   • Guild {item['guild_id']}: {item['reason']}")
            if skipped > 10:
                print(f"   ... and {skipped - 10} more")
        
        print()
