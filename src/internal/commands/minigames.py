import random
import discord
import asyncio
import json
from internal import utils

def load_config():
        try:
            with open('quiz.json', 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading config file: {e}")
            return {}

class Minigames:
    def __init__(self):
        self._bot_choices = ['rock', 'paper', 'scissors']
        random.shuffle(self._bot_choices)  # Shuffle once during initialization
        self.games = {
            "rps": self.rock_paper_scissors,
            "guess": self.guess_the_number,
            "hangman": self.hangman,
            "quiz": self.quiz
        }

    @property
    def bot_choices(self):
        return self._bot_choices

    @bot_choices.setter
    def bot_choices(self, value):
        self._bot_choices = value

    async def wait_for_message(self, client, message, check_func, timeout=30.0):
        try:
            user_message = await client.wait_for('message', check=check_func, timeout=timeout)
            return user_message.content
        except asyncio.TimeoutError:
            await message.channel.send("You took too long to respond.")
            return None

    async def rock_paper_scissors(self, message, client):
        await message.channel.send("Let's play Rock Paper Scissors! Enter your choice (rock/paper/scissors):")
        def check(msg):
            return msg.author == message.author and msg.content.lower() in ['rock', 'paper', 'scissors']
        
        player_choice = await self.wait_for_message(client, message, check)
        if player_choice is None:
            return

        bot_choice = self.bot_choices[0]
        await message.channel.send(f"Bot chose: {bot_choice}")

        if player_choice == bot_choice:
            await message.channel.send("It's a tie!")
        elif (player_choice == 'rock' and bot_choice == 'scissors') or \
             (player_choice == 'paper' and bot_choice == 'rock') or \
             (player_choice == 'scissors' and bot_choice == 'paper'):
            await message.channel.send("You win!")
        else:
            await message.channel.send("Bot wins!")

    async def guess_the_number(self, message, client):
        await message.channel.send("I'm thinking of a number. Enter the range (e.g., 1-100):")
    
        def range_check(msg):
            return msg.author == message.author and '-' in msg.content and \
               all(part.strip().isdigit() for part in msg.content.split('-'))
    
        range_message = await self.wait_for_message(client, message, range_check)
        if range_message is None:
            return
    
        try:
            low, high = map(int, range_message.split('-'))
            if low >= high:
                await message.channel.send("Invalid range! Please ensure the lower bound is less than the upper bound.")
                return
        except ValueError:
            await message.channel.send("Invalid range format. Please use the format: 1-100.")
            return
    
        secret_number = random.randint(low, high)
        attempts = 0

        async def guess_check(msg):
            return msg.author == message.author and msg.content.isdigit()

        while True:
            await message.channel.send("Enter your guess:")
            guess_message = await self.wait_for_message(client, message, guess_check)
            if guess_message is None:
                return
        
            guess = int(guess_message)
            attempts += 1

            if guess < secret_number:
                await message.channel.send("Too low! Try again.")
            elif guess > secret_number:
                await message.channel.send("Too high! Try again.")
            else:
                await message.channel.send(f"Congratulations! You guessed the number {secret_number} in {attempts} attempts!")
                break

    async def hangman(self, message, client):
        words = ['python', 'programming', 'computer', 'algorithm', 'database']
        word = random.choice(words)
        word_letters = set(word)
        alphabet = set('abcdefghijklmnopqrstuvwxyz')
        used_letters = set()

        lives = 6

        while len(word_letters) > 0 and lives > 0:
            await message.channel.send(f'You have {lives} lives left and you have used these letters: {", ".join(used_letters)}')
            word_list = [letter if letter in used_letters else '-' for letter in word]
            await message.channel.send(f'Current word: {" ".join(word_list)}')

            def check(msg):
                return msg.author == message.author and len(msg.content) == 1 and msg.content.isalpha()

            await message.channel.send('Guess a letter:')
            user_letter = await self.wait_for_message(client, message, check)
            if user_letter is None:
                return

            if user_letter in alphabet - used_letters:
                used_letters.add(user_letter)
                if user_letter in word_letters:
                    word_letters.remove(user_letter)
                else:
                    lives -= 1
                    await message.channel.send(f'Your letter, {user_letter}, is not in the word.')
            elif user_letter in used_letters:
                await message.channel.send('You have already used that letter. Please try again.')
            else:
                await message.channel.send('Invalid character. Please try again.')

        if lives == 0:
            await message.channel.send(f'Sorry, you lost. The word was {word}.')
        else:
            await message.channel.send(f'Congratulations! You guessed the word {word}!!')

    async def play(self, game_name, client, message, category=None):
        if game_name == "quiz":
            if category:
                await self.quiz(message, client, category)
            else:
                # No category provided, show available categories
                quiz_data = utils.load_quiz()
                if quiz_data:
                    available_categories = ", ".join(quiz_data.keys())
                    await message.channel.send(f"Please specify a category for the quiz. Available categories: {available_categories}")
                    await message.channel.send("Available quiz sizes: 10, 20, 30.")
                else:
                    await message.channel.send("Quiz data could not be loaded.")
        elif game_name in self.games:
            await self.games[game_name](message, client)
        else:
            available_games = ', '.join(self.games.keys())
            await message.channel.send(f"Game '{game_name}' not found. Available games are: {available_games}.")
            
    async def quiz(self, message, client, category):
        # Load quiz data using the dedicated function
        quiz_data = utils.load_quiz()

        if not quiz_data:
            await message.channel.send("Quiz data could not be loaded.")
            return

        # Get questions and shuffle them
        questions = quiz_data[category]
        random.shuffle(questions)

        # Ensure we don't ask more questions than available
        quiz_size = 10  # default quiz size
        selected_questions = questions[:quiz_size]

        score = 0

        # Loop through the selected questions
        for idx, question in enumerate(selected_questions, 1):
            await message.channel.send(f"Question {idx}/{quiz_size}: {question['question']}")

            def check(msg):
                return msg.author == message.author

            try:
                # Wait for the user's response
                answer_message = await client.wait_for('message', check=check, timeout=30.0)
                if answer_message.content.lower() == question['answer'].lower():
                    await message.channel.send("Correct!")
                    score += 1
                else:
                    await message.channel.send(f"Wrong! The correct answer was: {question['answer']}")
            except Exception:
                await message.channel.send("You took too long to respond!")

        # Show the final score
        await message.channel.send(f"Quiz complete! You scored {score}/{quiz_size}.")
        