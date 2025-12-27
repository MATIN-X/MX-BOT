"""
Instagram Handler for MX-BOT
Wrapper for Instagram API operations
"""
import logging
import time
from typing import Optional, Dict, List, Any
from instagrapi import Client
from instagrapi.exceptions import (
    MediaNotFound,
    PrivateAccount,
    LoginRequired,
    PleaseWaitFewMinutes
)
from session_manager import session_manager

logger = logging.getLogger(__name__)

class InstagramHandler:
    def __init__(self):
        self.client = None
    
    def initialize(self, username: str, password: str = None):
        """Initialize Instagram client"""
        # Try to load existing session
        self.client = session_manager.load_session(username)
        
        if not self.client and password:
            # Login if no session exists
            success, message, client = session_manager.login(username, password)
            if success:
                self.client = client
            else:
                raise Exception(f"Failed to initialize Instagram: {message}")
    
    def get_client(self) -> Optional[Client]:
        """Get Instagram client"""
        if not self.client:
            self.client = session_manager.get_client()
        return self.client
    
    def check_direct_message(self, verification_code: str, max_messages: int = 50) -> bool:
        """
        Check if verification code exists in direct messages
        Also checks message requests (pending DMs) which is where new users' messages go
        Returns True if code found
        """
        try:
            client = self.get_client()
            if not client:
                logger.error("No active Instagram client")
                return False
            
            # First check regular direct threads
            threads = client.direct_threads(amount=20)
            
            for thread in threads:
                # Get messages from thread
                messages = client.direct_messages(thread.id, amount=max_messages)
                
                for message in messages:
                    if message.text and verification_code in message.text:
                        logger.info(f"Verification code found in DM from user {message.user_id}")
                        return True
            
            # Also check message requests (pending DMs)
            # This is where messages from users who don't follow each other go
            try:
                pending_threads = client.direct_pending_inbox()
                for thread in pending_threads:
                    # Get messages from pending thread
                    messages = client.direct_messages(thread.id, amount=max_messages)
                    
                    for message in messages:
                        if message.text and verification_code in message.text:
                            logger.info(f"Verification code found in pending DM from user {message.user_id}")
                            # Optionally approve the thread so future messages appear in regular inbox
                            try:
                                client.direct_thread_approve(thread.id)
                            except Exception as approve_error:
                                logger.warning(f"Could not approve thread: {approve_error}")
                            return True
            except Exception as pending_error:
                logger.warning(f"Could not check pending inbox: {pending_error}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking DMs: {e}")
            return False
    
    def get_media_info(self, url: str) -> Optional[Dict]:
        """Get media information from URL"""
        try:
            client = self.get_client()
            if not client:
                logger.error("No active Instagram client")
                return None
            
            # Extract media ID from URL
            media_pk = client.media_pk_from_url(url)
            
            # Get media info
            media = client.media_info(media_pk)
            
            info = {
                'media_type': self._get_media_type(media.media_type),
                'user': {
                    'username': media.user.username,
                    'full_name': media.user.full_name,
                    'is_verified': media.user.is_verified,
                    'profile_pic_url': media.user.profile_pic_url,
                },
                'caption': media.caption_text if media.caption_text else '',
                'like_count': media.like_count,
                'comment_count': media.comment_count,
                'taken_at': media.taken_at,
                'product_type': media.product_type,
                'thumbnail_url': media.thumbnail_url,
                'resources': []
            }
            
            # Handle different media types
            if media.media_type == 1:  # Photo
                info['resources'].append({
                    'type': 'photo',
                    'url': media.thumbnail_url,
                })
            elif media.media_type == 2:  # Video
                info['resources'].append({
                    'type': 'video',
                    'url': media.video_url,
                    'thumbnail': media.thumbnail_url,
                })
            elif media.media_type == 8:  # Album/Carousel
                for resource in media.resources:
                    if resource.media_type == 1:
                        info['resources'].append({
                            'type': 'photo',
                            'url': resource.thumbnail_url,
                        })
                    elif resource.media_type == 2:
                        info['resources'].append({
                            'type': 'video',
                            'url': resource.video_url,
                            'thumbnail': resource.thumbnail_url,
                        })
            
            return info
            
        except MediaNotFound:
            logger.error("Media not found")
            return None
        except PrivateAccount:
            logger.error("Account is private")
            return None
        except LoginRequired:
            logger.error("Login required - session expired")
            return None
        except PleaseWaitFewMinutes:
            logger.error("Rate limited by Instagram")
            return None
        except Exception as e:
            logger.error(f"Error getting media info: {e}")
            return None
    
    def download_media(self, url: str, folder: str = 'downloads') -> Optional[List[str]]:
        """
        Download media from URL
        Returns list of downloaded file paths
        """
        try:
            client = self.get_client()
            if not client:
                logger.error("No active Instagram client")
                return None
            
            # Extract media PK from URL
            media_pk = client.media_pk_from_url(url)
            
            # Get media info first
            media = client.media_info(media_pk)
            
            downloaded_files = []
            
            # Download based on media type
            if media.media_type == 1:  # Photo
                path = client.photo_download(media_pk, folder)
                downloaded_files.append(path)
                
            elif media.media_type == 2:  # Video
                path = client.video_download(media_pk, folder)
                downloaded_files.append(path)
                
            elif media.media_type == 8:  # Album/Carousel
                paths = client.album_download(media_pk, folder)
                downloaded_files.extend(paths)
            
            logger.info(f"Downloaded {len(downloaded_files)} files")
            return downloaded_files
            
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None
    
    def download_story(self, story_pk: int, folder: str = 'downloads') -> Optional[str]:
        """Download story"""
        try:
            client = self.get_client()
            if not client:
                return None
            
            path = client.story_download(story_pk, folder)
            return path
            
        except Exception as e:
            logger.error(f"Error downloading story: {e}")
            return None
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information"""
        try:
            client = self.get_client()
            if not client:
                return None
            
            user = client.user_info_by_username(username)
            
            return {
                'user_id': str(user.pk),
                'username': user.username,
                'full_name': user.full_name,
                'is_verified': user.is_verified,
                'is_private': user.is_private,
                'profile_pic_url': user.profile_pic_url,
                'follower_count': user.follower_count,
                'following_count': user.following_count,
                'media_count': user.media_count,
                'biography': user.biography,
            }
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def _get_media_type(self, media_type: int) -> str:
        """Convert media type number to string"""
        types = {
            1: 'photo',
            2: 'video',
            8: 'album'
        }
        return types.get(media_type, 'unknown')
    
    def is_session_valid(self) -> bool:
        """Check if current session is valid"""
        try:
            client = self.get_client()
            if not client:
                return False
            
            # Try to get account info
            client.account_info()
            return True
            
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return False

# Global Instagram handler instance
instagram_handler = InstagramHandler()
