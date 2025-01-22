# src/internal/bot.py
import discord
import os
import sys
from internal import events, utils, responses, commands
from internal.commands import general, system


def run_discord_bot():
    config = utils.load_config()
    TOKEN = config['token']

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
        await events.on_message(client, message, responses, sys, os)

    client.run(TOKEN)
