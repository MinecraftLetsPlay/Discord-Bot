import random

    #
    #
    # Minigames
    #
    #

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

    def rock_paper_scissors(self):
        print("Let's play Rock Paper Scissors!")
        print("Enter your choice (rock/paper/scissors):")
        player_choice = input().lower()

        if player_choice not in ['rock', 'paper', 'scissors']:
            print("Invalid choice. Please choose rock, paper, or scissors.")
            return

        bot_choice = self.bot_choices[0]
        print(f"Bot chose: {bot_choice}")

        if player_choice == bot_choice:
            print("It's a tie!")
        elif (player_choice == 'rock' and bot_choice == 'scissors') or \
             (player_choice == 'paper' and bot_choice == 'rock') or \
             (player_choice == 'scissors' and bot_choice == 'paper'):
            print("You win!")
        else:
            print("Bot wins!")

    def guess_the_number(self):
        print("I'm thinking of a number between 1 and 100.")
        secret_number = random.randint(1, 100)
        attempts = 0

        while True:
            print("Enter your guess:")
            try:
                guess = int(input())
            except ValueError:
                print("Please enter a valid number.")
                continue

            attempts += 1

            if guess < secret_number:
                print("Too low!")
            elif guess > secret_number:
                print("Too high!")
            else:
                print(f"Congratulations! You guessed the number in {attempts} attempts!")
                break

    def hangman(self):
        words = ['python', 'programming', 'computer', 'algorithm', 'database']
        word = random.choice(words)
        word_letters = set(word)
        alphabet = set('abcdefghijklmnopqrstuvwxyz')
        used_letters = set()

        lives = 6

        while len(word_letters) > 0 and lives > 0:
            print('You have', lives, 'lives left and you have used these letters: ', ' '.join(used_letters))

            word_list = [letter if letter in used_letters else '-' for letter in word]
            print('Current word: ', ' '.join(word_list))

            user_letter = input('Guess a letter: ').lower()
            if user_letter in alphabet - used_letters:
                used_letters.add(user_letter)
                if user_letter in word_letters:
                    word_letters.remove(user_letter)
                else:
                    lives = lives - 1
                    print('\nYour letter,', user_letter, 'is not in the word.')
            elif user_letter in used_letters:
                print('\nYou have already used that letter. Please try again.')
            else:
                print('\nInvalid character. Please try again.')

        if lives == 0:
            print('Sorry, you died. The word was', word)
        else:
            print('Congratulations! You guessed the word', word, '!!')

    def play(self, game_name):
        if game_name in self.games:
            self.games[game_name]()
        else:
            print(f"Game '{game_name}' not found.")
