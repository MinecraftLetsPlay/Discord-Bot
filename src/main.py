import bot as bot
import logging
import sys
import asyncio
import aiohttp

# Configure logging to handle Unicode characters
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

async def cleanup():
    # Cleanup sessions
    for task in asyncio.all_tasks():
        if not task.done():
            task.cancel()
    await asyncio.sleep(0.25)

# Main entry point
if __name__ == '__main__':
    try:
        bot.run_discord_bot()
    except KeyboardInterrupt:
        asyncio.run(cleanup())
    except Exception as e:
        logging.error(f"Unerwarteter Fehler: {e}")
        asyncio.run(cleanup())