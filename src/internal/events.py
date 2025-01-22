async def on_ready(client):
    print(f'{client.user} is now running!')

async def on_message(client, message, responses, sys, os):
    if message.author == client.user:
        return

    username = str(message.author)
    user_message = str(message.content)
    channel = str(message.channel)

    print(f'{username} said: "{user_message}" ({channel})')

    if user_message.lower() == '!shutdown':
        await message.channel.send("Shutting down...")
        await client.close()

    elif user_message.lower() == '!restart':
        await message.channel.send("Restarting...")
        os.execv(sys.executable, ['python'] + sys.argv)

    else:
        response = responses.get_response(user_message)
        if response:
            print(f'{client.user} said: "{response}" ({channel})')
            await message.channel.send(response)
