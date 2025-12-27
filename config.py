"""
Configuration Management for MX-BOT
Handles bot configuration and settings
"""
import os
import configparser
from pathlib import Path

class Config:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.base_dir = Path(__file__).parent.absolute()
        
        # Default values
        self.bot_token = None
        self.admin_id = None
        self.instagram_username = None
        self.instagram_password = None
        self.database_path = str(self.base_dir / 'bot.db')
        self.session_dir = str(self.base_dir / 'sessions')
        self.download_dir = str(self.base_dir / 'downloads')
        
        # Load config if exists
        if os.path.exists(config_file):
            self.load()
    
    def load(self):
        """Load configuration from file"""
        self.config.read(self.config_file)
        
        if 'Telegram' in self.config:
            self.bot_token = self.config['Telegram'].get('bot_token')
            self.admin_id = self.config['Telegram'].getint('admin_id', None)
        
        if 'Instagram' in self.config:
            self.instagram_username = self.config['Instagram'].get('username')
            self.instagram_password = self.config['Instagram'].get('password')
        
        if 'Paths' in self.config:
            self.database_path = self.config['Paths'].get('database', self.database_path)
            self.session_dir = self.config['Paths'].get('sessions', self.session_dir)
            self.download_dir = self.config['Paths'].get('downloads', self.download_dir)
    
    def save(self):
        """Save configuration to file"""
        if 'Telegram' not in self.config:
            self.config['Telegram'] = {}
        self.config['Telegram']['bot_token'] = self.bot_token or ''
        self.config['Telegram']['admin_id'] = str(self.admin_id or '')
        
        if 'Instagram' not in self.config:
            self.config['Instagram'] = {}
        self.config['Instagram']['username'] = self.instagram_username or ''
        self.config['Instagram']['password'] = self.instagram_password or ''
        
        if 'Paths' not in self.config:
            self.config['Paths'] = {}
        self.config['Paths']['database'] = self.database_path
        self.config['Paths']['sessions'] = self.session_dir
        self.config['Paths']['downloads'] = self.download_dir
        
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    def validate(self):
        """Validate required configuration"""
        errors = []
        warnings = []

        if not self.bot_token:
            errors.append("Bot token is required")
        if not self.admin_id:
            errors.append("Admin ID is required")

        # Instagram is optional - can be configured later via admin panel
        if not self.instagram_username:
            warnings.append("Instagram username not set (can be configured via admin panel)")
        if not self.instagram_password:
            warnings.append("Instagram password not set (can be configured via admin panel)")

        return len(errors) == 0, errors

    def has_instagram_credentials(self) -> bool:
        """Check if Instagram credentials are configured"""
        return bool(self.instagram_username and self.instagram_password)

# Global config instance
config = Config()
