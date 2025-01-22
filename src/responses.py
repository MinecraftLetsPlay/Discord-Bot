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
        return str(random.randint(1, 6))
    
    if p_message == '!info':
        embed = discord.Embed(title="Info", description="This is a Discord bot created by Minecraft Lets Play.", color=0x00ff00)
        embed.add_field(name="", value="Its purpose is to provide information and entertainment to the community.", inline=False)
        embed.add_field(name="", value="It is currently in development and will be updated regularly.", inline=False)
        return embed

    if p_message == '!ping':
        return str("Pong!")

    embed = discord.Embed(title="Error", description="I do not understand that command.", color=0xff0000)
    return embed
