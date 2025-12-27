"""
Main Bot File for MX-BOT
Instagram Download Telegram Bot - Complete Version
"""
import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from telegram.constants import ParseMode, ChatAction
from telegram.error import TelegramError

from config import config
from database import db
from messages import messages
from keyboards import keyboards
from utils import (
    generate_verification_code,
    extract_instagram_url,
    extract_media_url,
    is_instagram_url,
    is_ytdlp_supported_url,
    is_valid_instagram_username,
    format_number,
    format_duration,
    get_timestamp,
    rate_limiter,
    setup_logging
)
from instagram_handler import instagram_handler
from downloader import downloader
from session_manager import session_manager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Conversation states
(WAITING_USERNAME, WAITING_VERIFICATION, WAITING_BROADCAST,
 WAITING_SESSION_FILE, WAITING_CHANNEL_ID, WAITING_USER_SEARCH,
 WAITING_MESSAGE_TO_USER, WAITING_IG_USERNAME, WAITING_IG_PASSWORD) = range(9)


class MXBot:
    def __init__(self):
        self.app = None
        self.bot_username = None
        self.instagram_initialized = False

    async def check_channel_membership(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is member of all required channels"""
        channels = db.get_locked_channels()

        if not channels:
            return True  # No channel lock

        for channel in channels:
            if not channel.get('is_active'):
                continue

            channel_id = channel.get('channel_id')
            try:
                member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                if member.status in ['left', 'kicked']:
                    return False
            except TelegramError as e:
                logger.error(f"Error checking membership for {channel_id}: {e}")
                # If we can't check, assume they're not a member
                return False

        return True

    async def check_membership_middleware(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Middleware to check channel membership before processing"""
        user = update.effective_user
        if not user:
            return False

        # Admin is exempt from channel lock
        if user.id == config.admin_id:
            return True

        # Check if user is banned
        if db.is_user_banned(user.id):
            if update.message:
                await update.message.reply_text(messages.USER_BANNED_MESSAGE)
            return False

        # Check channel membership
        if not await self.check_channel_membership(user.id, context):
            channels = db.get_locked_channels()
            channels_text = ""
            for ch in channels:
                if ch.get('is_active'):
                    title = ch.get('channel_title') or ch.get('channel_username') or "کانال"
                    channels_text += f"• {title}\n"

            text = messages.CHANNEL_LOCK_REQUIRED.format(channels=channels_text)

            if update.message:
                await update.message.reply_text(
                    text,
                    reply_markup=keyboards.join_channel_buttons(channels),
                    parse_mode=ParseMode.HTML
                )
            elif update.callback_query:
                await update.callback_query.message.reply_text(
                    text,
                    reply_markup=keyboards.join_channel_buttons(channels),
                    parse_mode=ParseMode.HTML
                )
            return False

        return True

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user = update.effective_user

        # Add user to database
        db.add_user(user.id, user.username, user.first_name)

        # Check membership
        if not await self.check_membership_middleware(update, context):
            return

        is_admin = user.id == config.admin_id

        await update.message.reply_text(
            messages.WELCOME,
            reply_markup=keyboards.main_menu(is_admin),
            parse_mode=ParseMode.HTML
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        if not await self.check_membership_middleware(update, context):
            return

        await update.message.reply_text(
            messages.HELP,
            parse_mode=ParseMode.HTML
        )

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        if not await self.check_membership_middleware(update, context):
            return

        user_id = update.effective_user.id
        user = db.get_user(user_id)
        accounts = db.get_user_instagram_accounts(user_id)

        if not user:
            await update.message.reply_text(messages.ERROR_OCCURRED)
            return

        premium_status = "👑 وضعیت: کاربر ویژه" if user.get('is_premium') else ""

        stats_text = messages.YOUR_STATS.format(
            downloads=user['download_count'],
            accounts=len([acc for acc in accounts if acc['is_verified']]),
            join_date=user['created_at'][:10],
            premium_status=premium_status
        )

        await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)

    async def accounts_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show accounts management menu"""
        if not await self.check_membership_middleware(update, context):
            return

        user_id = update.effective_user.id
        accounts = db.get_user_instagram_accounts(user_id)

        if not accounts:
            await update.message.reply_text(
                messages.NO_ACCOUNTS,
                reply_markup=keyboards.account_management()
            )
        else:
            accounts_text = ""
            for acc in accounts:
                status = "✅" if acc['is_verified'] else "⏳"
                accounts_text += f"{status} @{acc['instagram_username']}\n"

            text = messages.ACCOUNTS_LIST.format(accounts=accounts_text)
            await update.message.reply_text(
                text,
                reply_markup=keyboards.accounts_list(accounts),
                parse_mode=ParseMode.HTML
            )

    async def add_account_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding Instagram account"""
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            messages.ENTER_INSTAGRAM_USERNAME,
            reply_markup=keyboards.back_button()
        )

        return WAITING_USERNAME

    async def receive_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive Instagram username"""
        username = update.message.text.strip().replace('@', '')
        user_id = update.effective_user.id

        # Validate username
        if not is_valid_instagram_username(username):
            await update.message.reply_text(
                "❌ نام کاربری نامعتبر است! لطفاً فقط نام کاربری اینستاگرام را وارد کنید."
            )
            return WAITING_USERNAME

        # Check if account exists on Instagram
        if self.instagram_initialized:
            user_info = instagram_handler.get_user_info(username)
            if not user_info:
                await update.message.reply_text(
                    "❌ این نام کاربری در اینستاگرام یافت نشد! لطفاً نام کاربری صحیح را وارد کنید."
                )
                return WAITING_USERNAME

        # Generate verification code
        code = generate_verification_code()
        expires_at = datetime.now() + timedelta(minutes=30)

        # Save to database
        verification_id = db.create_verification(user_id, username, code, expires_at)

        # Also add to instagram_accounts for tracking
        db.add_instagram_account(user_id, username, code, expires_at)

        # Get admin Instagram accounts for verification
        admin_accounts = db.get_admin_instagram_accounts()
        if admin_accounts:
            bot_ig_username = admin_accounts[0]['username']
        else:
            bot_ig_username = config.instagram_username or "ربات"

        # Send verification instructions
        text = messages.VERIFICATION_CODE_SENT.format(
            code=code,
            bot_username=bot_ig_username,
            minutes=30
        )

        await update.message.reply_text(
            text,
            reply_markup=keyboards.verification_check(verification_id),
            parse_mode=ParseMode.HTML
        )

        return ConversationHandler.END

    async def check_verification(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check if verification code was sent"""
        query = update.callback_query
        await query.answer("در حال بررسی...")

        # Extract verification ID
        verification_id = int(query.data.split(':')[1])
        verification = db.get_verification(verification_id)

        if not verification:
            await query.message.edit_text("❌ کد تایید منقضی شده است!")
            return

        # Check Instagram DMs for the code
        await query.message.edit_text(messages.VERIFICATION_PENDING)

        code_found = False
        if self.instagram_initialized:
            code_found = instagram_handler.check_direct_message(verification['verification_code'])

        if code_found:
            # Mark account as verified
            accounts = db.get_user_instagram_accounts(verification['user_id'])
            for acc in accounts:
                if acc['instagram_username'] == verification['instagram_username']:
                    db.verify_instagram_account(acc['id'])
                    break

            # Delete verification
            db.delete_verification(verification_id)

            success_text = messages.VERIFICATION_SUCCESS.format(
                username=verification['instagram_username']
            )

            await query.message.edit_text(
                success_text,
                reply_markup=keyboards.back_button(),
                parse_mode=ParseMode.HTML
            )
        else:
            admin_accounts = db.get_admin_instagram_accounts()
            bot_ig_username = admin_accounts[0]['username'] if admin_accounts else config.instagram_username or "ربات"

            fail_text = messages.VERIFICATION_FAILED.format(
                bot_username=bot_ig_username
            )

            await query.message.edit_text(
                fail_text,
                reply_markup=keyboards.verification_check(verification_id),
                parse_mode=ParseMode.HTML
            )

    async def check_membership_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check membership when user clicks 'I joined' button"""
        query = update.callback_query
        user_id = update.effective_user.id

        if await self.check_channel_membership(user_id, context):
            await query.answer("✅ عضویت تایید شد!")
            await query.message.edit_text(messages.MEMBERSHIP_VERIFIED)

            # Show main menu
            is_admin = user_id == config.admin_id
            await query.message.reply_text(
                messages.WELCOME,
                reply_markup=keyboards.main_menu(is_admin),
                parse_mode=ParseMode.HTML
            )
        else:
            await query.answer("❌ هنوز عضو نشده‌اید!", show_alert=True)

    async def ytdlp_download_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle download requests for yt-dlp supported URLs"""
        user_id = update.effective_user.id

        # Add user to database if not exists
        user = update.effective_user
        db.add_user(user_id, user.username, user.first_name)

        # Check membership
        if not await self.check_membership_middleware(update, context):
            return

        # Check rate limit
        can_proceed, wait_time = rate_limiter.can_proceed(user_id, cooldown=5)
        if not can_proceed:
            await update.message.reply_text(
                f"{messages.RATE_LIMIT}\n⏳ لطفاً {wait_time} ثانیه صبر کنید."
            )
            return

        text = update.message.text
        url = extract_media_url(text)

        if not url:
            await update.message.reply_text(messages.INVALID_LINK)
            return

        # Store URL in context for later use
        context.user_data['download_url'] = url

        # Get video info first
        status_msg = await update.message.reply_text(messages.FETCHING_INFO)

        try:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.TYPING
            )

            info = downloader.get_video_info(url)

            if info:
                # Format duration
                duration_str = format_duration(info.get('duration', 0)) if info.get('duration') else "نامشخص"
                views_str = format_number(info.get('view_count', 0)) if info.get('view_count') else "نامشخص"

                # Show quality selection
                select_text = messages.SELECT_QUALITY.format(
                    title=info.get('title', 'Unknown')[:50],
                    uploader=info.get('uploader', 'Unknown'),
                    duration=duration_str,
                    views=views_str
                )

                await status_msg.edit_text(
                    select_text,
                    reply_markup=keyboards.download_options(url),
                    parse_mode=ParseMode.HTML
                )
            else:
                # Direct download with best quality
                await self._perform_download(update, context, status_msg, url, 'best')

        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            # Fallback to direct download
            await self._perform_download(update, context, status_msg, url, 'best')

    async def handle_quality_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle quality selection callback"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data == "cancel_download":
            await query.message.edit_text("❌ دانلود لغو شد.")
            return

        if data.startswith("dl:"):
            parts = data.split(":", 2)
            if len(parts) >= 2:
                quality = parts[1]
                url = context.user_data.get('download_url')

                if not url:
                    await query.message.edit_text("❌ خطا: لینک یافت نشد. لطفاً دوباره لینک را ارسال کنید.")
                    return

                await query.message.edit_text(messages.DOWNLOADING)
                await self._perform_download(update, context, query.message, url, quality)

    async def _perform_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               status_msg, url: str, quality: str):
        """Perform the actual download"""
        user_id = update.effective_user.id

        try:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.UPLOAD_DOCUMENT
            )

            logger.info(f"Downloading with yt-dlp: {url} (quality: {quality})")
            result = downloader.download_with_quality(url, quality)

            if result:
                await status_msg.edit_text(messages.UPLOADING)

                file_size = downloader.get_file_size(result['filepath'])

                # Check file size (50MB limit)
                if file_size > 50 * 1024 * 1024:
                    await update.effective_message.reply_text(messages.FILE_TOO_LARGE)
                    downloader.cleanup_file(result['filepath'])
                    await status_msg.delete()
                    return

                # Prepare caption with full info
                duration_str = format_duration(result.get('duration', 0)) if result.get('duration') else "نامشخص"
                views_str = format_number(result.get('view_count', 0)) if result.get('view_count') else "نامشخص"
                likes_str = format_number(result.get('like_count', 0)) if result.get('like_count') else "نامشخص"

                if result.get('is_audio'):
                    caption = messages.AUDIO_DOWNLOAD_SUCCESS.format(
                        title=result.get('title', 'Unknown'),
                        uploader=result.get('uploader', 'Unknown'),
                        duration=duration_str,
                        url=result.get('webpage_url', url)
                    )
                else:
                    caption = messages.DOWNLOAD_SUCCESS_YTDLP.format(
                        title=result.get('title', 'Unknown'),
                        uploader=result.get('uploader', 'Unknown'),
                        duration=duration_str,
                        views=views_str,
                        likes=likes_str,
                        upload_date=result.get('upload_date', 'نامشخص'),
                        video_id=result.get('video_id', ''),
                        url=result.get('webpage_url', url)
                    )

                # Determine file type
                ext = os.path.splitext(result['filepath'])[1].lower()

                with open(result['filepath'], 'rb') as f:
                    if ext in ['.mp3', '.m4a', '.wav', '.ogg', '.opus'] or result.get('is_audio'):
                        await update.effective_message.reply_audio(
                            audio=f,
                            caption=caption,
                            title=result.get('title', 'Unknown'),
                            performer=result.get('uploader', 'Unknown'),
                            parse_mode=ParseMode.HTML
                        )
                    elif ext in ['.mp4', '.webm', '.mkv', '.mov']:
                        await update.effective_message.reply_video(
                            video=f,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    else:
                        await update.effective_message.reply_document(
                            document=f,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )

                # Cleanup
                downloader.cleanup_file(result['filepath'])
                await status_msg.delete()

                # Record download
                db.add_download(user_id, 'ytdlp', url)
                db.increment_download_count(user_id)
            else:
                await status_msg.edit_text(
                    messages.DOWNLOAD_FAILED.format(error="دانلود ناموفق. لینک را بررسی کنید.")
                )

        except Exception as e:
            logger.error(f"yt-dlp download error: {e}")
            await status_msg.edit_text(
                messages.DOWNLOAD_FAILED.format(error=str(e))
            )

    async def download_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle download requests for Instagram URLs"""
        user_id = update.effective_user.id

        # Check membership
        if not await self.check_membership_middleware(update, context):
            return

        # Check if user has verified account
        if not db.has_verified_account(user_id):
            await update.message.reply_text(messages.NO_VERIFIED_ACCOUNT, parse_mode=ParseMode.HTML)
            return

        # Check rate limit
        can_proceed, wait_time = rate_limiter.can_proceed(user_id, cooldown=5)
        if not can_proceed:
            await update.message.reply_text(
                f"{messages.RATE_LIMIT}\n⏳ لطفاً {wait_time} ثانیه صبر کنید."
            )
            return

        text = update.message.text
        url = extract_instagram_url(text)

        if not url:
            await update.message.reply_text(messages.INVALID_LINK)
            return

        # Send downloading message
        status_msg = await update.message.reply_text(messages.DOWNLOADING)

        try:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.TYPING
            )

            # Get media info
            media_info = None
            if self.instagram_initialized:
                media_info = instagram_handler.get_media_info(url)

            if not media_info:
                # Try yt-dlp as fallback
                logger.info("Instagram download failed, trying yt-dlp")
                result = downloader.download_with_ytdlp(url)

                if result:
                    await status_msg.edit_text(messages.UPLOADING)

                    with open(result['filepath'], 'rb') as f:
                        await update.message.reply_document(
                            document=f,
                            caption=f"📥 {result['title']}\n👤 {result['uploader']}"
                        )

                    downloader.cleanup_file(result['filepath'])
                    await status_msg.delete()

                    db.add_download(user_id, 'ytdlp', url)
                    db.increment_download_count(user_id)
                    return
                else:
                    await status_msg.edit_text(
                        messages.DOWNLOAD_FAILED.format(error="رسانه یافت نشد")
                    )
                    return

            # Download with Instagram
            await status_msg.edit_text(messages.PROCESSING)

            downloaded_files = instagram_handler.download_media(url, config.download_dir)

            if not downloaded_files:
                await status_msg.edit_text(
                    messages.DOWNLOAD_FAILED.format(error="دانلود ناموفق")
                )
                return

            await status_msg.edit_text(messages.UPLOADING)

            # Prepare caption
            caption = messages.DOWNLOAD_SUCCESS.format(
                username=media_info['user']['username'],
                likes=format_number(media_info['like_count']),
                comments=format_number(media_info['comment_count']),
                caption=media_info['caption'][:200] if media_info['caption'] else '',
                post_url=url
            )

            # Send files
            for file_path in downloaded_files:
                if not os.path.exists(file_path):
                    continue

                file_size = downloader.get_file_size(file_path)

                if file_size > 50 * 1024 * 1024:
                    await update.message.reply_text(messages.FILE_TOO_LARGE)
                    downloader.cleanup_file(file_path)
                    continue

                ext = os.path.splitext(file_path)[1].lower()

                with open(file_path, 'rb') as f:
                    if ext in ['.jpg', '.jpeg', '.png']:
                        await update.message.reply_photo(
                            photo=f,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    elif ext in ['.mp4', '.mov']:
                        await update.message.reply_video(
                            video=f,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    else:
                        await update.message.reply_document(
                            document=f,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )

                downloader.cleanup_file(file_path)

                db.add_download(user_id, media_info['media_type'], url,
                              media_info['user']['username'], file_size)

            await status_msg.delete()
            db.increment_download_count(user_id)

        except Exception as e:
            logger.error(f"Download error: {e}")
            await status_msg.edit_text(
                messages.DOWNLOAD_FAILED.format(error=str(e))
            )

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin panel"""
        user_id = update.effective_user.id

        if user_id != config.admin_id:
            await update.message.reply_text("❌ شما دسترسی به پنل مدیریت ندارید!")
            return

        # Get statistics
        total_users = db.get_total_users()
        total_downloads = db.get_total_downloads()
        verified_accounts = db.get_total_verified_accounts()
        active_sessions = db.get_total_active_sessions()

        text = messages.ADMIN_PANEL.format(
            total_users=total_users,
            total_downloads=total_downloads,
            verified_accounts=verified_accounts,
            active_sessions=active_sessions
        )

        await update.message.reply_text(
            text,
            reply_markup=keyboards.admin_panel(),
            parse_mode=ParseMode.HTML
        )

    async def admin_stats_detailed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed admin statistics"""
        query = update.callback_query
        await query.answer()

        # Get detailed stats
        total_users = db.get_total_users()
        today_users = db.get_today_users()
        banned_users = db.get_banned_users_count()
        total_downloads = db.get_total_downloads()
        today_downloads = db.get_today_downloads()
        verified_accounts = db.get_total_verified_accounts()
        active_sessions = db.get_total_active_sessions()
        channels = db.get_locked_channels()

        # Downloads by type
        downloads_by_type = db.get_downloads_by_type()
        type_text = ""
        for media_type, count in downloads_by_type.items():
            type_text += f"   • {media_type}: {count}\n"

        if not type_text:
            type_text = "   • هیچ دانلودی ثبت نشده\n"

        text = messages.ADMIN_STATS_DETAILED.format(
            total_users=total_users,
            today_users=today_users,
            banned_users=banned_users,
            total_downloads=total_downloads,
            today_downloads=today_downloads,
            downloads_by_type=type_text,
            verified_accounts=verified_accounts,
            active_sessions=active_sessions,
            channel_count=len(channels)
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboards.back_button("admin_panel"),
            parse_mode=ParseMode.HTML
        )

    async def admin_channel_lock(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Channel lock management"""
        query = update.callback_query
        await query.answer()

        channels = db.get_locked_channels()
        status = messages.CHANNEL_LOCK_ENABLED if channels else messages.CHANNEL_LOCK_DISABLED

        text = messages.CHANNEL_LOCK_SETTINGS.format(status=status)

        await query.message.edit_text(
            text,
            reply_markup=keyboards.channel_lock_menu(channels),
            parse_mode=ParseMode.HTML
        )

    async def add_channel_lock_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding channel to lock list"""
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            messages.ENTER_CHANNEL_ID,
            reply_markup=keyboards.back_button("admin_channel_lock"),
            parse_mode=ParseMode.HTML
        )

        return WAITING_CHANNEL_ID

    async def receive_channel_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive channel ID/username"""
        text = update.message.text.strip()
        user_id = update.effective_user.id

        if user_id != config.admin_id:
            return ConversationHandler.END

        # Parse channel identifier
        if text.startswith('@'):
            channel_username = text[1:]
            channel_id = text
        elif text.startswith('-100'):
            channel_id = text
            channel_username = None
        else:
            channel_username = text
            channel_id = f"@{text}"

        # Try to get channel info
        try:
            chat = await context.bot.get_chat(channel_id)
            channel_title = chat.title
            channel_id = str(chat.id)
            channel_username = chat.username
        except TelegramError as e:
            await update.message.reply_text(
                messages.INVALID_CHANNEL,
                reply_markup=keyboards.back_button("admin_channel_lock")
            )
            return ConversationHandler.END

        # Add channel to database
        success = db.add_channel_lock(channel_id, channel_username, channel_title)

        if success:
            await update.message.reply_text(
                messages.CHANNEL_ADDED,
                reply_markup=keyboards.back_button("admin_channel_lock")
            )
        else:
            await update.message.reply_text(
                messages.CHANNEL_LIMIT_REACHED,
                reply_markup=keyboards.back_button("admin_channel_lock")
            )

        return ConversationHandler.END

    async def view_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View channel details"""
        query = update.callback_query
        await query.answer()

        channel_id = query.data.split(':')[1]
        channels = db.get_locked_channels()

        channel = None
        for ch in channels:
            if ch['channel_id'] == channel_id:
                channel = ch
                break

        if not channel:
            await query.message.edit_text("❌ کانال یافت نشد!")
            return

        is_active = channel.get('is_active', False)
        status = "✅ فعال" if is_active else "❌ غیرفعال"
        title = channel.get('channel_title') or channel.get('channel_username') or channel_id

        text = f"""📢 <b>اطلاعات کانال</b>

🆔 آیدی: <code>{channel_id}</code>
📝 نام: {title}
🔹 وضعیت: {status}"""

        await query.message.edit_text(
            text,
            reply_markup=keyboards.channel_actions(channel_id, is_active),
            parse_mode=ParseMode.HTML
        )

    async def toggle_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enable/disable channel"""
        query = update.callback_query
        await query.answer()

        data = query.data
        channel_id = data.split(':')[1]

        if data.startswith('enable_channel:'):
            db.toggle_channel_lock(channel_id, True)
            await query.answer("✅ کانال فعال شد!")
        elif data.startswith('disable_channel:'):
            db.toggle_channel_lock(channel_id, False)
            await query.answer("❌ کانال غیرفعال شد!")
        elif data.startswith('delete_channel:'):
            db.remove_channel_lock(channel_id)
            await query.answer("🗑 کانال حذف شد!")

        # Refresh channel lock menu
        await self.admin_channel_lock(update, context)

    async def admin_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User management menu"""
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            "👥 <b>مدیریت کاربران</b>\n\nیک گزینه را انتخاب کنید:",
            reply_markup=keyboards.user_management(),
            parse_mode=ParseMode.HTML
        )

    async def admin_users_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show paginated users list"""
        query = update.callback_query
        await query.answer()

        page = int(query.data.split(':')[1]) if ':' in query.data else 0
        users = db.get_all_users()

        await query.message.edit_text(
            f"👥 <b>لیست کاربران</b> (صفحه {page + 1})\n\nتعداد کل: {len(users)}",
            reply_markup=keyboards.users_list(users, page),
            parse_mode=ParseMode.HTML
        )

    async def admin_search_user_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start user search"""
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            messages.ENTER_USER_ID,
            reply_markup=keyboards.back_button("admin_users")
        )

        return WAITING_USER_SEARCH

    async def receive_user_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive user search query"""
        query_text = update.message.text.strip()

        users = db.search_users(query_text)

        if not users:
            await update.message.reply_text(
                messages.USER_NOT_FOUND,
                reply_markup=keyboards.back_button("admin_users")
            )
            return ConversationHandler.END

        if len(users) == 1:
            # Show single user
            user = users[0]
            context.user_data['target_user_id'] = user['user_id']
            await self._show_user_info(update.message, user)
        else:
            # Show list
            await update.message.reply_text(
                f"🔍 {len(users)} کاربر یافت شد:",
                reply_markup=keyboards.users_list(users, 0)
            )

        return ConversationHandler.END

    async def view_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View user details"""
        query = update.callback_query
        await query.answer()

        user_id = int(query.data.split(':')[1])
        user = db.get_user(user_id)

        if not user:
            await query.message.edit_text(messages.USER_NOT_FOUND)
            return

        context.user_data['target_user_id'] = user_id
        await self._show_user_info(query.message, user, edit=True)

    async def _show_user_info(self, message, user, edit=False):
        """Show user information"""
        status = "🚫 مسدود" if user.get('is_banned') else "✅ فعال"

        text = messages.USER_INFO.format(
            user_id=user['user_id'],
            first_name=user.get('first_name') or 'ندارد',
            username=user.get('username') or 'ندارد',
            downloads=user.get('download_count', 0),
            join_date=user.get('created_at', '')[:10],
            status=status
        )

        keyboard = keyboards.user_actions(user['user_id'], user.get('is_banned', False))

        if edit:
            await message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    async def ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban user"""
        query = update.callback_query
        await query.answer()

        user_id = int(query.data.split(':')[1])
        db.ban_user(user_id)

        await query.answer(messages.USER_BANNED.format(user_id=user_id), show_alert=True)

        # Refresh user info
        user = db.get_user(user_id)
        if user:
            await self._show_user_info(query.message, user, edit=True)

    async def unban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unban user"""
        query = update.callback_query
        await query.answer()

        user_id = int(query.data.split(':')[1])
        db.unban_user(user_id)

        await query.answer(messages.USER_UNBANNED.format(user_id=user_id), show_alert=True)

        # Refresh user info
        user = db.get_user(user_id)
        if user:
            await self._show_user_info(query.message, user, edit=True)

    async def admin_banned_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show banned users"""
        query = update.callback_query
        await query.answer()

        users = [u for u in db.get_all_users() if u.get('is_banned')]

        await query.message.edit_text(
            f"🚫 <b>کاربران مسدود شده</b>\n\nتعداد: {len(users)}",
            reply_markup=keyboards.banned_users_list(users),
            parse_mode=ParseMode.HTML
        )

    async def send_to_user_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start sending message to user"""
        query = update.callback_query
        await query.answer()

        user_id = int(query.data.split(':')[1])
        context.user_data['target_user_id'] = user_id

        await query.message.edit_text(
            messages.ENTER_MESSAGE_TO_USER,
            reply_markup=keyboards.back_button("admin_users")
        )

        return WAITING_MESSAGE_TO_USER

    async def send_message_to_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send message to specific user"""
        target_user_id = context.user_data.get('target_user_id')
        message_text = update.message.text

        if not target_user_id:
            await update.message.reply_text("❌ خطا: کاربر هدف یافت نشد!")
            return ConversationHandler.END

        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"📬 <b>پیام از مدیریت:</b>\n\n{message_text}",
                parse_mode=ParseMode.HTML
            )
            await update.message.reply_text(
                messages.MESSAGE_SENT_TO_USER,
                reply_markup=keyboards.back_button("admin_users")
            )
        except TelegramError as e:
            logger.error(f"Failed to send message to user {target_user_id}: {e}")
            await update.message.reply_text(
                messages.MESSAGE_FAILED_TO_USER,
                reply_markup=keyboards.back_button("admin_users")
            )

        return ConversationHandler.END

    async def admin_instagram_accounts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin Instagram accounts management"""
        query = update.callback_query
        await query.answer()

        accounts = db.get_admin_instagram_accounts()

        await query.message.edit_text(
            messages.ADMIN_IG_ACCOUNTS_MENU,
            reply_markup=keyboards.admin_instagram_accounts_menu(accounts),
            parse_mode=ParseMode.HTML
        )

    async def add_admin_ig_account_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding admin Instagram account"""
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            messages.ENTER_IG_USERNAME,
            reply_markup=keyboards.back_button("admin_instagram_accounts"),
            parse_mode=ParseMode.HTML
        )

        return WAITING_IG_USERNAME

    async def receive_ig_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive Instagram username for admin account"""
        username = update.message.text.strip().replace('@', '')

        if not is_valid_instagram_username(username):
            await update.message.reply_text(
                "❌ نام کاربری نامعتبر است!",
                reply_markup=keyboards.back_button("admin_instagram_accounts")
            )
            return ConversationHandler.END

        context.user_data['ig_username'] = username

        await update.message.reply_text(
            messages.ENTER_IG_PASSWORD,
            reply_markup=keyboards.back_button("admin_instagram_accounts"),
            parse_mode=ParseMode.HTML
        )

        return WAITING_IG_PASSWORD

    async def receive_ig_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive Instagram password and try to login"""
        password = update.message.text.strip()
        username = context.user_data.get('ig_username')

        if not username:
            await update.message.reply_text("❌ خطا: نام کاربری یافت نشد!")
            return ConversationHandler.END

        # Delete password message for security
        try:
            await update.message.delete()
        except:
            pass

        status_msg = await update.effective_chat.send_message("⏳ در حال ورود به اینستاگرام...")

        # Try to login
        success, message, client = session_manager.login(username, password)

        if success:
            # Save to database
            session_file = str(session_manager.get_session_file(username))
            db.add_admin_instagram_account(username, session_file, is_primary=True)

            # Update Instagram handler
            instagram_handler.client = client
            self.instagram_initialized = True

            await status_msg.edit_text(
                messages.IG_LOGIN_SUCCESS.format(username=username),
                reply_markup=keyboards.back_button("admin_instagram_accounts"),
                parse_mode=ParseMode.HTML
            )
        else:
            await status_msg.edit_text(
                messages.IG_SESSION_REQUIRED,
                reply_markup=keyboards.waiting_session_options(),
                parse_mode=ParseMode.HTML
            )

        return ConversationHandler.END

    async def admin_broadcast_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start broadcast message"""
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            messages.BROADCAST_MESSAGE,
            reply_markup=keyboards.back_button("admin_panel")
        )

        return WAITING_BROADCAST

    async def admin_broadcast_send(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send broadcast message"""
        broadcast_text = update.message.text

        users = db.get_all_users()
        sent_count = 0
        total = len(users)

        status_msg = await update.message.reply_text(
            messages.BROADCAST_PROGRESS.format(sent=0, total=total)
        )

        for i, user in enumerate(users):
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=broadcast_text,
                    parse_mode=ParseMode.HTML
                )
                sent_count += 1

                # Update progress every 10 users
                if (i + 1) % 10 == 0:
                    await status_msg.edit_text(
                        messages.BROADCAST_PROGRESS.format(sent=sent_count, total=total)
                    )

                await asyncio.sleep(0.05)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to send to {user['user_id']}: {e}")

        await status_msg.edit_text(
            messages.BROADCAST_SENT.format(count=sent_count)
        )

        return ConversationHandler.END

    async def admin_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bot settings menu"""
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            "⚙️ <b>تنظیمات ربات</b>\n\nیک گزینه را انتخاب کنید:",
            reply_markup=keyboards.bot_settings(),
            parse_mode=ParseMode.HTML
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data == "back_to_menu":
            user_id = update.effective_user.id
            is_admin = user_id == config.admin_id

            await query.message.edit_text(
                messages.MAIN_MENU,
                reply_markup=keyboards.main_menu(is_admin)
            )

        elif data == "list_accounts":
            user_id = update.effective_user.id
            accounts = db.get_user_instagram_accounts(user_id)

            if not accounts:
                await query.message.edit_text(
                    messages.NO_ACCOUNTS,
                    reply_markup=keyboards.account_management()
                )
            else:
                accounts_text = ""
                for acc in accounts:
                    status = "✅" if acc['is_verified'] else "⏳"
                    accounts_text += f"{status} @{acc['instagram_username']}\n"

                text = messages.ACCOUNTS_LIST.format(accounts=accounts_text)
                await query.message.edit_text(
                    text,
                    reply_markup=keyboards.accounts_list(accounts),
                    parse_mode=ParseMode.HTML
                )

        elif data.startswith("view_account:"):
            account_id = int(data.split(':')[1])
            account = db.get_instagram_account(account_id)

            if account:
                status = "✅ تایید شده" if account['is_verified'] else "⏳ در انتظار تایید"
                text = f"📱 حساب: @{account['instagram_username']}\n🔹 وضعیت: {status}"

                await query.message.edit_text(
                    text,
                    reply_markup=keyboards.account_actions(account_id)
                )

        elif data.startswith("delete_account:"):
            account_id = int(data.split(':')[1])
            await query.message.edit_text(
                "⚠️ آیا مطمئن هستید که می‌خواهید این حساب را حذف کنید?",
                reply_markup=keyboards.confirm_delete(account_id)
            )

        elif data.startswith("confirm_delete:"):
            account_id = int(data.split(':')[1])
            db.delete_instagram_account(account_id)

            await query.message.edit_text(
                messages.ACCOUNT_DELETED,
                reply_markup=keyboards.back_button("list_accounts")
            )

        elif data == "admin_panel":
            await self.admin_stats_detailed(update, context)

        elif data == "admin_stats":
            await self.admin_stats_detailed(update, context)

        elif data == "admin_channel_lock":
            await self.admin_channel_lock(update, context)

        elif data == "admin_users":
            await self.admin_users(update, context)

        elif data == "admin_banned_users":
            await self.admin_banned_users(update, context)

        elif data == "admin_instagram_accounts":
            await self.admin_instagram_accounts(update, context)

        elif data == "admin_settings":
            await self.admin_settings(update, context)

        elif data == "admin_sessions":
            await self.admin_sessions_callback(update, context)

        elif data.startswith("view_channel:"):
            await self.view_channel(update, context)

        elif data.startswith(("enable_channel:", "disable_channel:", "delete_channel:")):
            await self.toggle_channel(update, context)

        elif data.startswith("admin_users_list:"):
            await self.admin_users_list(update, context)

        elif data.startswith("view_user:"):
            await self.view_user(update, context)

        elif data.startswith("ban_user:"):
            await self.ban_user(update, context)

        elif data.startswith("unban_user:"):
            await self.unban_user(update, context)

        elif data == "cancel_action":
            await query.message.edit_text("❌ عملیات لغو شد.")

    async def admin_sessions_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Session management callback"""
        query = update.callback_query
        user_id = update.effective_user.id

        if user_id != config.admin_id:
            await query.message.edit_text("❌ شما دسترسی به این بخش ندارید!")
            return

        status = session_manager.get_session_status()

        if status['active']:
            status_text = "✅ فعال و معتبر"
        else:
            status_text = "❌ غیرفعال"

        text = f"""🔑 <b>مدیریت نشست‌های اینستاگرام</b>

📊 <b>وضعیت فعلی:</b>
👤 نام کاربری: @{status['username'] or config.instagram_username or 'تنظیم نشده'}
🔹 وضعیت: {status_text}

<b>گزینه‌ها:</b>
• بررسی وضعیت - وضعیت اتصال را بررسی کنید
• ورود مجدد - با نام کاربری و رمز عبور تلاش کنید
• آپلود نشست - فایل سشن JSON را آپلود کنید"""

        instagram_error = context.application.bot_data.get('instagram_error')
        if instagram_error:
            text += f"\n\n⚠️ <b>خطای فعلی:</b>\n<code>{instagram_error[:200]}</code>"

        await query.message.edit_text(
            text,
            reply_markup=keyboards.session_management(),
            parse_mode=ParseMode.HTML
        )

    async def upload_session_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start session file upload"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        if user_id != config.admin_id:
            await query.message.edit_text("❌ شما دسترسی به این بخش ندارید!")
            return ConversationHandler.END

        await query.message.edit_text(
            messages.UPLOAD_SESSION_PROMPT,
            reply_markup=keyboards.back_button("admin_sessions"),
            parse_mode=ParseMode.HTML
        )

        return WAITING_SESSION_FILE

    async def receive_session_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive session file from user"""
        user_id = update.effective_user.id

        if user_id != config.admin_id:
            await update.message.reply_text("❌ شما دسترسی به این بخش ندارید!")
            return ConversationHandler.END

        document = update.message.document

        if document.file_name and not document.file_name.endswith('.json'):
            await update.message.reply_text(
                "❌ فقط فایل‌های JSON پذیرفته می‌شوند!",
                reply_markup=keyboards.back_button("admin_sessions")
            )
            return WAITING_SESSION_FILE

        try:
            status_msg = await update.message.reply_text("⏳ در حال دریافت فایل...")

            file = await context.bot.get_file(document.file_id)
            file_data = await file.download_as_bytearray()

            extracted_username = session_manager.get_username_from_session_file(bytes(file_data))
            username = extracted_username or config.instagram_username

            success, message, _ = session_manager.upload_session_file(username, bytes(file_data))

            if not success:
                await status_msg.edit_text(
                    messages.SESSION_UPLOAD_FAILED.format(error=message),
                    reply_markup=keyboards.back_button("admin_sessions"),
                    parse_mode=ParseMode.HTML
                )
                return WAITING_SESSION_FILE

            await status_msg.edit_text(
                messages.SESSION_UPLOAD_SUCCESS.format(
                    username=username,
                    filename=document.file_name or "session.json"
                ),
                parse_mode=ParseMode.HTML
            )

            valid_success, valid_message, client = session_manager.load_and_validate_session(username)

            if valid_success:
                instagram_handler.client = client
                self.instagram_initialized = True
                context.application.bot_data['instagram_initialized'] = True
                context.application.bot_data['instagram_error'] = None

                # Save to database
                session_file = str(session_manager.get_session_file(username))
                db.add_admin_instagram_account(username, session_file, is_primary=True)

                await update.message.reply_text(
                    messages.SESSION_VALID.format(username=username),
                    reply_markup=keyboards.session_management(),
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    messages.SESSION_INVALID,
                    reply_markup=keyboards.session_management(),
                    parse_mode=ParseMode.HTML
                )

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error receiving session file: {e}")
            await update.message.reply_text(
                messages.SESSION_UPLOAD_FAILED.format(error=str(e)),
                reply_markup=keyboards.back_button("admin_sessions"),
                parse_mode=ParseMode.HTML
            )
            return WAITING_SESSION_FILE

    async def check_session_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check Instagram session status"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        if user_id != config.admin_id:
            await query.message.edit_text("❌ شما دسترسی به این بخش ندارید!")
            return

        status = session_manager.get_session_status()

        if status['active']:
            status_text = "✅ فعال و معتبر"
        else:
            status_text = f"❌ غیرفعال - {status['message']}"

        text = messages.SESSION_STATUS.format(
            username=status['username'] or config.instagram_username or 'تنظیم نشده',
            status=status_text,
            last_check=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        instagram_error = context.application.bot_data.get('instagram_error')
        if instagram_error:
            text += f"\n\n⚠️ <b>خطای قبلی:</b>\n<code>{instagram_error}</code>"

        await query.message.edit_text(
            text,
            reply_markup=keyboards.session_management(),
            parse_mode=ParseMode.HTML
        )

    async def relogin_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Try to re-login with credentials"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        if user_id != config.admin_id:
            await query.message.edit_text("❌ شما دسترسی به این بخش ندارید!")
            return

        if not config.instagram_username or not config.instagram_password:
            await query.message.edit_text(
                "❌ نام کاربری یا رمز عبور اینستاگرام تنظیم نشده است!",
                reply_markup=keyboards.session_management()
            )
            return

        await query.message.edit_text("⏳ در حال تلاش برای ورود مجدد...")

        try:
            success, message, client = session_manager.login(
                config.instagram_username,
                config.instagram_password
            )

            if success:
                instagram_handler.client = client
                self.instagram_initialized = True
                context.application.bot_data['instagram_initialized'] = True
                context.application.bot_data['instagram_error'] = None

                await query.message.edit_text(
                    "✅ ورود با موفقیت انجام شد!",
                    reply_markup=keyboards.session_management()
                )
            else:
                context.application.bot_data['instagram_error'] = message

                await query.message.edit_text(
                    messages.INSTAGRAM_LOGIN_FAILED.format(error=message),
                    reply_markup=keyboards.session_management(),
                    parse_mode=ParseMode.HTML
                )

        except Exception as e:
            logger.error(f"Re-login failed: {e}")
            context.application.bot_data['instagram_error'] = str(e)

            await query.message.edit_text(
                messages.INSTAGRAM_LOGIN_FAILED.format(error=str(e)),
                reply_markup=keyboards.session_management(),
                parse_mode=ParseMode.HTML
            )

    async def message_router(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route text messages"""
        text = update.message.text

        if text == "📥 دانلود":
            if await self.check_membership_middleware(update, context):
                await update.message.reply_text(messages.SEND_LINK, parse_mode=ParseMode.HTML)
        elif text == "📱 حساب‌های من":
            await self.accounts_menu(update, context)
        elif text == "📊 آمار":
            await self.stats_command(update, context)
        elif text == "❓ راهنما":
            await self.help_command(update, context)
        elif text == "👨‍💼 پنل مدیریت":
            await self.admin_panel(update, context)
        elif extract_instagram_url(text):
            await self.download_handler(update, context)
        elif is_ytdlp_supported_url(extract_media_url(text) or ''):
            await self.ytdlp_download_handler(update, context)
        else:
            # Check if it's a URL that might be supported
            url = extract_media_url(text)
            if url:
                await self.ytdlp_download_handler(update, context)
            else:
                await update.message.reply_text(
                    "❌ دستور نامعتبر! از منو استفاده کنید یا لینک ارسال کنید.\n\n"
                    "🔗 لینک‌های پشتیبانی شده:\n"
                    "• اینستاگرام (نیاز به ثبت حساب)\n"
                    "• یوتیوب، ساندکلود و... (بدون ثبت حساب)"
                )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        user_id = update.effective_user.id
        is_admin = user_id == config.admin_id

        await update.message.reply_text(
            "❌ عملیات لغو شد.",
            reply_markup=keyboards.main_menu(is_admin)
        )
        return ConversationHandler.END

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")

    def run(self):
        """Run the bot"""
        # Load config
        if not os.path.exists('config.ini'):
            logger.error("Config file not found! Please run install.sh first.")
            return

        config.load()

        # Validate config
        valid, errors = config.validate()
        if not valid:
            logger.error(f"Invalid configuration: {errors}")
            return

        # Create directories
        os.makedirs('downloads', exist_ok=True)
        os.makedirs('sessions', exist_ok=True)

        # Initialize Instagram handler
        instagram_error = None
        try:
            if config.instagram_username and config.instagram_password:
                instagram_handler.initialize(
                    config.instagram_username,
                    config.instagram_password
                )
                self.instagram_initialized = True
                logger.info("Instagram handler initialized")
            else:
                logger.warning("Instagram credentials not configured")
        except Exception as e:
            instagram_error = str(e)
            self.instagram_initialized = False
            logger.warning(f"Failed to initialize Instagram: {e}")
            logger.info("Bot will continue without Instagram. Admin can upload session file.")

        # Create application
        self.app = Application.builder().token(config.bot_token).build()

        # Store instagram error for admin notification
        self.app.bot_data['instagram_error'] = instagram_error
        self.app.bot_data['instagram_initialized'] = self.instagram_initialized

        # Get bot username
        async def get_bot_info():
            bot = await self.app.bot.get_me()
            self.bot_username = bot.username

        asyncio.get_event_loop().run_until_complete(get_bot_info())

        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))

        # Conversation handler for adding accounts
        add_account_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.add_account_start, pattern="^add_account$")],
            states={
                WAITING_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_username)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(add_account_conv)

        # Broadcast conversation handler
        broadcast_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.admin_broadcast_start, pattern="^admin_broadcast$")],
            states={
                WAITING_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_broadcast_send)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(broadcast_conv)

        # Session upload conversation handler
        session_upload_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.upload_session_start, pattern="^upload_session$")],
            states={
                WAITING_SESSION_FILE: [
                    MessageHandler(filters.Document.ALL, self.receive_session_file),
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(session_upload_conv)

        # Channel lock conversation handler
        channel_lock_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.add_channel_lock_start, pattern="^add_channel_lock$")],
            states={
                WAITING_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_channel_id)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(channel_lock_conv)

        # User search conversation handler
        user_search_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.admin_search_user_start, pattern="^admin_search_user$")],
            states={
                WAITING_USER_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_user_search)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(user_search_conv)

        # Send to user conversation handler
        send_to_user_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.send_to_user_start, pattern="^send_to_user:")],
            states={
                WAITING_MESSAGE_TO_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.send_message_to_user)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(send_to_user_conv)

        # Admin Instagram account conversation handler
        admin_ig_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.add_admin_ig_account_start, pattern="^add_admin_ig_account$")],
            states={
                WAITING_IG_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_ig_username)],
                WAITING_IG_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_ig_password)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(admin_ig_conv)

        # Callback handlers
        self.app.add_handler(CallbackQueryHandler(self.check_verification, pattern="^check_verification:"))
        self.app.add_handler(CallbackQueryHandler(self.check_membership_callback, pattern="^check_membership$"))
        self.app.add_handler(CallbackQueryHandler(self.check_session_status, pattern="^check_session_status$"))
        self.app.add_handler(CallbackQueryHandler(self.relogin_session, pattern="^relogin_session$"))
        self.app.add_handler(CallbackQueryHandler(self.handle_quality_selection, pattern="^dl:"))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))

        # Message handler
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_router))

        # Error handler
        self.app.add_error_handler(self.error_handler)

        # Start bot
        logger.info("Bot started!")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    bot = MXBot()
    bot.run()
