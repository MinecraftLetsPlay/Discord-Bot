import time
import asyncio
import logging
from typing import Dict, Tuple, Optional
from collections import defaultdict
from datetime import datetime, timedelta

# Copyright (c) 2026 Dennis Plischke.
# All rights reserved.

# ================================================================
# Module: Rate_limiter.py
# Description: Centralized rate limiting for API calls and commands
# ================================================================

# ----------------------------------------------------------------
# Component test function for calculator module
# ----------------------------------------------------------------

def component_test():
    status = "🟩"
    messages = ["Rate limiter module loaded."]
    
    return {"status": status, "msg": " | ".join(messages)}

# ----------------------------------------------------------------
# Logger setup & Rate Limiter Classes
# ----------------------------------------------------------------

logger = logging.getLogger(__name__)

class RateLimiter:
    # Token bucket algorithm for API rate limiting
    def __init__(self, max_requests: int, time_window: int):
        # max_requests: Number of allowed requests
        # time_window: Time window in seconds
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, identifier: str) -> Tuple[bool, float]:
        # Returns: (allowed: bool, retry_after: float in seconds)
        now = time.time()

        # Clean old requests outside time window
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if now - req_time < self.time_window
            ]

        # Check if limit exceeded
        if len(self.requests[identifier]) >= self.max_requests:
            oldest_request = self.requests[identifier][0]
            retry_after = self.time_window - (now - oldest_request)
            return False, max(0.1, retry_after)

        # Add current request
        self.requests[identifier].append(now)
        return True, 0.0

    def get_remaining(self, identifier: str) -> int:
        # Get remaining requests for identifier
        now = time.time()
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if now - req_time < self.time_window
            ]
            return max(0, self.max_requests - len(self.requests[identifier]))
        return self.max_requests


class CommandCooldown:
    # Simple per-command global cooldown (not per-user)
    def __init__(self):
        self.last_execution: Dict[str, float] = {}

    def is_on_cooldown(self, command: str, cooldown_seconds: int) -> Tuple[bool, float]:
        # Returns: (on_cooldown: bool, remaining_seconds: float)
        now = time.time()

        if command in self.last_execution:
            elapsed = now - self.last_execution[command]
            if elapsed < cooldown_seconds:
                return True, cooldown_seconds - elapsed

        return False, 0.0

    def set_cooldown(self, command: str):
        # Set cooldown for command
        self.last_execution[command] = time.time()

    def get_remaining(self, command: str, cooldown_seconds: int) -> float:
        # Get remaining cooldown time
        if command not in self.last_execution:
            return 0.0
        elapsed = time.time() - self.last_execution[command]
        return max(0.0, cooldown_seconds - elapsed)


# ----------------------------------------------------------------
# Global API Rate Limiters
# ----------------------------------------------------------------

api_limiter_nasa = RateLimiter(max_requests=5, time_window=60)
api_limiter_openweather = RateLimiter(max_requests=10, time_window=60)
api_limiter_dictionary = RateLimiter(max_requests=20, time_window=60)
api_limiter_catfact = RateLimiter(max_requests=30, time_window=60)
api_limiter_nitrado = RateLimiter(max_requests=3, time_window=60)

# ----------------------------------------------------------------
# Global Command Cooldowns
# ----------------------------------------------------------------

command_cooldown = CommandCooldown()

# Command cooldown configuration (in seconds)
# Aligned with API rate limits to prevent conflicts
# NASA: 5 req/60s -> 15s cooldown (safety margin for slow connections)
# OpenWeather: 10 req/60s -> 8s cooldown
# CatFact: 30 req/60s -> 3s cooldown
# Games/UX: 10-15s for reasonable user experience
# Quick utilities: 2s
COMMAND_COOLDOWNS = {
    'calc': 2,
    'quiz': 10,
    'hangman': 15,
    'weather': 8,
    'city': 8,
    'time': 8,
    'rps': 10,
    'guess': 10,
    'roll': 10,
    'apod': 15,
    'marsphoto': 15,
    'asteroids': 15,
    'sun': 15,
    'exoplanet': 15,
    'catfact': 3,
}

# ----------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------

def log_rate_limit_hit(api_name: str, retry_after: float):
    # Log rate limit hit
    logger.warning(f"Rate limit hit for {api_name}. Retry after {retry_after:.1f}s")

def log_cooldown_hit(command: str, remaining: float):
    # Log command cooldown hit
    logger.info(f"Command {command} on cooldown. Remaining: {remaining:.1f}s")

async def check_api_limit(limiter: RateLimiter, api_name: str, identifier: str = "global") -> Tuple[bool, Optional[str]]:
    # Check API rate limit and return error message if limit hit
    # Returns: (allowed: bool, error_message: Optional[str])
    allowed, retry_after = limiter.is_allowed(identifier)

    if not allowed:
        error_msg = f"API rate limit exceeded. Please wait {retry_after:.0f} seconds."
        log_rate_limit_hit(api_name, retry_after)
        return False, error_msg

    return True, None

async def check_command_cooldown(command: str) -> Tuple[bool, Optional[str]]:
    # Check command cooldown and return error message if on cooldown
    # Returns: (allowed: bool, error_message: Optional[str])
    cooldown_seconds = COMMAND_COOLDOWNS.get(command, 0)

    if cooldown_seconds <= 0:
        return True, None

    on_cooldown, remaining = command_cooldown.is_on_cooldown(command, cooldown_seconds)

    if on_cooldown:
        error_msg = f"This command is on cooldown. Please wait {remaining:.0f} seconds."
        log_cooldown_hit(command, remaining)
        return False, error_msg

    command_cooldown.set_cooldown(command)
    return True, None

def get_cooldown_remaining(command: str) -> float:
    # Get remaining cooldown time for command
    cooldown_seconds = COMMAND_COOLDOWNS.get(command, 0)
    return command_cooldown.get_remaining(command, cooldown_seconds)

def reset_cooldown(command: str):
    # Reset cooldown for testing/debugging purposes
    if command in command_cooldown.last_execution:
        del command_cooldown.last_execution[command]
        logger.debug(f"Cooldown reset for command: {command}")