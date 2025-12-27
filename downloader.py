"""
Download Manager for MX-BOT
Handles media downloads with yt-dlp integration
"""
import os
import logging
import subprocess
import hashlib
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import yt_dlp

logger = logging.getLogger(__name__)

class Downloader:
    def __init__(self, download_dir: str = 'downloads'):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.url_cache = {}  # Cache for URL info

    def get_url_hash(self, url: str) -> str:
        """Generate a short hash for URL identification"""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Get video information without downloading
        Returns detailed info for quality selection
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if not info:
                    return None

                # Cache the info
                url_hash = self.get_url_hash(url)
                self.url_cache[url_hash] = {
                    'url': url,
                    'info': info,
                    'timestamp': datetime.now()
                }

                # Format the info
                return {
                    'title': info.get('title', 'Unknown'),
                    'uploader': info.get('uploader', info.get('channel', 'Unknown')),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'upload_date': info.get('upload_date', ''),
                    'description': info.get('description', '')[:500] if info.get('description') else '',
                    'thumbnail': info.get('thumbnail', ''),
                    'webpage_url': info.get('webpage_url', url),
                    'id': info.get('id', ''),
                    'formats': self._parse_formats(info.get('formats', [])),
                    'url_hash': url_hash,
                }

        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return None

    def _parse_formats(self, formats: List[Dict]) -> List[Dict]:
        """Parse and filter available formats"""
        parsed = []
        seen_qualities = set()

        for fmt in formats:
            if not fmt.get('url'):
                continue

            # Get format info
            format_id = fmt.get('format_id', '')
            ext = fmt.get('ext', '')
            height = fmt.get('height', 0)
            width = fmt.get('width', 0)
            filesize = fmt.get('filesize', 0) or fmt.get('filesize_approx', 0)
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')
            format_note = fmt.get('format_note', '')

            # Skip formats without video for video quality selection
            if vcodec == 'none' and acodec != 'none':
                # This is audio only, add separately
                continue

            # Create quality label
            if height:
                quality = f"{height}p"
            elif format_note:
                quality = format_note
            else:
                quality = format_id

            # Skip duplicates
            if quality in seen_qualities:
                continue
            seen_qualities.add(quality)

            parsed.append({
                'format_id': format_id,
                'ext': ext,
                'quality': quality,
                'height': height,
                'width': width,
                'filesize': filesize,
                'has_video': vcodec != 'none',
                'has_audio': acodec != 'none',
            })

        # Sort by height (quality) descending
        parsed.sort(key=lambda x: x.get('height', 0), reverse=True)

        # Limit to top 8 quality options
        return parsed[:8]

    def download_with_ytdlp(self, url: str, extract_audio: bool = False,
                           quality: str = 'best', format_id: str = None) -> Optional[Dict]:
        """
        Download media using yt-dlp with quality options
        Returns dict with file path and info
        """
        try:
            output_template = str(self.download_dir / '%(title).100s.%(ext)s')

            ydl_opts = {
                'outtmpl': output_template,
                'quiet': False,
                'no_warnings': False,
                'restrictfilenames': True,
            }

            # Set format based on options
            if extract_audio:
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            elif format_id and format_id != 'best':
                ydl_opts['format'] = f'{format_id}+bestaudio/best'
            elif quality == 'best':
                ydl_opts['format'] = 'bestvideo[filesize<50M]+bestaudio/best[filesize<50M]/best'
            elif quality == '720':
                ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
            elif quality == '480':
                ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
            elif quality == '360':
                ydl_opts['format'] = 'bestvideo[height<=360]+bestaudio/best[height<=360]'
            elif quality == '240':
                ydl_opts['format'] = 'bestvideo[height<=240]+bestaudio/best[height<=240]'
            elif quality == 'audio':
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
                extract_audio = True
            else:
                ydl_opts['format'] = 'best[filesize<50M]/best'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get info and download
                info = ydl.extract_info(url, download=True)

                # Get the downloaded file path
                if extract_audio or quality == 'audio':
                    filename = ydl.prepare_filename(info)
                    filepath = os.path.splitext(filename)[0] + '.mp3'
                else:
                    filepath = ydl.prepare_filename(info)

                # Format upload date
                upload_date = info.get('upload_date', '')
                if upload_date and len(upload_date) == 8:
                    try:
                        upload_date = f"{upload_date[:4]}/{upload_date[4:6]}/{upload_date[6:]}"
                    except:
                        pass

                return {
                    'filepath': filepath,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', info.get('channel', 'Unknown')),
                    'thumbnail': info.get('thumbnail', None),
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'upload_date': upload_date,
                    'video_id': info.get('id', ''),
                    'webpage_url': info.get('webpage_url', url),
                    'is_audio': extract_audio or quality == 'audio',
                }

        except Exception as e:
            logger.error(f"yt-dlp download failed: {e}")
            return None

    def download_audio_only(self, url: str) -> Optional[Dict]:
        """Download only audio as MP3"""
        return self.download_with_ytdlp(url, extract_audio=True)

    def download_with_quality(self, url: str, quality: str) -> Optional[Dict]:
        """Download with specific quality"""
        return self.download_with_ytdlp(url, quality=quality)

    def download_with_format_id(self, url: str, format_id: str) -> Optional[Dict]:
        """Download with specific format ID"""
        if format_id == 'audio':
            return self.download_audio_only(url)
        return self.download_with_ytdlp(url, format_id=format_id)

    def extract_audio_from_video(self, video_path: str) -> Optional[str]:
        """Extract audio from video file using ffmpeg"""
        try:
            video_path = Path(video_path)
            audio_path = video_path.with_suffix('.mp3')

            # Use ffmpeg to extract audio
            command = [
                'ffmpeg',
                '-i', str(video_path),
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-q:a', '2',  # Quality
                str(audio_path),
                '-y'  # Overwrite
            ]

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )

            if audio_path.exists():
                logger.info(f"Audio extracted to {audio_path}")
                return str(audio_path)
            else:
                logger.error("Audio file not created")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            return None
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return None

    def get_file_size(self, filepath: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(filepath)
        except:
            return 0

    def cleanup_file(self, filepath: str):
        """Delete file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Cleaned up file: {filepath}")
        except Exception as e:
            logger.error(f"Failed to cleanup file: {e}")

    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old downloaded files"""
        try:
            import time
            current_time = time.time()

            for file_path in self.download_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > (max_age_hours * 3600):
                        file_path.unlink()
                        logger.info(f"Cleaned up old file: {file_path}")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def is_supported_url(self, url: str) -> bool:
        """Check if URL is supported by yt-dlp"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                ydl.extract_info(url, download=False)
                return True
        except:
            return False

    def get_formats(self, url: str) -> Optional[List[Dict]]:
        """Get available formats for URL"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])

                # Filter and format info
                available_formats = []
                for fmt in formats:
                    available_formats.append({
                        'format_id': fmt.get('format_id'),
                        'ext': fmt.get('ext'),
                        'quality': fmt.get('format_note', 'unknown'),
                        'filesize': fmt.get('filesize', 0),
                    })

                return available_formats

        except Exception as e:
            logger.error(f"Failed to get formats: {e}")
            return None

    def get_cached_url(self, url_hash: str) -> Optional[str]:
        """Get original URL from cache by hash"""
        if url_hash in self.url_cache:
            return self.url_cache[url_hash].get('url')
        return None

    def clear_cache(self):
        """Clear URL cache"""
        self.url_cache.clear()

# Global downloader instance
downloader = Downloader()
