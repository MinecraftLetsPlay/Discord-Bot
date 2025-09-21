import bot as bot
from internal.commands.logging_setup import setup_logging

# Main entry point
if __name__ == '__main__':
    # Initialize logging first
    logger = setup_logging()
    print()
    logger.info("Logging set up! Starting bot...")
    bot.run_discord_bot()
