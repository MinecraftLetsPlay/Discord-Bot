import random
import discord
import asyncio

class Minigames:
    def __init__(self):
        self.games = {
            "rps": self.rock_paper_scissors,
            "guess": self.guess_the_number,
            "hangman": self.hangman
        }
        self.bot_choices = ['rock', 'paper', 'scissors']

    @property
    def bot_choices(self):
        random.shuffle(self._bot_choices)
        return self._bot_choices

    @bot_choices.setter
    def bot_choices(self, value):
        self._bot_choices = value

    async def rock_paper_scissors(self, message, client):
        await message.channel.send("Let's play Rock Paper Scissors!")
        await message.channel.send("Enter your choice (rock/paper/scissors):")
        
        def check(msg):
            return msg.author == message.author and msg.content.lower() in ['rock', 'paper', 'scissors']
        
        try:
            player_message = await client.wait_for('message', check=check, timeout=30.0)
            player_choice = player_message.content.lower()
        except asyncio.TimeoutError:
            await message.channel.send("You took too long to respond.")
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
        await message.channel.send("I'm thinking of a number between 1 and 100.")
        secret_number = random.randint(1, 100)
        attempts = 0

        while True:
            await message.channel.send("Enter your guess:")
            
            def check(msg):
                return msg.author == message.author and msg.content.isdigit()
            
            try:
                guess_message = await client.wait_for('message', check=check, timeout=30.0)
                guess = int(guess_message.content)
            except asyncio.TimeoutError:
                await message.channel.send("You took too long to respond.")
                return
            except ValueError:
                await message.channel.send("Please enter a valid number.")
                continue

            attempts += 1

            if guess < secret_number:
                await message.channel.send("Too low!")
            elif guess > secret_number:
                await message.channel.send("Too high!")
            else:
                await message.channel.send(f"Congratulations! You guessed the number in {attempts} attempts!")
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
            try:
                user_message = await client.wait_for('message', check=check, timeout=30.0)
                user_letter = user_message.content.lower()
            except asyncio.TimeoutError:
                await message.channel.send("You took too long to respond.")
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

    async def play(self, game_name, client, message):
        if game_name in self.games:
            await self.games[game_name](message, client)
        else:
            await message.channel.send(f"Game '{game_name}' not found.")

# Handler for minigames commands
async def handle_minigames(client, message, user_message):
    minigames = Minigames()

    if user_message.startswith('!rps'):
        await minigames.play("rps", client, message)

    elif user_message.startswith('!guess'):
        await minigames.play("guess", client, message)

    elif user_message.startswith('!hangman'):
        await minigames.play("hangman", client, message)
