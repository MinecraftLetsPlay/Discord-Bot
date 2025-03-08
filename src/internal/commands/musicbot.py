import wavelink
import discord
import logging
from discord.ext import commands

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.lavalink_online = False

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting"""
        self.bot.lavalink_online = True
        logging.info(f"✅ Wavelink node is ready!")

    @commands.Cog.listener()
    async def on_wavelink_node_disconnect(self, node: wavelink.Node):
        """Event fired when a node disconnects"""
        self.bot.lavalink_online = False
        logging.warning(f"⚠️ Wavelink node disconnected!")

    @commands.command(name="join")
    async def join_command(self, ctx, *, channel: discord.VoiceChannel = None):
        """Join a voice channel."""
        try:
            if not channel:
                if not ctx.author.voice:
                    await ctx.send("Du bist in keinem Voice-Channel!")
                    return
                channel = ctx.author.voice.channel

            # Prüfe, ob der Bot bereits in einem Voice-Channel ist
            if ctx.voice_client:
                if ctx.voice_client.channel.id == channel.id:
                    await ctx.send(f"Ich bin bereits in {channel.name}!")
                    return
                await ctx.voice_client.disconnect()

            # Verbinde mit dem Voice-Channel
            await channel.connect(cls=wavelink.Player)
            await ctx.send(f"Verbunden mit {channel.name}!")
            
        except Exception as e:
            logging.error(f"Fehler beim Verbinden mit Voice-Channel: {e}")
            await ctx.send(f"❌ Fehler beim Verbinden mit dem Voice-Channel: {str(e)}")

    # Disconnect from a voice channel
    @commands.command()
    async def disconnect(self, ctx):
        """Disconnect from a voice channel."""
        try:
            await ctx.voice_client.disconnect()
            await ctx.send("Disconnected.")
        except Exception as e:
            await ctx.send(f"Error disconnecting: {str(e)}")
            logging.error(f"Error disconnecting: {e}")

    # Play a song with the given search query
    @commands.command()
    async def play(self, ctx, *, search: str):
        """Play a song with the given search query."""
        if not ctx.voice_client:
            await ctx.invoke(self.join)

        try:
            # Search for the track
            tracks = await wavelink.YouTubeTrack.search(query=search)
            if not tracks:
                await ctx.send("No tracks found.")
                return

            track = tracks[0]
            await ctx.voice_client.play(track)
            await ctx.send(f"Now playing: {track.title}")
        except Exception as e:
            await ctx.send(f"Error playing track: {str(e)}")
            logging.error(f"Error playing track: {e}")

    # Stop the current song
    @commands.command()
    async def stop(self, ctx):
        """Stop the current song."""
        try:
            await ctx.voice_client.stop()
            await ctx.send("Stopped the music.")
        except Exception as e:
            await ctx.send(f"Error stopping track: {str(e)}")
            logging.error(f"Error stopping track: {e}")

    # Skip the current song
    @commands.command()
    async def skip(self, ctx):
        """Skip the current song."""
        try:
            await ctx.voice_client.stop()
            await ctx.send("Skipped the song.")
        except Exception as e:
            await ctx.send(f"Error skipping track: {str(e)}")
            logging.error(f"Error skipping track: {e}")

    # Show the current queue
    @commands.command()
    async def queue(self, ctx):
        """Show the current queue."""
        if not ctx.voice_client or not ctx.voice_client.queue:
            await ctx.send("The queue is empty.")
            return

        try:
            queue = "\n".join([track.title for track in ctx.voice_client.queue])
            await ctx.send(f"Current queue:\n{queue}")
        except Exception as e:
            await ctx.send(f"Error displaying queue: {str(e)}")
            logging.error(f"Error displaying queue: {e}")

async def setup(bot):
    """Setup function that is called when loading the cog"""
    try:
        await bot.add_cog(MusicBot(bot))
        logging.info("✅ MusicBot cog loaded successfully")
    except Exception as e:
        logging.error(f"❌ Error loading MusicBot cog: {e}")