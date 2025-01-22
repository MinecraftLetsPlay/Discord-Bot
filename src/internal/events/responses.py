# src/internal/events/responses.py
async def on_message(client, message, responses, commands, sys, os):
    if message.author == client.user:
        return

    username = str(message.author)
    user_message = str(message.content)
    channel = str(message.channel)

    print(f'{username} said: "{user_message}" ({channel})')

    if user_message.lower() == '!shutdown':
        await commands.system.shutdown(client, message)

    elif user_message.lower() == '!restart':
        await commands.system.restart(client, message, sys, os)

    elif user_message.lower() == '!info':
        await commands.general.info(client, message)

    elif user_message.lower() == '!ping':
        await commands.general.ping(client, message)

    else:
        response = responses.get_response(user_message)
        if response:
            print(f'{client.user} said: "{response.title}" ({channel})')
            await message.channel.send(embed=response)
