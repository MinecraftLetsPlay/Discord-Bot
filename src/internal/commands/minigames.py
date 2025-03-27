import discord
import random
import asyncio
import logging
from internal.utils import load_hangman, load_quiz  # Aktualisierte Importe

# Globale Variablen für Spielressourcen
hangman_data = None
quiz_data = None

# Überprüfen, ob die Daten erfolgreich geladen werden können
def initialize_game_data():
    global hangman_data, quiz_data
    hangman_data = load_hangman()
    quiz_data = load_quiz()

    if not hangman_data:
        logging.error("❌ Failed to load Hangman data.")
    if not quiz_data:
        logging.error("❌ Failed to load Quiz data.")

# Initialisiere die Daten beim Laden des Moduls
initialize_game_data()

# List to keep track of asked question IDs
asked_questions = []

# ----------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------

# get data from hangman.json for hangman game
async def get_hangman_word(difficulty=None):
    global hangman_data
    if not hangman_data:
        logging.error("❌ Hangman data is not loaded.")
        return None, None

    categories = list(hangman_data.keys())
    if not categories:
        logging.error("❌ No categories found in Hangman data.")
        return None, None

    category = random.choice(categories)

    if not difficulty:
        difficulty = random.choice(['easy', 'medium', 'hard'])

    words = hangman_data[category].get(difficulty, [])
    if not words:
        logging.error(f"❌ No words found for {category}/{difficulty}")
        return None, None

    return random.choice(words), difficulty

# get data from quiz.json for quiz game
async def get_quiz_question(category=None):
    global quiz_data
    if not quiz_data:
        logging.error("❌ Quiz data is not loaded.")
        return None, None

    categories = list(quiz_data.keys())
    if not category or category not in categories:
        category = random.choice(categories)

    questions = quiz_data.get(category, [])
    if not questions:
        logging.error(f"❌ No questions found for category '{category}'.")
        return None, None

    # Filter out questions that have already been asked
    available_questions = [q for q in questions if q['id'] not in asked_questions]

    if not available_questions:
        # If all questions have been asked, reset the list and start over
        asked_questions.clear()
        available_questions = questions

    # Select a random question from the available ones
    question = random.choice(available_questions)
    asked_questions.append(question['id'])

    # Debugging: Print the list of asked question IDs
    logging.debug(f"Asked questions: {asked_questions}")

    return question, category

# Determine the winner of a rock-paper-scissors game
def determine_rps_winner(user_choice: str, bot_choice: str) -> str:
    if user_choice == bot_choice:
        return "It's a tie!"
    elif ((user_choice == '🪨' and bot_choice == '✂️') or
          (user_choice == '📄' and bot_choice == '🪨') or
          (user_choice == '✂️' and bot_choice == '📄')):
        return "You win!"
    else:
        return "Bot wins!"


# ----------------------------------------------------------------
# Main command handler
# ----------------------------------------------------------------
async def handle_minigames_commands(client, message, user_message):

    # !rps command
    if user_message == '!rps':
        choices = ['🪨', '📄', '✂️']
        embed = discord.Embed(title="Rock Paper Scissors",
                            description="Choose: 🪨, 📄, or ✂️",
                            color=0x00ff00)
        game_message = await message.channel.send(embed=embed)

        for choice in choices:
            await game_message.add_reaction(choice)

        try:
            reaction, user = await client.wait_for(
            'reaction_add',
            timeout=60.0,
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
            await message.channel.send("⚠️ Timeout - Game cancelled!")
            logging.warning("⚠️ Timeout - Game cancelled!")

    # !guess command
    if user_message == '!guess':
        number = random.randint(1, 100)
        tries = 0
        max_tries = 7

        embed = discord.Embed(title="Guess the Number",
                            description="Guess a number between 1 and 100!",
                            color=0x00ff00)
        await message.channel.send(embed=embed)

        while tries < max_tries:
            try:
                guess_message = await client.wait_for(
                    'message',
                    timeout=30.0,
                    check=lambda m: m.author == message.author and m.content.isdigit()
                )

                guess = int(guess_message.content)
                tries += 1

                if guess == number:
                    await message.channel.send(f"Correct! The number was {number}. You took {tries} tries!")
                    logging.info(f"Correct! The number was {number}. User took {tries} tries!")
                    return
                elif guess < number:
                    await message.channel.send("Higher!")
                else:
                    await message.channel.send("Lower!")

            except asyncio.TimeoutError:
                await message.channel.send("⚠️ Timeout - Game cancelled!")
                logging.warning("⚠️ Timeout - Game cancelled!")
                return

        await message.channel.send(f"Game Over! The number was {number}")
        logging.info(f"Game Over! The number was {number}")

    # !hangman command
    if user_message == '!hangman':
        word, difficulty = await get_hangman_word()
        if not word:
            await message.channel.send("❌ Error loading words! Please try again later.")
            logging.error("❌ Error loading words for Hangman!")
            return

        guessed = set()
        alphabet = set('abcdefghijklmnopqrstuvwxyz')

        # Set tries based on difficulty
        if difficulty == 'easy':
            tries = 6
        elif difficulty == 'medium':
            tries = 10
        else:  # hard
            tries = 16

        # Initial display with hyphens
        word_length = "-" * len(word)
        embed = discord.Embed(
            title="Hangman",
            description=f"Guess the word! (Difficulty: {difficulty})\nWord: {word_length}\nOne letter per message.",
            color=0x00ff00
        )
        embed.add_field(name="Word length", value=f"{len(word)} letters", inline=False)
        embed.add_field(name="Remaining tries", value=str(tries), inline=False)
        await message.channel.send(embed=embed)

        while tries > 0:
            # Display the current word with guessed letters
            display = "".join(letter if letter in guessed else "-" for letter in word)
            status_embed = discord.Embed(
                title="Hangman",
                description=f"Word: {display}\nGuessed Letters: {' '.join(guessed)}\nRemaining tries: {tries}",
                color=0x00ff00
            )
            await message.channel.send(embed=status_embed)

            if display == word:  # Check if the word has been fully guessed
                await message.channel.send("🎉 You win! The word has been guessed!")
                logging.info("🎉 Hangman: The word has been guessed!")
                return

            try:
                guess_message = await client.wait_for(
                    'message',
                    timeout=60.0,
                    check=lambda m: m.author == message.author and len(m.content) == 1
                )

                letter = guess_message.content.lower()

                if letter in guessed:
                    await message.channel.send("ℹ️ You've already guessed this letter! Please try another one.")
                    continue

                if letter not in alphabet:
                    await message.channel.send("ℹ️ Invalid character. Please guess a letter (a-z).")
                    continue

                guessed.add(letter)

                if letter not in word:
                    tries -= 1
                    await message.channel.send(f"❌ Your letter, '{letter}', is not in the word.")
                    if tries == 0:
                        await message.channel.send(f"💀 Game Over! The word was: {word}")
                        logging.info(f"💀 Hangman: Game Over! The word was: {word}")
                        return

            except asyncio.TimeoutError:
                await message.channel.send("⚠️ Timeout - Game cancelled!")
                logging.warning("⚠️ Hangman: Timeout - Game cancelled!")
                return

    # !quiz command
    if user_message.startswith('!quiz'):
        parts = user_message.split()
        if len(parts) != 3 or not parts[2].isdigit():
            await message.channel.send("ℹ️ Please use the format: `!quiz <category> <number of questions>`")
            return

        category = parts[1]
        quiz_size = int(parts[2])

        if quiz_size not in [10, 20, 30]:
            await message.channel.send("ℹ️ Invalid quiz size. Please choose 10, 20, or 30 questions.")
            return

        score = 0

        for idx in range(1, quiz_size + 1):
            question_data, actual_category = await get_quiz_question(category)
            if not question_data:
                await message.channel.send(f"❌ Error loading quiz questions for category '{category}'!")
                logging.error(f"❌ Error loading quiz questions for category '{category}'!")
                return

            embed = discord.Embed(
                title=f"Quiz - {actual_category}",
                description=f"Question {idx}/{quiz_size}: {question_data['question']}",
                color=0x00ff00
            )
            await message.channel.send(embed=embed)

            try:
                answer_message = await client.wait_for(
                    'message',
                    timeout=90.0,
                    check=lambda m: m.author == message.author
                )

                # Check if the user wants to end the quiz
                if answer_message.content.lower() == '!quiz end':
                    await message.channel.send(f"Quiz ended early. You scored {score}/{quiz_size}.")
                    return

                if answer_message.content.lower() == question_data["answer"].lower():
                    await message.channel.send("✅ Correct!")
                    score += 1
                else:
                    await message.channel.send(f"❌ Incorrect! The correct answer was: {question_data['answer']}")

            except asyncio.TimeoutError:
                await message.channel.send("⚠️ Timeout - Moving to the next question!")
                logging.warning("⚠️ Quiz: Timeout - Moving to the next question!")

        await message.channel.send(f"🎉 Quiz complete! You scored {score}/{quiz_size}.")

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
                        await message.channel.send("ℹ️ You can only roll between 1 and 10 dice at a time!")
                        return
                elif arg.startswith('s'):
                    default_num_sides = int(arg[1:])
                    if default_num_sides not in valid_sides:
                        await message.channel.send(f"ℹ️ Invalid number of sides! Available: {', '.join(map(str, valid_sides))}")
                        return

            # Roll dice
            rolls = [random.randint(1, default_num_sides) for _ in range(default_num_dice)]
            total = sum(rolls)

            # Create embed
            embed = discord.Embed(
                title="🎲 Dice Roll",
                description=f"Arguments: {default_num_dice}d{default_num_sides}",
                color=0x00ff00
            )

            # Add roll results
            roll_str = ", ".join(str(r) for r in rolls)
            embed.add_field(
                name="Rolls",
                value=roll_str,
                inline=False
            )

            # Add total
            embed.add_field(
                name="Total",
                value=str(total),
                inline=False
            )

            # Add average if multiple dice
            if default_num_dice > 1:
                avg = total / default_num_dice
                embed.add_field(
                    name="Average",
                    value=f"{avg:.2f}",
                    inline=False
                )
                logging.info(f"Dice roll: {default_num_dice}d{default_num_sides}, Rolls: {roll_str}, Total: {total}, Average: {avg:.2f}")
            else:
                logging.info(f"Dice roll: {default_num_dice}d{default_num_sides}, Rolls: {roll_str}, Total: {total}")

            await message.channel.send(embed=embed)

        except (ValueError, IndexError):
            await message.channel.send("ℹ️ Invalid format! Example: !roll d3 s20 (3 dice with 20 sides each)")
            logging.warning("ℹ️ Invalid format for dice roll command!")
