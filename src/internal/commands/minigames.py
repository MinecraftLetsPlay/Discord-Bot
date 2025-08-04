import discord
import random
import asyncio
import aiohttp
import logging
import string
from internal.utils import load_hangman, load_quiz, load_scrabble  # Utils functions for loading data

# Global variables to store game data
hangman_data = None
quiz_data = None
scrabble_data = {}
supported_languages = ['En', 'De'] # Supported languages for scrabble

# Initialize game data / load it from JSON files -> Utils.py
def initialize_game_data():
    global hangman_data, quiz_data, scrabble_data
    hangman_data = load_hangman()
    quiz_data = load_quiz()
    
    if not hangman_data:
        logging.error("❌ Failed to load Hangman data.")
    if not quiz_data:
        logging.error("❌ Failed to load Quiz data.")
    
    for lang in supported_languages:
        scrabble_data[lang] = load_scrabble(lang)  # Load Scrabble data for each supported language
        if not scrabble_data[lang]:  # Check if data is loaded successfully
            logging.error(f"❌ Failed to load Scrabble data for {lang}.")
            scrabble_data[lang] = {}  # Set empty data if loading failed
            logging.debug(f"Loaded Scrabble data for {lang}: {scrabble_data[lang]}")

# Initialize game data when the bot starts
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

# Draw a specified number of letters from the pool
def draw_letters(pool, count):
    """Draws a specified number of letters from the pool."""
    letters = []
    for _ in range(count):
        if not pool:
            logging.warning("⚠️ The letter pool is empty. Cannot draw more letters.")
            break
        letter = random.choice(pool)
        pool.remove(letter)
        letters.append(letter)
    if not letters:
        logging.warning("⚠️ No letters could be drawn because the pool is empty.")
    return letters

# Calculate the score of a word based on letter values
def calculate_word_score(word, scrabble_data):
    """Calculates the score of a word based on letter values."""
    score = 0
    for letter in word.upper():
        if letter in scrabble_data:
            score += scrabble_data[letter]["value"]
        else:
            logging.warning(f"⚠️ Letter '{letter}' is not in the Scrabble data. Ignoring it.")
    return score

# Check if a word is valid using the appropriate dictionary API
async def is_valid_word(word, language):
    """Checks if a word exists using the appropriate dictionary API."""
    if language == "En":
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}"
    elif language == "De":
        url = f"https://api.dictionaryapi.dev/api/v2/entries/de/{word.lower()}"
    else:
        logging.error(f"❌ Unsupported language '{language}' for dictionary lookup.")
        return False

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return True  # Word exists
                elif response.status == 404:
                    return False  # Word does not exist
                else:
                    logging.warning(f"⚠️ Unexpected response from dictionary API: {response.status}")
                    return False
    except aiohttp.ClientError as e:
        logging.error(f"❌ Error connecting to dictionary API: {e}")
        return False

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
        # E.g.!quiz programming 10
        parts = user_message.split()
        if len(parts) < 3:
            await message.channel.send("Please specify a category and the number of questions (e.g., `!quiz programming 10`).")
            return

        category = parts[1]
        quiz_size = int(parts[2])

        score = 0

        for idx in range(quiz_size):
            question_data, actual_category = await get_quiz_question(category)
            if not question_data:
                await message.channel.send("⚠️ No more questions available or error loading questions. Please try again later.")
                break

            # Multiple-Choice question
            if "options" in question_data:
                options = question_data["options"]
                option_letters = list(string.ascii_uppercase)[:len(options)]
                description = "\n".join([f":regional_indicator_{l.lower()}: {o}" for l, o in zip(option_letters, options)])

                embed = discord.Embed(
                    title=f"Frage {idx+1}/{quiz_size}",
                    description=f"{question_data['question']}\n\n{description}",
                    color=0x00ff00
                )
                quiz_msg = await message.channel.send(embed=embed)

                # Add reactions for options
                emoji_map = [chr(0x1F1E6 + i) for i in range(len(options))]  # 🇦, 🇧, 🇨, ...
                for emoji in emoji_map:
                    await quiz_msg.add_reaction(emoji)

                def check(reaction, user):
                    return (
                        user == message.author and
                        reaction.message.id == quiz_msg.id and
                        str(reaction.emoji) in emoji_map
                    )

                try:
                    reaction, user = await client.wait_for('reaction_add', timeout=30.0, check=check)
                    user_answer = option_letters[emoji_map.index(str(reaction.emoji))]
                    if user_answer == question_data["correct"]:
                        await message.channel.send("✅ Correct!")
                        score += 1
                    else:
                        await message.channel.send(f"❌ Wrong! The right answer was: {question_data['correct']}")
                except asyncio.TimeoutError:
                    await message.channel.send(f"⚠️ Timeout - Game cancelled! The right answer was: {question_data['correct']}")
            else:
                # open text question
                embed = discord.Embed(
                    title=f"Frage {idx+1}/{quiz_size}",
                    description=question_data['question'],
                    color=0x00ff00
                )
                await message.channel.send(embed=embed)
                try:
                    answer_message = await client.wait_for(
                        'message',
                        timeout=30.0,
                        check=lambda m: m.author == message.author
                    )
                    # Compare the answer
                    if answer_message.content.strip().lower() == question_data.get("answer", "").strip().lower():
                        await message.channel.send("✅ Right!")
                        score += 1
                    else:
                        await message.channel.send(f"❌ Wrong! The right answer was: {question_data.get('answer', 'unbekannt')}")
                except asyncio.TimeoutError:
                    await message.channel.send("⚠️ Timeout - Game cancelled!")

        await message.channel.send(f"Quiz finished! You scored {score}/{quiz_size}.")

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

    # !scrabble command
    if user_message.startswith('!scrabble'):
        # Start a new game
        if user_message.startswith('!scrabble start'):
            parts = user_message.split()
            if len(parts) < 2:
                await message.channel.send("❌ Please specify a language (e.g., `!scrabble start En`) and mention at least 2 players.")
                return

            language = parts[2].capitalize() if len(parts) > 2 else "En"
            if language not in supported_languages:
                await message.channel.send(f"❌ Unsupported language '{language}'. Supported languages: {', '.join(supported_languages)}.")
                return
            
            # Load Scrabble data for the specified language
            scrabble_data = load_scrabble(language)
            if not scrabble_data:
                await message.channel.send(f"❌ Failed to load Scrabble data for language '{language}'.")
                return

            players = [message.author.id]
            for user in message.mentions:
                if user.id not in players:
                    players.append(user.id)

            # Initialize the game
            letter_pool = []
            for letter, data in scrabble_data.items():  # Entferne [language], da scrabble_data bereits die Daten enthält
                letter_pool.extend([letter] * data["count"])
            random.shuffle(letter_pool)

            game_state = {
                "players": players,
                "hands": {player: draw_letters(letter_pool, 7) for player in players},
                "scores": {player: 0 for player in players},
                "current_player": players[0],
                "letter_pool": letter_pool,
                "language": language
            }
            client.scrabble_game = game_state

            await message.channel.send(f"🎮 Scrabble game started in {language}!")
            for player in players:
                hand = " ".join(game_state["hands"][player])
                await message.channel.send(f"<@{player}>, your letters: {hand}")
            return

        # Play a word
        if user_message.startswith('!scrabble play'):
            if not hasattr(client, 'scrabble_game'):
                await message.channel.send("❌ No Scrabble game is currently running!")
                return

            game = client.scrabble_game
            if message.author.id != game["current_player"]:
                await message.channel.send("❌ It's not your turn!")
                return

            try:
                word_message = await client.wait_for(
                    'message',
                    timeout=60.0,
                    check=lambda m: m.author == message.author
                )
                word = word_message.content.strip().upper()
            except asyncio.TimeoutError:
                await message.channel.send(f"⏳ {message.author.mention} took too long! Skipping their turn.")
                game["current_player"] = game["players"][(game["players"].index(message.author.id) + 1) % len(game["players"])]
                return

            if not word:
                await message.channel.send("❌ You must play a word! Please try again.")
                return

            if len(word) > len(game["hands"][message.author.id]):
                await message.channel.send(f"❌ Your word '{word}' is too long for your current hand: {' '.join(game['hands'][message.author.id])}.")
                return

            if not set(word).issubset(set(game["hands"][message.author.id])):
                await message.channel.send(f"❌ You don't have all the required letters to play '{word}'. Your hand: {' '.join(game['hands'][message.author.id])}.")
                return

            if not await is_valid_word(word, game["language"]):
                await message.channel.send(f"❌ '{word}' is not a valid word in {game['language']}!")
                return

            # Hole die Scrabble-Daten für die aktuelle Sprache
            scrabble_data = load_scrabble(game["language"])
            score = calculate_word_score(word, scrabble_data)
            game["scores"][message.author.id] += score
            for letter in word:
                game["hands"][message.author.id].remove(letter)
            game["hands"][message.author.id] += draw_letters(game["letter_pool"], len(word))
            game["current_player"] = game["players"][(game["players"].index(message.author.id) + 1) % len(game["players"])]

            await message.channel.send(f"✅ {word} was played! You earned {score} points. 🎉")

            # Zeige jedem Spieler seine neuen Buchstaben
            for player in game["players"]:
                user = await client.fetch_user(player)
                hand = " ".join(game["hands"][player])
                await user.send(f"🎮 Your letters: {hand}")

            # Prüfe, ob das Spiel zu Ende ist
            if not game["letter_pool"] and all(not hand for hand in game["hands"].values()):
                results = "\n".join([f"<@{player}>: {score} points" for player, score in game["scores"].items()])
                await message.channel.send(f"🏁 Scrabble game ended automatically!\n📊 Results:\n{results}")
                del client.scrabble_game
            return