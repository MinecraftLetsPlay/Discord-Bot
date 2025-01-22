import random
import discord

def get_response(message: str) -> discord.Embed:
    p_message = message.lower()

    if p_message == '!help':
        embed = discord.Embed(title="Help", description="Possible Commands", color=0x00ff00)
        embed.add_field(name="[System]", value="!shutdown, !restart", inline=False)
        embed.add_field(name="[Public]", value="!roll, !test, !info, !ping", inline=False)
        return embed

    if p_message == '!test':
        embed = discord.Embed(title="Test", description="Hello! I am online and ready...", color=0x00ff00)
        return embed

    if p_message == '!roll':
        embed = discord.Embed(title="Roll", description=str(random.randint(1, 6)), color=0x00ff00)
        return embed

    if p_message == '!info':
        embed = discord.Embed(title="Info", description="This is a Discord bot created for demonstration purposes.", color=0x00ff00)
        return embed

    if p_message == '!ping':
        embed = discord.Embed(title="Ping", description="Pong!", color=0x00ff00)
        return embed

    embed = discord.Embed(title="Error", description="I do not understand that command.", color=0xff0000)
    return embed
