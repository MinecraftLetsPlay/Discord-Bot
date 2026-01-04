import discord
import random
import asyncio
import aiohttp
import logging
import string
from internal.utils import load_hangman, load_quiz  # Utils functions for loading data
from internal import rate_limiter

# Copyright (c) 2026 Dennis Plischke.
# All rights reserved.

# ================================================================
# Module: Minigames.py
# Description: Contains the code for the minigames like hangman
# Error handling for game logic and API requests included
# ================================================================

# ----------------------------------------------------------------
# Game Configuration Constants
# ----------------------------------------------------------------

# API and Network Timeouts
API_TIMEOUT = 5.0  # API request timeout in seconds
REACTION_TIMEOUT = 60.0  # Timeout for reaction-based games (RPS, Hangman)
GUESS_TIMEOUT = 30.0  # Timeout for text input in guess game
QUIZ_CHOICE_TIMEOUT = 30.0  # Timeout for quiz choice selection
QUIZ_TEXT_TIMEOUT = 40.0  # Timeout for text-based quiz answers

# Game Mechanics
GUESS_MAX_TRIES = 7  # Maximum attempts in guess the number game
GUESS_MAX_NUMBER = 100  # Maximum number in guess the number game

# ----------------------------------------------------------------
# Component test function for [Minigames]
# ----------------------------------------------------------------

async def component_test():
    status = "🟩"
    messages = ["Minigames commands module loaded."]

    try:
        initialize_game_data()
        if not hangman_data:
            status = "🟧"
            messages.append("Warning: Hangman data missing or empty.")
        else:
            messages.append("Hangman data loaded.")
        if not quiz_data:
            status = "🟧"
            messages.append("Warning: Quiz data missing or empty.")
        else:
            messages.append("Quiz data loaded.")
                
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.dictionaryapi.dev/api/v2/entries/en/example', timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)) as response:
                if response.status == 200:
                    messages.append("Dictionary API reachable.")
                else:
                    status = "🟧"
                    messages.append(f"Dictionary API error: Status {response.status}")
                    
    except Exception as e:
        status = "🟥"
        messages.append(f"Error during data initialization: {e}")
        
    return {"status": status, "msg": " | ".join(messages)}

# ----------------------------------------------------------------
# Helper variables and functions for [Minigames]
# ----------------------------------------------------------------

# Global variables to store game data
hangman_data = None
quiz_data = None
supported_languages = ['En','De'] # Supported languages for scrabble

# Initialize game data / load it from JSON files -> Utils.py
def initialize_game_data():
    global hangman_data, quiz_data
    hangman_data = load_hangman()
    quiz_data = load_quiz()
    
    if not hangman_data:
        logging.error("Failed to load Hangman data.")
    if not quiz_data:
        logging.error("Failed to load Quiz data.")

# Initialize game data when the bot starts
initialize_game_data()

# List to keep track of asked question IDs
asked_questions = []

# get data from hangman.json for hangman game
async def get_hangman_word(difficulty=None):
    global hangman_data
    if not hangman_data:
        logging.error("Hangman data is not loaded.")
        return None, None

    categories = list(hangman_data.keys())
    if not categories:
        logging.error("No categories found in Hangman data.")
        return None, None

    category = random.choice(categories)

    if not difficulty:
        difficulty = random.choice(['easy', 'medium', 'hard'])

    words = hangman_data[category].get(difficulty, [])
    if not words:
        logging.error(f"No words found for {category}/{difficulty}")
        return None, None

    return random.choice(words), difficulty

# get data from quiz.json for quiz game
async def get_quiz_question(category=None):
    global quiz_data
    if not quiz_data:
        logging.error("Quiz data is not loaded.")
        return None, None

    categories = list(quiz_data.keys())
    if not category or category not in categories:
        category = random.choice(categories)

    # If category is "random", pool from all categories
    if category == "random":
        all_questions = []
        for cat in categories:
            all_questions.extend(quiz_data[cat])
        questions = all_questions
    else:
        questions = quiz_data.get(category, [])

    if not questions:
        logging.error(f"No questions found for category '{category}'.")
        return None, None

    available_questions = [q for q in questions if q['id'] not in asked_questions]

    if not available_questions:
        asked_questions.clear()
        available_questions = questions

    question = random.choice(available_questions)
    asked_questions.append(question['id'])

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
    letters = []
    for _ in range(count):
        if not pool:
            logging.warning("The letter pool is empty. Cannot draw more letters.")
            break
        letter = random.choice(pool)
        pool.remove(letter)
        letters.append(letter)
    if not letters:
        logging.warning("No letters could be drawn because the pool is empty.")
    return letters

# Check if a word is valid using the appropriate dictionary API
async def is_valid_word(word, language):
    if language == "En":
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}"
    elif language == "De":
        url = f"https://api.dictionaryapi.dev/api/v2/entries/de/{word.lower()}"
    else:
        logging.error(f"Unsupported language '{language}' for dictionary lookup.")
        return False

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return True  # Word exists
                elif response.status == 404:
                    return False  # Word does not exist
                else:
                    logging.warning(f"Unexpected response from dictionary API: {response.status}")
                    return False
    except aiohttp.ClientError as e:
        logging.error(f"Error connecting to dictionary API: {e}")
        return False

def check_answer(question, user_answer):
    # If the question has multiple correct answers
    if "answers" in question:
        return any(user_answer.lower() == ans.lower() for ans in question["answers"])
    # If the question has a single correct answer
    return user_answer.lower() == question["answer"].lower()

# Safe Discord Message Sending with Error Handling
async def safe_send(message_obj, content=None, embed=None, view=None):
    try:
        return await message_obj.channel.send(content=content, embed=embed, view=view)
    except discord.Forbidden:
        logging.error(f"Missing permission to send message in {message_obj.channel}")
        return None
    except discord.HTTPException as e:
        logging.error(f"Failed to send message: {e}")
        return None

# ----------------------------------------------------------------
# Main command handler for [Minigames]
# ----------------------------------------------------------------

async def handle_minigames_commands(client, message, user_message):
    
    # ----------------------------------------------------------------
    # Command: !rps
    # Category: Minigames
    # Type: Full Command
    # Description: Start a game of Rock-Paper-Scissors
    # ----------------------------------------------------------------
    
    if user_message == '!rps':
        allowed, error_msg = await rate_limiter.check_command_cooldown('rps')
        if not allowed:
            await safe_send(message, content=error_msg)
            return
        
        rate_limiter.command_cooldown.set_cooldown('rps')
        
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
            timeout=REACTION_TIMEOUT,
            check=lambda reaction, user: user == message.author and str(reaction.emoji) in choices
        )

            bot_choice = random.choice(choices)
            user_choice = str(reaction.emoji)

            result = determine_rps_winner(user_choice, bot_choice)

            result_embed = discord.Embed(title="Result",
                                    description=f"You: {user_choice}\nBot: {bot_choice}\n{result}",
                                    color=0x00ff00)
            await safe_send(message, embed=result_embed)

        except asyncio.TimeoutError:
            await safe_send(message, content="⚠️ Timeout - Game cancelled!")
            logging.warning("Timeout - Game cancelled!")

    # ----------------------------------------------------------------
    # Command: !guess
    # Category: Minigames
    # Type: Full Command
    # Description: Start a number guessing game
    # ----------------------------------------------------------------
    
    if user_message == '!guess':
        allowed, error_msg = await rate_limiter.check_command_cooldown('guess')
        if not allowed:
            await safe_send(message, content=error_msg)
            return
        
        rate_limiter.command_cooldown.set_cooldown('guess')
        
        number = random.randint(1, GUESS_MAX_NUMBER)
        tries = 0
        max_tries = GUESS_MAX_TRIES

        embed = discord.Embed(title="Guess the Number",
                            description="Guess a number between 1 and 100!",
                            color=0x00ff00)
        await safe_send(message, embed=embed)

        while tries < max_tries:
            try:
                guess_message = await client.wait_for(
                    'message',
                    timeout=GUESS_TIMEOUT,
                    check=lambda m: m.author == message.author and m.content.isdigit()
                )

                guess = int(guess_message.content)
                tries += 1

                if guess == number:
                    await safe_send(message, content=f"Correct! The number was {number}. You took {tries} tries!")
                    logging.debug(f"Correct! The number was {number}. User took {tries} tries!")
                    return
                elif guess < number:
                    await safe_send(message, content="Higher!")
                else:
                    await safe_send(message, content="Lower!")

            except asyncio.TimeoutError:
                await safe_send(message, content="⚠️ Timeout - Game cancelled!")
                logging.warning("Timeout - Game cancelled!")
                return

        await safe_send(message, content=f"Game Over! The number was {number}")
        logging.debug(f"Game Over! The number was {number}")

    # ----------------------------------------------------------------
    # Command: !hangman
    # Category: Minigames
    # Type: Full Command
    # Description: Start a game of Hangman with difficulty levels
    # ----------------------------------------------------------------
    
    if user_message == '!hangman':
        allowed, error_msg = await rate_limiter.check_command_cooldown('hangman')
        if not allowed:
            await safe_send(message, content=error_msg)
            return
        
        rate_limiter.command_cooldown.set_cooldown('hangman')
        
        word, difficulty = await get_hangman_word()
        if not word:
            await message.channel.send("❌ Error loading words! Please try again later.")
            logging.error("Error loading words for Hangman!")
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
        await safe_send(message, embed=embed)

        while tries > 0:
            # Display the current word with guessed letters
            display = "".join(letter if letter in guessed else "-" for letter in word)
            status_embed = discord.Embed(
                title="Hangman",
                description=f"Word: {display}\nGuessed Letters: {' '.join(guessed)}\nRemaining tries: {tries}",
                color=0x00ff00
            )
            await safe_send(message, embed=status_embed)

            # Check if the word has been fully guessed
            if display == word:
                await safe_send(message, content="🎉 You win! The word has been guessed!")
                logging.debug("Hangman: The word has been guessed!")
                return

            # Wait for the user's letter guess
            try:
                guess_message = await client.wait_for(
                    'message',
                    timeout=REACTION_TIMEOUT,
                    check=lambda m: m.author == message.author and len(m.content) == 1
                )

                letter = guess_message.content.lower()

                if letter in guessed:
                    await safe_send(message, content="ℹ️ You've already guessed this letter! Please try another one.")
                    continue

                if letter not in alphabet:
                    await safe_send(message, content="ℹ️ Invalid character. Please guess a letter (a-z).")
                    continue

                guessed.add(letter)

                if letter not in word:
                    tries -= 1
                    await safe_send(message, content=f"❌ Your letter, '{letter}', is not in the word.")
                    if tries == 0:
                        await safe_send(message, content=f"💀 Game Over! The word was: {word}")
                        logging.debug(f"Hangman: Game Over! The word was: {word}")
                        return

            except asyncio.TimeoutError:
                await safe_send(message, content="⚠️ Timeout - Game cancelled!")
                logging.warning("Hangman: Timeout - Game cancelled!")
                return

    # ----------------------------------------------------------------------------
    # !quiz command
    # Category: Minigames
    # Type: Full Command
    # Description: Start a quiz with customizable category and number of questions
    # ----------------------------------------------------------------------------
    
    if user_message.startswith('!quiz'):
        allowed, error_msg = await rate_limiter.check_command_cooldown('quiz')
        if not allowed:
            await safe_send(message, content=error_msg)
            return
        
        rate_limiter.command_cooldown.set_cooldown('quiz')
        
        # E.g.!quiz programming 10
        parts = user_message.split()
        if len(parts) < 3:
            await safe_send(message, content="ℹ️ Usage: `!quiz <category> <number_of_questions>` (e.g., `!quiz programming 10`)")
            return

        category = parts[1]
        
        # Validate and parse quiz_size
        try:
            quiz_size = int(parts[2])
        except ValueError:
            await safe_send(message, content="⚠️ Number of questions must be a valid number.")
            logging.warning(f"Invalid quiz_size input: {parts[2]}")
            return
        
        # Validate quiz_size range (1-20 questions)
        if quiz_size < 1 or quiz_size > 20:
            await safe_send(message, content="⚠️ Please specify between 1 and 20 questions.")
            return

        score = 0

        for idx in range(quiz_size):
            question_data, actual_category = await get_quiz_question(category)
            if not question_data:
                await safe_send(message, content="⚠️ No more questions available or error loading questions. Please try again later.")
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
                    reaction, user = await client.wait_for('reaction_add', timeout=QUIZ_CHOICE_TIMEOUT, check=check)
                    user_answer = option_letters[emoji_map.index(str(reaction.emoji))]
                    if user_answer == question_data["correct"]:
                        await safe_send(message, content="✅ Correct!")
                        score += 1
                    else:
                        await safe_send(message, content=f"❌ Wrong! The right answer was: {question_data['correct']}")
                except asyncio.TimeoutError:
                    await safe_send(message, content=f"⚠️ Timeout - The right answer was: {question_data['correct']}")
            else:
                # open text question
                embed = discord.Embed(
                    title=f"Frage {idx+1}/{quiz_size}",
                    description=question_data['question'],
                    color=0x00ff00
                )
                await safe_send(message, embed=embed)
                try:
                    answer_message = await client.wait_for(
                        'message',
                        timeout=QUIZ_TEXT_TIMEOUT,
                        check=lambda m: m.author == message.author
                    )
                    # Compare the answer
                    if answer_message.content.strip().lower() == question_data.get("answer", "").strip().lower():
                        await safe_send(message, content="✅ Right!")
                        score += 1
                    else:
                        await safe_send(message, content=f"❌ Wrong! The right answer was: {question_data.get('answer', 'unbekannt')}")
                except asyncio.TimeoutError:
                    await safe_send(message, content=f"⚠️ Timeout - The right answer was: {question_data['answer']}")

        await safe_send(message, content=f"Quiz finished! You scored {score}/{quiz_size}.")

    # ----------------------------------------------------------------
    # !roll command
    # Category: Minigames
    # Type: Full Command
    # Description: Roll dice with customizable number and sides
    # ----------------------------------------------------------------
    
    if user_message.startswith('!roll'):
        allowed, error_msg = await rate_limiter.check_command_cooldown('roll')
        if not allowed:
            await safe_send(message, content=error_msg)
            return
        
        rate_limiter.command_cooldown.set_cooldown('roll')
        
        try:
            args = user_message.split()[1:] if len(user_message.split()) > 1 else []

            # Default values
            default_num_dice = 1
            default_num_sides = 6
            valid_sides = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 26, 28, 30, 36, 48, 50, 60, 100]

            # Parse arguments
            for arg in args:
                if arg.startswith('d'):
                    try:
                        default_num_dice = int(arg[1:])
                        if not 1 <= default_num_dice <= 10:
                            await safe_send(message, content="ℹ️ You can only roll between 1 and 10 dice at a time!")
                            return
                    except ValueError:
                        await safe_send(message, content=f"⚠️ Invalid dice count: '{arg[1:]}' is not a number.")
                        logging.warning(f"Invalid dice format: {arg}")
                        return
                elif arg.startswith('s'):
                    try:
                        default_num_sides = int(arg[1:])
                        if default_num_sides not in valid_sides:
                            await safe_send(message, content=f"ℹ️ Invalid number of sides! Available: {', '.join(map(str, valid_sides))}")
                            return
                    except ValueError:
                        await safe_send(message, content=f"⚠️ Invalid sides count: '{arg[1:]}' is not a number.")
                        logging.warning(f"Invalid sides format: {arg}")
                        return

            # Roll dice
            rolls = [random.randint(1, default_num_sides) for _ in range(default_num_dice)]
            total = sum(rolls)

            # Create embed
            embed = discord.Embed(
                title="🎲 Dice Roll",
                description=f"Arguments: d{default_num_dice} s{default_num_sides}",
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
                logging.debug(f"Dice roll: {default_num_dice}d{default_num_sides}, Rolls: {roll_str}, Total: {total}, Average: {avg:.2f}")
            else:
                logging.debug(f"Dice roll: {default_num_dice}d{default_num_sides}, Rolls: {roll_str}, Total: {total}")

            await safe_send(message, embed=embed)

        except (ValueError, IndexError):
            await safe_send(message, content="ℹ️ Invalid format! Example: !roll d3 s20 (3 dice with 20 sides each)")
            logging.warning("Invalid format for dice roll command!")