import discord
import random
import asyncio
from internal import utils

async def get_hangman_word(difficulty=None):
    hangman_data = utils.load_hangman()
    if not difficulty:
        difficulty = random.choice(['easy', 'medium', 'hard'])

    words = hangman_data.get('words', {}).get(difficulty, [])
    if not words:
        return None, None

    return random.choice(words), difficulty

async def get_quiz_question(category=None):
    quiz_data = utils.load_quiz()
    if not quiz_data:
        return None, None

    categories = list(quiz_data.keys())
    if not category or category not in categories:
        category = random.choice(categories)

    questions = quiz_data.get(category, [])
    if not questions:
        return None, None

    return random.choice(questions), category

def determine_rps_winner(user_choice: str, bot_choice: str) -> str:
    if user_choice == bot_choice:
        return "Draw!"
    elif ((user_choice == '🪨' and bot_choice == '✂️') or
          (user_choice == '📄' and bot_choice == '🪨') or
          (user_choice == '✂️' and bot_choice == '📄')):
        return "You win!"
    else:
        return "Bot wins!"

async def handle_minigames_commands(client, message, user_message):
    # !rps command
    if user_message == '!rps':
        choices = ['🪨', '📄', '✂️']
        embed = discord.Embed(title="Rock Paper Scissors",
                            description="Choose: 🪨, 📄 oder ✂️",
                            color=0x00ff00)
        game_message = await message.channel.send(embed=embed)

        for choice in choices:
            await game_message.add_reaction(choice)

        try:
            reaction, user = await client.wait_for(
            'reaction_add',
            timeout=30.0,
            check=lambda reaction, user: user == message.author and str(reaction.emoji) in choices
        )

            bot_choice = random.choice(choices)
            user_choice = str(reaction.emoji)

            result = determine_rps_winner(user_choice, bot_choice)

            result_embed = discord.Embed(title="Result",
                                    description=f"You: {user_choice}\nBot: {bot_choice}\n{result}",
                                    color=0x00ff00)
            await message.channel.send(embed=result_embed)

        except asyncio.TimeoutError:
            await message.channel.send("Timeout - Game cancelled!")

    # !guess command
    if user_message == '!guess':
        number = random.randint(1, 100)
        tries = 0
        max_tries = 7

        embed = discord.Embed(title="Number-guessing",
                            description="Guess a number between 1 and 100!",
                            color=0x00ff00)
        await message.channel.send(embed=embed)

        while tries < max_tries:
            try:
                guess_message = await message.guild.wait_for(
                    'message',
                    timeout=30.0,
                    check=lambda m: m.author == message.author and m.content.isdigit()
                )

                guess = int(guess_message.content)
                tries += 1

                if guess == number:
                    await message.channel.send(f"Right! The number was {number}. You needed {tries} tries!")
                    return
                elif guess < number:
                    await message.channel.send("Higher!")
                else:
                    await message.channel.send("Lower!")

            except asyncio.TimeoutError:
                await message.channel.send("Timeout - Game cancelled!")
                return

        await message.channel.send(f"Game Over! The number was {number}")

    # !hangman command
    if user_message == '!hangman':
        word, difficulty = await get_hangman_word()
        if not word:
            await message.channel.send("Error loading hangman words!")
            return

        guessed = set()
        tries = 6

        embed = discord.Embed(title="Hangman",
                            description=f"Guess the word (Difficulty: {difficulty})\nOne letter per message.",
                            color=0x00ff00)
        await message.channel.send(embed=embed)

        while tries > 0:
            display = "".join(letter if letter in guessed else "_" for letter in word)
            status_embed = discord.Embed(title="Hangman",
                                    description=f"Word: {display}\nRemaining tries: {tries}",
                                    color=0x00ff00)
            await message.channel.send(embed=status_embed)

            if "_" not in display:
                await message.channel.send("Won! The word has been guessed!")
                return

            try:
                guess_message = await message.guild.wait_for(
                    'message',
                    timeout=30.0,
                    check=lambda m: m.author == message.author and len(m.content) == 1
                )

                letter = guess_message.content.lower()

                if letter in guessed:
                    await message.channel.send("You already tried this letter!")
                    continue

                guessed.add(letter)

                if letter not in word:
                    tries -= 1
                    if tries == 0:
                        await message.channel.send(f"Game Over! The word was: {word}")
                        return

            except asyncio.TimeoutError:
                await message.channel.send("Timeout - Game cancelled!")
                return

    # !quiz command
    if user_message == '!quiz':
        question_data, category = await get_quiz_question()
        if not question_data:
            await message.channel.send("Error loading quiz-questions!")
            return

        embed = discord.Embed(title=f"Quiz - {category}",
                            description=question_data["question"],
                            color=0x00ff00)
        await message.channel.send(embed=embed)

        try:
            answer_message = await message.guild.wait_for(
                'message',
                timeout=30.0,
                check=lambda m: m.author == message.author
            )

            if answer_message.content.lower() == question_data["answer"].lower():
                await message.channel.send("Right!")
            else:
                await message.channel.send(f"Wrong! The right answer was: {question_data['answer']}")

        except asyncio.TimeoutError:
            await message.channel.send("Timeout - Game cancelled!")

    # !roll command
    if user_message.startswith('!roll'):
        try:
            args = user_message.split()[1:] if len(user_message.split()) > 1 else []

            # Default values
            default_num_dice = 1
            default_num_sides = 6
            valid_sides = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 26, 28, 30, 36, 48, 50, 60, 100]

            # Parse arguments
            for arg in args:
                if arg.startswith('d'):
                    default_num_dice = int(arg[1:])
                    if not 1 <= default_num_dice <= 10:
                        await message.channel.send("Du kannst nur 1-100 Würfel gleichzeitig würfeln!")
                        return
                elif arg.startswith('s'):
                    default_num_sides = int(arg[1:])
                    if default_num_sides not in valid_sides:
                        await message.channel.send(f"Ungültige Seitenzahl! Verfügbar: {', '.join(map(str, valid_sides))}")
                        return

            # Roll dice
            rolls = [random.randint(1, default_num_sides) for _ in range(default_num_dice)]
            total = sum(rolls)

            # Create embed
            embed = discord.Embed(title="🎲 Würfelwurf", color=0x00ff00)

            # Add roll results
            roll_str = ", ".join(str(r) for r in rolls)
            embed.add_field(
                name="Würfe",
                value=roll_str,
                inline=False
            )

            # Add total
            embed.add_field(
                name="Summe",
                value=str(total),
                inline=False
            )

            # Add average if multiple dice
            if default_num_dice > 1:
                avg = total / default_num_dice
                embed.add_field(
                    name=f"d{sides} ({len(rolls)}x)",
                    value=f"Würfe: {roll_str}\nSumme: {sum(rolls)}",
                    inline=False
                )

            # Add total if multiple dice were rolled
            if len(results) > 1:
                embed.add_field(name="Gesamt", value=str(total), inline=False)

            await message.channel.send(embed=embed)

        except (ValueError, IndexError):
            await message.channel.send("Ungültiges Format! Beispiele: !roll s20, !roll 3s6, !roll s20 s8")
