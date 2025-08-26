# MCLP Discord Bot

A feature-rich Discord bot built with Discord.py, providing moderation tools, utility commands, minigames, and more. This bot is designed for private server use with sophisticated permission handling and logging capabilities.

## Core Functionality

### Source Files Overview

- `bot.py` - Main bot initialization and event handling (Core functionality)
- `main.py` - Entry point and logging configuration (Main entry point)
- `console_to_discord.py` - Enables console-to-Discord messaging
- `command_router.py` - Routes commands to appropriate handlers

### Command Modules

- `moderation_commands.py` - Handles user management (kick/ban/timeout)
- `minigames.py` - Implements various games (RPS, Hangman, Quiz)
- `utility_commands.py` - Provides utility features (weather, time, etc.)
- `public_commands.py` - Basic user commands (help, info, etc.)
- `system_commands.py` - Administrative system controls
- `calculator.py` - Provides extensive calculator functionality
- `mcserver_commands.py` - Provides Minecraft-Server control functionality (Nitrado API)

### Support Modules

- `utils.py` - Helper functions and data management
- `logging_setup.py` - Configures comprehensive logging system and log-file handler

## Features Under Development

- **Music Bot Features**: Voice channel audio - YTMusic

## Tech Stack

### Core Technologies

- Python 3.11.4 - Python enviroment
- Discord.py 2.4.0 - Discord API Wrapper
- PyNaCl 1.5.0 (for voice support)
- aiohttp 3.11.11 - Websocket connection
- python-dotenv 1.0.1 - Enviroment files
- sympy 1.12 - Advanced calc. functionality

### Development Tools

- JSON for data storage
- Asyncio for asynchronous operations
- Logging system with rotation

## Setup Requirements

See [`requirements`](./requirements.txt) for detailed dependencies.

## Contributing

This is a private bot project. While the code is visible for educational purposes, we do not accept direct contributions without prior discussion.
Sharing or using this sourcecode is prohibited without permission.

## Authors

- Minecraft Lets Play (@MinecraftLetsPlay) => Dennis Plischke
- Jirasrel (@Jirasrel)

## License

Copyright © 2025 Dennis Plischke

Private use only. All rights reserved.

