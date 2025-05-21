from typing import Dict, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_system_prompt(character_name: str = "Sophia", personality: str = "romantic and flirty") -> Dict:
    """Get the system prompt for chat conversations"""
    return {
        "role": "system",
        "content": (
            f"You are {character_name}, a {personality} college student in a texting simulation. "
            "You never mention you're an AI or bot. Respond naturally, emotionally, and affectionately "
            "using pet names, emojis, and humor. Keep responses concise and engaging."
        )
    }

def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display"""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def get_time_ago(timestamp: datetime) -> str:
    """Get human-readable time ago string"""
    now = datetime.now()
    diff = now - timestamp
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_list(items: List[str], max_items: int = 3) -> str:
    """Format a list of items with a maximum number of items to show"""
    if not items:
        return "None"
    if len(items) <= max_items:
        return ", ".join(items)
    return ", ".join(items[:max_items]) + f" and {len(items) - max_items} more"
