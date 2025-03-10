# MCLP Discord Bot

A feature-rich Discord bot built with Discord.py, providing moderation tools, utility commands, minigames, and more. This bot is designed for private server use with sophisticated permission handling and logging capabilities.

## Core Functionality

### Source Files Overview

- `bot.py` - Main bot initialization and event handling
- `main.py` - Entry point and logging configuration
- `console_to_discord.py` - Enables console-to-Discord messaging
- `command_router.py` - Routes commands to appropriate handlers

### Command Modules

- `moderation_commands.py` - Handles user management (kick/ban/timeout)
- `minigames.py` - Implements various games (RPS, Hangman, Quiz)
- `utility_commands.py` - Provides utility features (weather, time, etc.)
- `public_commands.py` - Basic user commands (help, info, etc.)
- `system_commands.py` - Administrative system controls

### Support Modules

- `utils.py` - Helper functions and data management
- `logging_setup.py` - Configures comprehensive logging system

## Features Under Development

- **Translation Service**: Multi-language translation support
- **LaTeX Calculator**: Advanced mathematical calculations
- **Music Bot Features**: Voice channel audio playback and control

## Tech Stack

### Core Technologies

- Python 3.8+
- Discord.py 2.3.2
- PyNaCl (for voice support)
- aiohttp 3.8.5
- python-dotenv 1.0.0

### Development Tools

- JSON for data storage
- Asyncio for asynchronous operations
- Logging system with rotation

## Setup Requirements

See [`requirements.txt`](requirements) for detailed dependencies.

## Contributing

This is a private bot project. While the code is visible for educational purposes, we do not accept direct contributions without prior discussion.

## Authors

- Minecraft Lets Play (@MinecraftLetsPlay)
- olittlefoxE (@olittlefoxE)

## License

Private use only. All rights reserved.
