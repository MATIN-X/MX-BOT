"""
Database Operations for MX-BOT
SQLite database management
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = 'bot.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_banned INTEGER DEFAULT 0,
                is_premium INTEGER DEFAULT 0,
                download_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Instagram accounts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instagram_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                instagram_username TEXT,
                instagram_user_id TEXT,
                is_verified INTEGER DEFAULT 0,
                verification_code TEXT,
                code_expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Downloads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                media_type TEXT,
                media_url TEXT,
                instagram_username TEXT,
                file_size INTEGER,
                download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Bot sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                session_file TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Pending verifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                verification_code TEXT,
                instagram_username TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Channel lock settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_lock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE,
                channel_username TEXT,
                channel_title TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Bot settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Admin Instagram accounts table (for DM checking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_instagram_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                session_file TEXT,
                is_active INTEGER DEFAULT 1,
                is_primary INTEGER DEFAULT 0,
                last_check TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    # User operations
    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Add or update user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        ''', (user_id, username, first_name))
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        user = self.get_user(user_id)
        return user['is_banned'] == 1 if user else False
    
    def ban_user(self, user_id: int):
        """Ban user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def unban_user(self, user_id: int):
        """Unban user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def increment_download_count(self, user_id: int):
        """Increment user download count"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET download_count = download_count + 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_total_users(self) -> int:
        """Get total users count"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM users')
        result = cursor.fetchone()
        conn.close()
        return result['count'] if result else 0
    
    # Instagram accounts operations
    def add_instagram_account(self, user_id: int, instagram_username: str, 
                              verification_code: str, expires_at: datetime) -> int:
        """Add Instagram account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO instagram_accounts 
            (user_id, instagram_username, verification_code, code_expires_at, is_verified)
            VALUES (?, ?, ?, ?, 0)
        ''', (user_id, instagram_username, verification_code, expires_at))
        
        account_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return account_id
    
    def verify_instagram_account(self, account_id: int, instagram_user_id: str = None):
        """Verify Instagram account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE instagram_accounts 
            SET is_verified = 1, instagram_user_id = ?
            WHERE id = ?
        ''', (instagram_user_id, account_id))
        
        conn.commit()
        conn.close()
    
    def get_instagram_account(self, account_id: int) -> Optional[Dict]:
        """Get Instagram account by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM instagram_accounts WHERE id = ?', (account_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_user_instagram_accounts(self, user_id: int) -> List[Dict]:
        """Get all Instagram accounts for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM instagram_accounts 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def has_verified_account(self, user_id: int) -> bool:
        """Check if user has any verified Instagram account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM instagram_accounts 
            WHERE user_id = ? AND is_verified = 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] > 0 if result else False
    
    def delete_instagram_account(self, account_id: int):
        """Delete Instagram account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM instagram_accounts WHERE id = ?', (account_id,))
        conn.commit()
        conn.close()
    
    def get_account_by_verification_code(self, code: str) -> Optional[Dict]:
        """Get account by verification code"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM instagram_accounts 
            WHERE verification_code = ? AND is_verified = 0 AND code_expires_at > datetime('now')
        ''', (code,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_total_verified_accounts(self) -> int:
        """Get total verified accounts count"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM instagram_accounts WHERE is_verified = 1')
        result = cursor.fetchone()
        conn.close()
        return result['count'] if result else 0
    
    # Downloads operations
    def add_download(self, user_id: int, media_type: str, media_url: str, 
                     instagram_username: str = None, file_size: int = 0):
        """Add download record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO downloads (user_id, media_type, media_url, instagram_username, file_size)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, media_type, media_url, instagram_username, file_size))
        
        conn.commit()
        conn.close()
    
    def get_user_downloads(self, user_id: int) -> List[Dict]:
        """Get user downloads"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM downloads 
            WHERE user_id = ? 
            ORDER BY download_time DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_total_downloads(self) -> int:
        """Get total downloads count"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM downloads')
        result = cursor.fetchone()
        conn.close()
        return result['count'] if result else 0
    
    # Bot sessions operations
    def add_bot_session(self, username: str, session_file: str):
        """Add bot session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Deactivate other sessions
        cursor.execute('UPDATE bot_sessions SET is_active = 0')
        
        cursor.execute('''
            INSERT INTO bot_sessions (username, session_file, is_active)
            VALUES (?, ?, 1)
        ''', (username, session_file))
        
        conn.commit()
        conn.close()
    
    def get_active_session(self) -> Optional[Dict]:
        """Get active bot session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM bot_sessions WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_total_active_sessions(self) -> int:
        """Get count of active sessions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM bot_sessions WHERE is_active = 1')
        result = cursor.fetchone()
        conn.close()
        return result['count'] if result else 0
    
    # Pending verifications operations
    def create_verification(self, user_id: int, instagram_username: str, 
                           verification_code: str, expires_at: datetime) -> int:
        """Create pending verification"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pending_verifications (user_id, instagram_username, verification_code, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, instagram_username, verification_code, expires_at))
        
        verification_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return verification_id
    
    def get_verification(self, verification_id: int) -> Optional[Dict]:
        """Get verification by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM pending_verifications WHERE id = ?', (verification_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def delete_verification(self, verification_id: int):
        """Delete verification"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM pending_verifications WHERE id = ?', (verification_id,))
        conn.commit()
        conn.close()
    
    def cleanup_expired_verifications(self):
        """Clean up expired verifications"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pending_verifications WHERE expires_at < datetime('now')")
        conn.commit()
        conn.close()

    # Channel lock operations
    def add_channel_lock(self, channel_id: str, channel_username: str = None,
                         channel_title: str = None) -> bool:
        """Add channel to lock list (max 2 channels)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if already have 2 channels
        cursor.execute('SELECT COUNT(*) as count FROM channel_lock WHERE is_active = 1')
        result = cursor.fetchone()
        if result and result['count'] >= 2:
            conn.close()
            return False

        try:
            cursor.execute('''
                INSERT INTO channel_lock (channel_id, channel_username, channel_title, is_active)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(channel_id) DO UPDATE SET
                    channel_username = excluded.channel_username,
                    channel_title = excluded.channel_title,
                    is_active = 1
            ''', (channel_id, channel_username, channel_title))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding channel lock: {e}")
            conn.close()
            return False

    def remove_channel_lock(self, channel_id: str):
        """Remove channel from lock list"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM channel_lock WHERE channel_id = ?', (channel_id,))
        conn.commit()
        conn.close()

    def get_locked_channels(self) -> List[Dict]:
        """Get all locked channels"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM channel_lock WHERE is_active = 1')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def is_channel_lock_enabled(self) -> bool:
        """Check if channel lock is enabled"""
        channels = self.get_locked_channels()
        return len(channels) > 0

    def toggle_channel_lock(self, channel_id: str, active: bool):
        """Toggle channel lock status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE channel_lock SET is_active = ? WHERE channel_id = ?',
                      (1 if active else 0, channel_id))
        conn.commit()
        conn.close()

    # Bot settings operations
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get bot setting"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM bot_settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        return row['value'] if row else default

    def set_setting(self, key: str, value: str):
        """Set bot setting"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bot_settings (key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = datetime('now')
        ''', (key, value))
        conn.commit()
        conn.close()

    def get_all_settings(self) -> Dict[str, str]:
        """Get all bot settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM bot_settings')
        rows = cursor.fetchall()
        conn.close()
        return {row['key']: row['value'] for row in rows}

    # Admin Instagram accounts operations
    def add_admin_instagram_account(self, username: str, session_file: str = None,
                                    is_primary: bool = False) -> int:
        """Add admin Instagram account"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # If setting as primary, unset others
        if is_primary:
            cursor.execute('UPDATE admin_instagram_accounts SET is_primary = 0')

        cursor.execute('''
            INSERT INTO admin_instagram_accounts (username, session_file, is_primary, is_active)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(username) DO UPDATE SET
                session_file = excluded.session_file,
                is_primary = excluded.is_primary,
                is_active = 1
        ''', (username, session_file, 1 if is_primary else 0))

        account_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return account_id

    def get_admin_instagram_accounts(self) -> List[Dict]:
        """Get all admin Instagram accounts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin_instagram_accounts WHERE is_active = 1 ORDER BY is_primary DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_primary_admin_instagram(self) -> Optional[Dict]:
        """Get primary admin Instagram account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin_instagram_accounts WHERE is_primary = 1 AND is_active = 1')
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_admin_instagram_account(self, account_id: int):
        """Delete admin Instagram account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admin_instagram_accounts WHERE id = ?', (account_id,))
        conn.commit()
        conn.close()

    def update_admin_instagram_session(self, username: str, session_file: str):
        """Update admin Instagram session file"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE admin_instagram_accounts
            SET session_file = ?, last_check = datetime('now')
            WHERE username = ?
        ''', (session_file, username))
        conn.commit()
        conn.close()

    # Statistics operations
    def get_today_downloads(self) -> int:
        """Get today's download count"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM downloads
            WHERE date(download_time) = date('now')
        ''')
        result = cursor.fetchone()
        conn.close()
        return result['count'] if result else 0

    def get_today_users(self) -> int:
        """Get today's new users count"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM users
            WHERE date(created_at) = date('now')
        ''')
        result = cursor.fetchone()
        conn.close()
        return result['count'] if result else 0

    def get_banned_users_count(self) -> int:
        """Get banned users count"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_banned = 1')
        result = cursor.fetchone()
        conn.close()
        return result['count'] if result else 0

    def get_downloads_by_type(self) -> Dict[str, int]:
        """Get download counts by media type"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT media_type, COUNT(*) as count
            FROM downloads
            GROUP BY media_type
        ''')
        rows = cursor.fetchall()
        conn.close()
        return {row['media_type']: row['count'] for row in rows}

    def search_users(self, query: str) -> List[Dict]:
        """Search users by username or user_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM users
            WHERE username LIKE ? OR CAST(user_id AS TEXT) LIKE ? OR first_name LIKE ?
            LIMIT 20
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

# Global database instance
db = Database()
