async def shutdown(client, message):
    await message.channel.send("Shutting down...")
    await client.close()

async def restart(client, message, sys, os):
    await message.channel.send("Restarting...")
    os.execv(sys.executable, ['python'] + sys.argv)
