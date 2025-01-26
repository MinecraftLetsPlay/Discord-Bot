import random # For generating random numbers

async def handle_command(client, message):
    # Handles user commands
    user_message = message.content.lower()

    username = message.author

    # Use message.author.mention to get the @username ping
    username_mention = message.author.mention  # @username

    #
    #
    # Minigame commands
    #
    #

    # !roll command
    if user_message.startswith('!roll'):
        # Extract the dice roll command or fallback to a default
        try:
            dice_str = user_message.split(' ', 1)[1]  # Get the dice string after "!roll"
            # Parse the dice string (e.g., "1d6")
            count, sides = map(int, dice_str.lower().split('d'))
            if count <= 0 or sides <= 0:
                raise ValueError("Invalid dice format")
            # Roll the dice
            rolls = [random.randint(1, sides) for _ in range(count)]
            total = sum(rolls)
            await message.channel.send(f"🎲 You rolled: {rolls} (Total: {total})")
        except IndexError:
            # No additional argument, fallback to 1d6
            roll = random.randint(1, 6)
            await message.channel.send(f"🎲 You rolled a {roll}!")
        except ValueError:
            await message.channel.send("Invalid dice format. Use `!roll XdY` (e.g., `!roll 2d6`).")

    choices = ["rock", "paper", "scissors"]

    if user_message.startswith('!rps'):
        try:
            user_choice = user_message.split(' ')[1].lower()
            bot_choice = random.choice(choices)

            if user_choice not in choices:
                raise ValueError("Invalid choice")

            if user_choice == bot_choice:
                result = "It's a tie!"
            elif (user_choice == "rock" and bot_choice == "scissors") or (user_choice == "paper" and bot_choice == "rock") or (user_choice == "scissors" and bot_choice == "paper"):
                result = "You win!"
            else:
                result = "Bot wins!"

            await message.channel.send(f"You chose {user_choice}, bot chose {bot_choice}. {result}")
        except IndexError:
            await message.channel.send("Please specify your choice: `rock`, `paper`, or `scissors`. Example: `!rps rock`.")
        except ValueError:
            await message.channel.send("Invalid choice. Please choose `rock`, `paper`, or `scissors`.")

    # Return None for unhandled commands
    return None
