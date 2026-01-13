import sys
import logging
import asyncio
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
import os

# Load environment variables (searches current dir and parent dirs)
load_dotenv()

from loader import BroadcastLoader
from confirm import BroadcastConfirmer
from sender import BroadcastSender

# Setup logging with rotation (10 MB per file, keep 5 files)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler with rotation - DEBUG level for detailed logging
file_handler = RotatingFileHandler(
    'broadcast.log',
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5  # Keep 5 backup files
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)  # Detailed logging to file

# Console handler - INFO level for user-friendly output
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)  # Only INFO and above to console

# Configure logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)  # Root logger captures all levels
log.addHandler(file_handler)
log.addHandler(console_handler)

class BroadcastCLI:
    # Main CLI interface for broadcasts
    
    def __init__(self):
        self.loader: Optional[BroadcastLoader] = None
        self.message: Optional[str] = None
        self.targets: List[Dict] = []
    
    def print_header(self):
        # Print welcome header
        print("\n")
        print("╔" + "="*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "  🚀 DISCORD BOT BROADCAST SYSTEM (v1.0)".center(57) + "║")
        print("║" + " "*58 + "║")
        print("╚" + "="*58 + "╝")
        print()
    
    def get_message_input(self) -> str:
        # Let the user input or load the broadcast message
        print("📝 Message Input Options:")
        print("   [1] Type message directly")
        print("   [2] Load from file")
        print()
        
        choice = input("Choose option [1/2]: ").strip()
        
        if choice == "1":
            print("\nEnter your message (type 'END' on a new line to finish):")
            lines = []
            while True:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            
            message = "\n".join(lines).strip()
            if not message:
                print("❌ Message cannot be empty!")
                return self.get_message_input()
            
            return message
        
        elif choice == "2":
            filepath = input("\nEnter file path: ").strip()
            
            try:
                if self.loader is None:
                    raise RuntimeError("Loader not initialized")
                message = self.loader.load_message_from_file(filepath)
                return message
            except Exception as e:
                print(f"❌ Error: {e}")
                return self.get_message_input()
        
        else:
            print("❓ Invalid choice. Please enter 1 or 2.")
            return self.get_message_input()
    
    async def run(self):
        # Main execution flow
        self.print_header()
        
        # Check environment
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token or len(token.strip()) < 50:
            print("❌ DISCORD_BOT_TOKEN not found or invalid in .env file!")
            print()
            print("Steps to fix:")
            print("  1. Open Discord-Bot/.env")
            print("  2. Ensure it contains: DISCORD_BOT_TOKEN=your_actual_token_here")
            print("  3. Get token from: https://discord.com/developers/applications")
            print("  4. Click your app → Bot → Reset Token → Copy full token")
            print()
            log.error("DISCORD_BOT_TOKEN not set or invalid")
            return False
        
        # 1. Load configurations
        print("📂 Loading configurations...\n")
        try:
            self.loader = BroadcastLoader()
            log.info("Configurations loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load configurations: {e}")
            log.error(f"Configuration load error: {e}", exc_info=True)
            return False
        
        # Validate config structure
        if not self.loader.validate_config_structure():
            print("❌ Config structure validation failed!")
            return False
        
        # 2. Get broadcast targets
        print("🔍 Scanning servers for broadcast channels...\n")
        self.targets = self.loader.get_broadcast_targets()
        
        if not self.targets:
            print("⚠️  No servers configured with broadcast channels!")
            print("\nTo enable broadcasts in a server, the server admin must:")
            print("   1. Ensure the server config exists at: src/internal/data/servers/{guild_id}.json")
            print("   2. Add this structure to the config file:")
            print("      {")
            print('         "announcements": {')
            print('           "enabled": true,')
            print('           "channel_id": 123456789012345678')
            print("         }")
            print("      }")
            log.warning("No broadcast targets found")
            return False
        
        print(f"✅ Found {len(self.targets)} servers configured for broadcasts\n")
        
        # 3. Get message input
        print("📝 Message Preparation...\n")
        self.message = self.get_message_input()
        
        # 4. Confirm broadcast
        print("\n🔐 Confirmation Required...\n")
        confirmer = BroadcastConfirmer(self.targets, self.message)
        
        if not confirmer.confirm():
            log.warning("Broadcast cancelled by user")
            return False
        
        # 5. Send broadcasts
        print("🚀 Sending broadcasts...\n")
        try:
            sender = BroadcastSender()
            results = await sender.send_broadcasts(self.targets, self.message)
            sender.print_summary()
            
            log.info(f"Broadcast completed: {len(results['success'])} sent, "
                    f"{len(results['failed'])} failed, "
                    f"{len(results['skipped'])} skipped")
            
            return len(results['failed']) == 0 and len(results['skipped']) == 0
        
        except Exception as e:
            print(f"❌ Broadcast failed: {e}")
            log.error(f"Broadcast error: {e}", exc_info=True)
            return False

def main():
    # Entry point for the broadcast system
    try:
        cli = BroadcastCLI()
        success = asyncio.run(cli.run())
        
        if success:
            print("✅ Broadcast system completed successfully!")
            sys.exit(0)
        else:
            print("❌ Broadcast system encountered errors or was cancelled")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n❌ Broadcast cancelled by user")
        log.warning("Broadcast cancelled by user (Ctrl+C)")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        log.critical(f"Critical error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
