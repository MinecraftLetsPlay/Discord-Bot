import wavelink
import discord
from discord.ext import commands

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.lavalink_online = False

    # Connect to the Lavalink nodes
    async def cog_load(self): 
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()
        try:
            await wavelink.NodePool.create_node(bot=self.bot,
                                                host='127.0.0.1',
                                                port=2333,
                                                password='youshallnotpass')
            self.bot.lavalink_online = True # Set the Lavalink status to online
        except Exception as e:
            self.bot.lavalink_online = False
            print(f"Failed to connect to Lavalink: {e}")

    # Join a voice channel
    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        """Join a voice channel."""
        if not self.bot.lavalink_online:
            await ctx.send("Lavalink server is offline. Music commands are disabled.")
            return

        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                await ctx.send("You are not in a voice channel and did not specify one.")
                return

        player = self.bot.wavelink.get_player(ctx.guild.id)
        await player.connect(channel.id)
        await ctx.send(f"Connected to {channel.name}")

    # Disconnect from a voice channel
    @commands.command()
    async def disconnect(self, ctx):
        """Disconnect from a voice channel."""
        if not self.bot.lavalink_online:
            await ctx.send("Lavalink server is offline. Music commands are disabled.")
            return

        player = self.bot.wavelink.get_player(ctx.guild.id)
        await player.disconnect()
        await ctx.send("Disconnected.")

    # Play a song with the given search query
    @commands.command()
    async def play(self, ctx, *, search: str):
        """Play a song with the given search query."""
        if not self.bot.lavalink_online:
            await ctx.send("Lavalink server is offline. Music commands are disabled.")
            return

        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            await ctx.invoke(self.join)

        query = f"ytsearch:{search}"
        tracks = await wavelink.YouTubeTrack.search(query=query)
        if not tracks:
            await ctx.send("No tracks found.")
            return

        track = tracks[0]
        await player.play(track)
        await ctx.send(f"Now playing: {track.title}")

    # Stop the current song
    @commands.command()
    async def stop(self, ctx):
        """Stop the current song."""
        if not self.bot.lavalink_online:
            await ctx.send("Lavalink server is offline. Music commands are disabled.")
            return

        player = self.bot.wavelink.get_player(ctx.guild.id)
        await player.stop()
        await ctx.send("Stopped the music.")

    # Skip the current song
    @commands.command()
    async def skip(self, ctx):
        """Skip the current song."""
        if not self.bot.lavalink_online:
            await ctx.send("Lavalink server is offline. Music commands are disabled.")
            return

        player = self.bot.wavelink.get_player(ctx.guild.id)
        await player.stop()
        await ctx.send("Skipped the song.")

    # Show the current queue
    @commands.command()
    async def queue(self, ctx):
        """Show the current queue."""
        if not self.bot.lavalink_online:
            await ctx.send("Lavalink server is offline. Music commands are disabled.")
            return

        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.queue:
            await ctx.send("The queue is empty.")
            return

        queue = "\n".join([track.title for track in player.queue])
        await ctx.send(f"Current queue:\n{queue}")

# Add the MusicBot cog to the bot
def setup(bot):
    bot.add_cog(MusicBot(bot))