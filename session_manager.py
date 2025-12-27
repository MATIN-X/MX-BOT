"""
Instagram Session Manager for MX-BOT
Handles Instagram session creation and management
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired, 
    ChallengeRequired, 
    TwoFactorRequired,
    BadPassword,
    PleaseWaitFewMinutes
)

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, session_dir: str = 'sessions'):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.client = None
        self.username = None
    
    def get_session_file(self, username: str) -> Path:
        """Get session file path for username"""
        return self.session_dir / f"{username}.json"
    
    def login(self, username: str, password: str, verification_code: str = None) -> tuple:
        """
        Login to Instagram
        Returns: (success: bool, message: str, client: Optional[Client])
        """
        try:
            self.client = Client()
            self.username = username
            session_file = self.get_session_file(username)
            
            # Try to load existing session
            if session_file.exists():
                try:
                    logger.info(f"Loading session from {session_file}")
                    self.client.load_settings(session_file)
                    self.client.login(username, password)
                    logger.info(f"Successfully logged in using saved session for {username}")
                    return True, "Login successful using saved session", self.client
                except Exception as e:
                    logger.warning(f"Failed to use saved session: {e}")
                    # Continue to fresh login
            
            # Fresh login
            logger.info(f"Attempting fresh login for {username}")
            
            if verification_code:
                self.client.two_factor_login(username, password, verification_code)
            else:
                self.client.login(username, password)
            
            # Save session
            self.client.dump_settings(session_file)
            logger.info(f"Session saved to {session_file}")
            
            return True, "Login successful", self.client
            
        except TwoFactorRequired:
            logger.warning("Two-factor authentication required")
            return False, "2FA_REQUIRED", None
            
        except ChallengeRequired:
            logger.warning("Challenge required (verification)")
            return False, "CHALLENGE_REQUIRED", None
            
        except BadPassword:
            logger.error("Bad password")
            return False, "BAD_PASSWORD", None
            
        except PleaseWaitFewMinutes:
            logger.error("Rate limited by Instagram")
            return False, "RATE_LIMITED", None
            
        except LoginRequired:
            logger.error("Login required (session expired)")
            return False, "LOGIN_REQUIRED", None
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False, f"ERROR: {str(e)}", None
    
    def validate_session(self, username: str) -> bool:
        """Validate existing session"""
        try:
            session_file = self.get_session_file(username)
            if not session_file.exists():
                return False
            
            client = Client()
            client.load_settings(session_file)
            
            # Try to get account info to validate
            client.account_info()
            return True
            
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return False
    
    def load_session(self, username: str) -> Optional[Client]:
        """Load existing session"""
        try:
            session_file = self.get_session_file(username)
            if not session_file.exists():
                logger.error(f"Session file not found: {session_file}")
                return None
            
            client = Client()
            client.load_settings(session_file)
            logger.info(f"Session loaded for {username}")
            
            self.client = client
            self.username = username
            return client
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None
    
    def get_client(self) -> Optional[Client]:
        """Get current client instance"""
        return self.client
    
    def logout(self):
        """Logout and clear session"""
        if self.client:
            try:
                self.client.logout()
            except:
                pass
            self.client = None
            self.username = None
    
    def upload_session_file(self, username: str, session_data: bytes) -> tuple:
        """
        Upload session file and validate it
        Returns: (success: bool, message: str, extracted_username: Optional[str])
        """
        try:
            session_file = self.get_session_file(username)
            
            # Validate JSON
            data = json.loads(session_data)
            
            # Try to extract username from session data if available
            extracted_username = username
            if 'authorization_data' in data and 'ds_user' in data.get('authorization_data', {}):
                extracted_username = data['authorization_data'].get('ds_user', username)
            elif 'uuids' in data and 'username' in data.get('uuids', {}):
                extracted_username = data['uuids'].get('username', username)
            
            # Save to file
            with open(session_file, 'wb') as f:
                f.write(session_data)
            
            logger.info(f"Session file uploaded for {username}")
            return True, "Session uploaded successfully", extracted_username
            
        except json.JSONDecodeError:
            logger.error("Invalid session file format")
            return False, "فرمت فایل JSON نامعتبر است", None
        except Exception as e:
            logger.error(f"Failed to upload session: {e}")
            return False, f"خطا در آپلود: {str(e)}", None
    
    def load_and_validate_session(self, username: str) -> tuple:
        """
        Load session from file and validate it
        Returns: (success: bool, message: str, client: Optional[Client])
        """
        try:
            session_file = self.get_session_file(username)
            if not session_file.exists():
                return False, "فایل سشن یافت نشد", None
            
            client = Client()
            client.load_settings(session_file)
            
            # Try to validate by getting account info
            try:
                account_info = client.account_info()
                self.client = client
                self.username = username
                logger.info(f"Session loaded and validated for {username}")
                return True, "سشن معتبر است", client
            except Exception as e:
                logger.warning(f"Session validation failed: {e}")
                return False, f"سشن نامعتبر است: {str(e)}", None
                
        except json.JSONDecodeError:
            logger.error("Invalid session file format")
            return False, "فرمت فایل سشن نامعتبر است", None
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False, f"خطا در بارگذاری سشن: {str(e)}", None
    
    def get_username_from_session_file(self, session_data: bytes) -> Optional[str]:
        """Extract username from session file data"""
        try:
            data = json.loads(session_data)
            
            # Try different possible locations for username
            if 'authorization_data' in data:
                auth_data = data['authorization_data']
                if 'ds_user' in auth_data:
                    return auth_data['ds_user']
            
            if 'uuids' in data:
                uuids = data['uuids']
                if 'username' in uuids:
                    return uuids['username']
            
            # Try to find username in any nested dict
            for key, value in data.items():
                if isinstance(value, dict):
                    if 'username' in value:
                        return value['username']
                    if 'ds_user' in value:
                        return value['ds_user']
            
            return None
        except Exception:
            return None
    
    def delete_session(self, username: str):
        """Delete session file"""
        try:
            session_file = self.get_session_file(username)
            if session_file.exists():
                session_file.unlink()
                logger.info(f"Session deleted for {username}")
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
    
    def get_session_status(self) -> dict:
        """Get current session status"""
        if not self.client or not self.username:
            return {
                'active': False,
                'username': None,
                'message': 'No active session'
            }
        
        try:
            # Try to get account info
            self.client.account_info()
            return {
                'active': True,
                'username': self.username,
                'message': 'Session is active and valid'
            }
        except Exception as e:
            return {
                'active': False,
                'username': self.username,
                'message': f'Session invalid: {str(e)}'
            }

# Global session manager instance
session_manager = SessionManager()
