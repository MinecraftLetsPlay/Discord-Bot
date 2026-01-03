import bot as bot
from internal.command_modules.logging_setup import setup_logging

# Copyright (c) 2026 Dennis Plischke.
# All rights reserved.

# Main entry point
if __name__ == '__main__':
    # Initialize logging first
    logger = setup_logging()
    print()
    logger.info("Logging set up! Starting bot...")
    bot.run_discord_bot()
