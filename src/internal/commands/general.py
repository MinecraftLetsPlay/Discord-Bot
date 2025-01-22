# src/internal/commands/general.py
import discord

async def info(client, message) -> None:
    embed = discord.Embed(title="Info", description="This is a Discord bot created for demonstration purposes.", color=0x00ff00)
    await message.channel.send(embed=embed)

async def ping(client, message) -> None:
    embed = discord.Embed(title="Ping", description="Pong!", color=0x00ff00)
    await message.channel.send(embed=embed)
