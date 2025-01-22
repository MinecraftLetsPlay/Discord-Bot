async def on_ready(client):
    print(f'{client.user} is now running!')

async def on_message(client, message, responses, commands, sys, os):
    if message.author == client.user:
        return

    username = str(message.author)
    user_message = str(message.content)
    channel = str(message.channel)

    print(f'{username} said: "{user_message}" ({channel})')

    if user_message.lower() == '!shutdown':
        await commands.shutdown(client, message)

    elif user_message.lower() == '!restart':
        await commands.restart(client, message, sys, os)

    else:
        response = responses.get_response(user_message)
        if response:
            print(f'{client.user} said: "{response}" ({channel})')
            await message.channel.send(response)
