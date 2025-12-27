"""
Utility Functions for MX-BOT
Helper functions and utilities
"""
import os
import re
import random
import string
import logging
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def generate_verification_code(length: int = 8) -> str:
    """Generate random verification code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def extract_instagram_url(text: str) -> Optional[str]:
    """Extract Instagram URL from text"""
    # Pattern for Instagram URLs
    patterns = [
        r'(?:https?://)?(?:www\.)?instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?instagram\.com/stories/([A-Za-z0-9._]+)/(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return None

def extract_media_url(text: str) -> Optional[str]:
    """
    Extract any media URL from text (for yt-dlp supported sites)
    Supports YouTube, SoundCloud, Twitter, TikTok, and other platforms
    """
    # General URL pattern
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    
    match = re.search(url_pattern, text)
    if match:
        url = match.group(0)
        # Clean trailing punctuation
        url = url.rstrip('.,;:!?')
        return url
    
    return None

def is_instagram_url(url: str) -> bool:
    """Check if URL is an Instagram URL using proper URL parsing"""
    if not url:
        return False
    try:
        parsed = urlparse(url if url.startswith('http') else f'https://{url}')
        hostname = parsed.netloc.lower()
        # Remove 'www.' prefix if present
        if hostname.startswith('www.'):
            hostname = hostname[4:]
        return hostname == 'instagram.com'
    except Exception:
        return False

def is_ytdlp_supported_url(url: str) -> bool:
    """
    Check if URL is from a platform supported by yt-dlp
    Excludes Instagram (handled separately)
    Uses proper URL parsing for security
    """
    if not url:
        return False
    
    try:
        parsed = urlparse(url if url.startswith('http') else f'https://{url}')
        hostname = parsed.netloc.lower()
        
        # Remove 'www.' prefix if present
        if hostname.startswith('www.'):
            hostname = hostname[4:]
        
        # Known supported domains (non-Instagram)
        supported_domains = {
            'youtube.com', 'youtu.be',
            'soundcloud.com',
            'twitter.com', 'x.com',
            'tiktok.com',
            'vimeo.com',
            'dailymotion.com',
            'twitch.tv',
            'facebook.com', 'fb.watch',
            'reddit.com',
            'streamable.com',
            'bandcamp.com',
            'mixcloud.com',
            'bilibili.com',
        }
        
        # Check for exact match or subdomain match
        if hostname in supported_domains:
            return True
        
        # Check if hostname ends with a supported domain (for subdomains)
        for domain in supported_domains:
            if hostname.endswith('.' + domain):
                return True
        
        return False
    except Exception:
        return False

def is_valid_instagram_username(username: str) -> bool:
    """Validate Instagram username format"""
    pattern = r'^[a-zA-Z0-9._]{1,30}$'
    return bool(re.match(pattern, username))

def format_number(num: int) -> str:
    """Format number with Persian digits and separators"""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)

def format_file_size(size_bytes: int) -> str:
    """Format file size to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def format_duration(seconds: int) -> str:
    """Format duration to human readable format"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    return filename

def get_media_type_from_url(url: str) -> str:
    """Determine media type from URL"""
    if '/p/' in url:
        return 'post'
    elif '/reel/' in url:
        return 'reel'
    elif '/tv/' in url:
        return 'igtv'
    elif '/stories/' in url:
        return 'story'
    return 'unknown'

def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def validate_telegram_token(token: str) -> bool:
    """Validate Telegram bot token format"""
    pattern = r'^\d+:[A-Za-z0-9_-]{35}$'
    return bool(re.match(pattern, token))

def is_admin(user_id: int, admin_id: int) -> bool:
    """Check if user is admin"""
    return user_id == admin_id

def get_timestamp() -> str:
    """Get current timestamp"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def parse_instagram_shortcode(url: str) -> Optional[str]:
    """Extract Instagram shortcode from URL"""
    patterns = [
        r'instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)',
        r'instagram\.com/stories/[^/]+/(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def setup_logging(log_file: str = 'bot.log', level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def clean_caption(caption: str, max_length: int = 1000) -> str:
    """Clean and truncate caption"""
    if not caption:
        return ""
    
    # Remove extra whitespace
    caption = ' '.join(caption.split())
    
    # Truncate if too long
    if len(caption) > max_length:
        caption = caption[:max_length] + "..."
    
    return caption

def extract_hashtags(text: str) -> list:
    """Extract hashtags from text"""
    return re.findall(r'#\w+', text)

def extract_mentions(text: str) -> list:
    """Extract mentions from text"""
    return re.findall(r'@\w+', text)

class RateLimiter:
    """Simple rate limiter"""
    def __init__(self):
        self.last_request = {}
    
    def can_proceed(self, user_id: int, cooldown: int = 5) -> Tuple[bool, int]:
        """Check if user can make request"""
        now = datetime.now().timestamp()
        
        if user_id in self.last_request:
            time_passed = now - self.last_request[user_id]
            if time_passed < cooldown:
                return False, int(cooldown - time_passed)
        
        self.last_request[user_id] = now
        return True, 0
    
    def reset(self, user_id: int):
        """Reset rate limit for user"""
        if user_id in self.last_request:
            del self.last_request[user_id]

# Global rate limiter instance
rate_limiter = RateLimiter()
