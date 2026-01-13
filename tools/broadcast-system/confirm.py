import logging
from typing import List, Dict

log = logging.getLogger(__name__)


class BroadcastConfirmer:
    # Handle confirmation for broadcast operations
    
    def __init__(self, targets: List[Dict], message: str):
        self.targets = targets
        self.message = message
        self.target_count = len(targets)
    
    def show_preview(self):
        # Show a preview of the broadcast details
        print("\n" + "="*60)
        print("[DRY RUN] BROADCAST PREVIEW")
        print("="*60)
        
        # Show message
        print(f"\n📝 Message ({len(self.message)} characters):\n")
        print("-" * 60)
        print(self.message[:500])  # First 500 chars
        if len(self.message) > 500:
            print(f"... ({len(self.message) - 500} more characters)")
        print("-" * 60)
        
        # Show targets
        print(f"\n📊 Broadcasting to: {self.target_count} channels")
        
        # Count unique guilds
        unique_guilds = len(set(t['guild_id'] for t in self.targets))
        print(f"   Total servers: {unique_guilds}")
        
        # Show sample targets
        print(f"\n📍 Target channels (first 5):")
        for i, target in enumerate(self.targets[:5], 1):
            guild_id = target['guild_id']
            channel_id = target['channel_id']
            print(f"   {i}. Guild {guild_id} → Channel {channel_id}")
        
        if self.target_count > 5:
            print(f"   ... and {self.target_count - 5} more channels")
        
        print("\n" + "="*60)
    
    def confirm(self) -> bool:
        # Request final confirmation from the user
        # Show preview
        self.show_preview()
        
        # Get confirmation
        print("\n⚠️  FINAL CONFIRMATION REQUIRED\n")
        print(f"You are about to send a message to {self.target_count} channels across multiple servers.")
        print("This action cannot be undone.\n")
        
        confirmation = input(f'Type "SEND {self.target_count}" to confirm: ').strip()
        
        if confirmation == f"SEND {self.target_count}":
            print("\n✅ Broadcast confirmed!\n")
            log.info(f"User confirmed broadcast to {self.target_count} channels")
            return True
        else:
            print("\n❌ Confirmation failed. Broadcast cancelled.\n")
            log.warning(f"User failed confirmation. Expected 'SEND {self.target_count}', got '{confirmation}'")
            return False
