# src/internal/bot.py
import discord
import os
import sys
import responses
from internal import events, utils, commands

def run_discord_bot():
    config = utils.load_config()
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')

    if not TOKEN:
        raise ValueError("No DISCORD_BOT_TOKEN found in environment variables")

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        await events.on_ready(client)

    @client.event
    async def on_message(message):
        await events.on_message(client, message, responses, commands, sys, os)

    client.run(TOKEN)
