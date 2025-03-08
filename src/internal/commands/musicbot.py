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
                    await ctx.send("You are not connected to a voice channel.")
                    return
                channel = ctx.author.voice.channel

            # Check if the bot is already in a voice channel
            if ctx.voice_client:
                if ctx.voice_client.channel.id == channel.id:
                    await ctx.send(f"I am already connected to {channel.name}!")
                    return
                await ctx.voice_client.disconnect()

            # Connect to the voice channel
            await channel.connect(cls=wavelink.Player)
            await ctx.send(f"Connected to {channel.name}!")
            
        except Exception as e:
            logging.error(f"Error connecting to voice channel: {e}")
            await ctx.send(f"❌ Error connecting to voice channel: {e}")

    @commands.command()
    async def disconnect(self, ctx):
        """Disconnect from a voice channel."""
        try:
            await ctx.voice_client.disconnect()
            await ctx.send("Disconnected.")
        except Exception as e:
            await ctx.send(f"Error disconnecting: {str(e)}")
            logging.error(f"Error disconnecting: {e}")

    @commands.command()
    async def play(self, ctx, *, search: str):
        """Play a song with the given search query."""
        if not ctx.voice_client:
            await ctx.invoke(self.join_command)

        try:
            # Temporary message while searching
            searching_msg = await ctx.send("🔍 Searching for track...")

            # Check if it's a Spotify link
            if "spotify.com" in search:
                # Extract track ID from Spotify URL - preserve case sensitivity
                if "/track/" in search:
                    track_id = search.split('/track/')[1].split('?')[0]  # Keine Umwandlung in Kleinbuchstaben
                    search = f"track:{track_id}"
                elif "/playlist/" in search:
                    playlist_id = search.split('/playlist/')[1].split('?')[0]  # Keine Umwandlung in Kleinbuchstaben
                    search = f"playlist:{playlist_id}"
                elif "/album/" in search:
                    album_id = search.split('/album/')[1].split('?')[0]  # Keine Umwandlung in Kleinbuchstaben 
                    search = f"album:{album_id}"
            else:
                # Normal search - hier können wir lowercase benutzen
                search = f"spotify:search:{search.lower()}"

            # Search for the track 
            tracks = await wavelink.Playable.search(search, source="spotify")
            
            if not tracks:
                await searching_msg.edit(content="❌ No tracks found on Spotify.")
                return

            track = tracks[0]
            await ctx.voice_client.play(track)

            # Create a nice embed for the current song
            embed = discord.Embed(
                title="🎵 Now playing (Spotify)",
                description=f"**{track.title}**",
                color=discord.Color.green()
            )
            
            # Add artwork if available
            if hasattr(track, 'artwork') and track.artwork:
                embed.set_thumbnail(url=track.artwork)
            
            # Add metadata
            if hasattr(track, 'author') and track.author:
                embed.add_field(name="Artist", value=track.author, inline=True)
            if hasattr(track, 'length'):
                minutes = int(track.length / 60000)
                seconds = int((track.length / 1000) % 60)
                embed.add_field(name="Duration", value=f"{minutes}:{seconds:02d}", inline=True)
            
            # Delete the search message and send the embed
            await searching_msg.delete()
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ General error: {str(e)}")
            logging.error(f"General error: {e}")

    @commands.command()
    async def stop(self, ctx):
        """Stop the current song."""
        try:
            await ctx.voice_client.stop()
            await ctx.send("Stopped the music.")
        except Exception as e:
            await ctx.send(f"Error stopping track: {str(e)}")
            logging.error(f"Error stopping track: {e}")

    @commands.command()
    async def skip(self, ctx):
        """Skip the current song."""
        try:
            await ctx.voice_client.stop()
            await ctx.send("Skipped the song.")
        except Exception as e:
            await ctx.send(f"Error skipping track: {str(e)}")
            logging.error(f"Error skipping track: {e}")

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