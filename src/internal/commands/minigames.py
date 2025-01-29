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
        return "Unentschieden!"
    elif ((user_choice == '🪨' and bot_choice == '✂️') or
          (user_choice == '📄' and bot_choice == '🪨') or
          (user_choice == '✂️' and bot_choice == '📄')):
        return "Du gewinnst!"
    else:
        return "Bot gewinnt!"

async def handle_minigames_commands(client, message, user_message):
    # !rps command
    if user_message == '!rps':
        choices = ['🪨', '📄', '✂️']
        embed = discord.Embed(title="Rock Paper Scissors",
                            description="Wähle: 🪨, 📄 oder ✂️",
                            color=0x00ff00)
        game_message = await message.channel.send(embed=embed)

        for choice in choices:
            await game_message.add_reaction(choice)

        try:
            reaction, user = await message.guild.wait_for(
                'reaction_add',
                timeout=30.0,
                check=lambda reaction, user: user == message.author and str(reaction.emoji) in choices
            )

            bot_choice = random.choice(choices)
            user_choice = str(reaction.emoji)

            result = determine_rps_winner(user_choice, bot_choice)

            result_embed = discord.Embed(title="Ergebnis",
                                    description=f"Du: {user_choice}\nBot: {bot_choice}\n{result}",
                                    color=0x00ff00)
            await message.channel.send(embed=result_embed)

        except asyncio.TimeoutError:
            await message.channel.send("Zeitüberschreitung - Spiel abgebrochen!")

    # !guess command
    if user_message == '!guess':
        number = random.randint(1, 100)
        tries = 0
        max_tries = 7

        embed = discord.Embed(title="Zahlenraten",
                            description="Rate eine Zahl zwischen 1 und 100!",
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
                    await message.channel.send(f"Richtig! Die Zahl war {number}. Du hast {tries} Versuche gebraucht!")
                    return
                elif guess < number:
                    await message.channel.send("Höher!")
                else:
                    await message.channel.send("Niedriger!")

            except asyncio.TimeoutError:
                await message.channel.send("Zeitüberschreitung - Spiel abgebrochen!")
                return

        await message.channel.send(f"Game Over! Die Zahl war {number}")

    # !hangman command
    if user_message == '!hangman':
        word, difficulty = await get_hangman_word()
        if not word:
            await message.channel.send("Fehler beim Laden der Wörter!")
            return

        guessed = set()
        tries = 6

        embed = discord.Embed(title="Hangman",
                            description=f"Rate das Wort! (Schwierigkeit: {difficulty})\nEin Buchstabe pro Nachricht.",
                            color=0x00ff00)
        await message.channel.send(embed=embed)

        while tries > 0:
            display = "".join(letter if letter in guessed else "_" for letter in word)
            status_embed = discord.Embed(title="Hangman",
                                    description=f"Wort: {display}\nVerbleibende Versuche: {tries}",
                                    color=0x00ff00)
            await message.channel.send(embed=status_embed)

            if "_" not in display:
                await message.channel.send("Gewonnen! Das Wort wurde erraten!")
                return

            try:
                guess_message = await message.guild.wait_for(
                    'message',
                    timeout=30.0,
                    check=lambda m: m.author == message.author and len(m.content) == 1
                )

                letter = guess_message.content.lower()

                if letter in guessed:
                    await message.channel.send("Diesen Buchstaben hast du bereits geraten!")
                    continue

                guessed.add(letter)

                if letter not in word:
                    tries -= 1
                    if tries == 0:
                        await message.channel.send(f"Game Over! Das Wort war: {word}")
                        return

            except asyncio.TimeoutError:
                await message.channel.send("Zeitüberschreitung - Spiel abgebrochen!")
                return

    # !quiz command
    if user_message == '!quiz':
        question_data, category = await get_quiz_question()
        if not question_data:
            await message.channel.send("Fehler beim Laden der Quiz-Fragen!")
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
                await message.channel.send("Richtig!")
            else:
                await message.channel.send(f"Falsch! Die richtige Antwort war: {question_data['answer']}")

        except asyncio.TimeoutError:
            await message.channel.send("Zeitüberschreitung - Quiz beendet!")

    # !roll command
    if user_message.startswith('!roll'):
        try:
            args = user_message.split()[1:] if len(user_message.split()) > 1 else ['s6']
            results = []
            total = 0
            valid_sides = [4, 6, 8, 10, 12, 20, 100]

            for arg in args:
                # Parse argument (e.g., "3s6" or "s20")
                count = 1
                if arg[0].isdigit():
                    count = int(arg[0])
                    sides = int(arg[2:])
                else:
                    sides = int(arg[1:])

                if sides not in valid_sides:
                    await message.channel.send(f"Ungültiger Würfel d{sides}! Verfügbar: d4, d6, d8, d10, d12, d20, d100")
                    return

                # Roll dice
                rolls = [random.randint(1, sides) for _ in range(count)]
                results.append((sides, rolls))
                total += sum(rolls)

            # Create embed
            embed = discord.Embed(title="🎲 Würfelwurf", color=0x00ff00)

            # Add results for each dice type
            for sides, rolls in results:
                roll_str = ", ".join(str(r) for r in rolls)
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
