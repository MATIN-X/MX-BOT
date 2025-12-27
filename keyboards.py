"""
Telegram Keyboards for MX-BOT
Persian/Farsi keyboard layouts
"""
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from typing import List, Dict, Optional

class Keyboards:
    @staticmethod
    def main_menu(is_admin=False):
        """Main menu keyboard"""
        keyboard = [
            [KeyboardButton("📥 دانلود"), KeyboardButton("📱 حساب‌های من")],
            [KeyboardButton("📊 آمار"), KeyboardButton("❓ راهنما")],
        ]

        if is_admin:
            keyboard.append([KeyboardButton("👨‍💼 پنل مدیریت")])

        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def account_management():
        """Account management inline keyboard"""
        keyboard = [
            [InlineKeyboardButton("➕ افزودن حساب", callback_data="add_account")],
            [InlineKeyboardButton("📱 مشاهده حساب‌ها", callback_data="list_accounts")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def verification_check(verification_id):
        """Verification check keyboard"""
        keyboard = [
            [InlineKeyboardButton("🔍 بررسی تایید", callback_data=f"check_verification:{verification_id}")],
            [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="add_account")],
            [InlineKeyboardButton("❌ انصراف", callback_data="back_to_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def accounts_list(accounts):
        """List of user accounts"""
        keyboard = []
        for acc in accounts:
            status = "✅" if acc['is_verified'] else "⏳"
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} @{acc['instagram_username']}",
                    callback_data=f"view_account:{acc['id']}"
                )
            ])
        keyboard.append([InlineKeyboardButton("➕ افزودن حساب جدید", callback_data="add_account")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def account_actions(account_id):
        """Actions for specific account"""
        keyboard = [
            [InlineKeyboardButton("🗑 حذف حساب", callback_data=f"delete_account:{account_id}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="list_accounts")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_delete(account_id):
        """Confirm account deletion"""
        keyboard = [
            [InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"confirm_delete:{account_id}")],
            [InlineKeyboardButton("❌ خیر، انصراف", callback_data=f"view_account:{account_id}")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def download_options(url: str, has_audio: bool = True, has_video: bool = True):
        """Download options keyboard with quality selection"""
        keyboard = []

        if has_video:
            keyboard.append([
                InlineKeyboardButton("📹 بهترین کیفیت", callback_data=f"dl:best:{url[:50]}"),
            ])
            keyboard.append([
                InlineKeyboardButton("📺 720p", callback_data=f"dl:720:{url[:50]}"),
                InlineKeyboardButton("📺 480p", callback_data=f"dl:480:{url[:50]}"),
            ])
            keyboard.append([
                InlineKeyboardButton("📺 360p", callback_data=f"dl:360:{url[:50]}"),
                InlineKeyboardButton("📺 240p", callback_data=f"dl:240:{url[:50]}"),
            ])

        if has_audio:
            keyboard.append([
                InlineKeyboardButton("🎵 فقط صدا (MP3)", callback_data=f"dl:audio:{url[:50]}"),
            ])

        keyboard.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel_download")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def quality_selection(formats: List[Dict], url_hash: str):
        """Quality selection from available formats"""
        keyboard = []

        for fmt in formats[:8]:  # Limit to 8 options
            quality = fmt.get('quality', 'Unknown')
            ext = fmt.get('ext', '')
            format_id = fmt.get('format_id', '')
            size = fmt.get('filesize', 0)

            if size:
                size_str = f" ({size // (1024*1024)}MB)" if size > 1024*1024 else ""
            else:
                size_str = ""

            keyboard.append([
                InlineKeyboardButton(
                    f"📺 {quality} ({ext}){size_str}",
                    callback_data=f"fmt:{format_id}:{url_hash}"
                )
            ])

        keyboard.append([InlineKeyboardButton("🎵 فقط صدا", callback_data=f"fmt:audio:{url_hash}")])
        keyboard.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel_download")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def admin_panel():
        """Admin panel keyboard - Complete"""
        keyboard = [
            [InlineKeyboardButton("📊 آمار کامل", callback_data="admin_stats")],
            [
                InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users"),
                InlineKeyboardButton("🚫 کاربران بن شده", callback_data="admin_banned_users"),
            ],
            [InlineKeyboardButton("🔐 مدیریت اکانت‌های اینستاگرام", callback_data="admin_instagram_accounts")],
            [InlineKeyboardButton("🔒 تنظیمات قفل کانال", callback_data="admin_channel_lock")],
            [InlineKeyboardButton("🔑 مدیریت نشست‌ها", callback_data="admin_sessions")],
            [InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast")],
            [InlineKeyboardButton("⚙️ تنظیمات ربات", callback_data="admin_settings")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def channel_lock_menu(channels: List[Dict]):
        """Channel lock management menu"""
        keyboard = []

        # Show current channels
        for ch in channels:
            status = "✅" if ch.get('is_active') else "❌"
            title = ch.get('channel_title') or ch.get('channel_username') or ch.get('channel_id')
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {title[:20]}",
                    callback_data=f"view_channel:{ch['channel_id']}"
                )
            ])

        # Add new channel button (max 2)
        if len(channels) < 2:
            keyboard.append([InlineKeyboardButton("➕ افزودن کانال جدید", callback_data="add_channel_lock")])

        # Toggle all
        if channels:
            keyboard.append([
                InlineKeyboardButton("✅ فعال کردن همه", callback_data="enable_all_channels"),
                InlineKeyboardButton("❌ غیرفعال کردن همه", callback_data="disable_all_channels"),
            ])

        keyboard.append([InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="admin_panel")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def channel_actions(channel_id: str, is_active: bool):
        """Actions for specific channel"""
        keyboard = []

        if is_active:
            keyboard.append([InlineKeyboardButton("❌ غیرفعال کردن", callback_data=f"disable_channel:{channel_id}")])
        else:
            keyboard.append([InlineKeyboardButton("✅ فعال کردن", callback_data=f"enable_channel:{channel_id}")])

        keyboard.append([InlineKeyboardButton("🗑 حذف کانال", callback_data=f"delete_channel:{channel_id}")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_channel_lock")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def join_channel_buttons(channels: List[Dict]):
        """Buttons for joining required channels"""
        keyboard = []

        for ch in channels:
            username = ch.get('channel_username')
            title = ch.get('channel_title') or username or "کانال"

            if username:
                keyboard.append([
                    InlineKeyboardButton(f"📢 عضویت در {title}", url=f"https://t.me/{username}")
                ])

        keyboard.append([InlineKeyboardButton("✅ عضو شدم", callback_data="check_membership")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def user_management(users_page=0):
        """User management keyboard"""
        keyboard = [
            [InlineKeyboardButton("🔍 جستجو کاربر", callback_data="admin_search_user")],
            [InlineKeyboardButton("📋 لیست کاربران", callback_data=f"admin_users_list:{users_page}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def users_list(users: List[Dict], page: int = 0, per_page: int = 10):
        """Paginated users list"""
        keyboard = []

        start = page * per_page
        end = start + per_page
        page_users = users[start:end]

        for user in page_users:
            status = "🚫" if user.get('is_banned') else "✅"
            name = user.get('first_name') or user.get('username') or str(user.get('user_id'))
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {name[:15]} ({user.get('download_count', 0)})",
                    callback_data=f"view_user:{user['user_id']}"
                )
            ])

        # Pagination buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"admin_users_list:{page-1}"))
        if end < len(users):
            nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"admin_users_list:{page+1}"))

        if nav_buttons:
            keyboard.append(nav_buttons)

        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_users")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def user_actions(user_id: int, is_banned: bool):
        """Actions for specific user"""
        keyboard = []

        if is_banned:
            keyboard.append([InlineKeyboardButton("✅ رفع مسدودیت", callback_data=f"unban_user:{user_id}")])
        else:
            keyboard.append([InlineKeyboardButton("🚫 مسدود کردن", callback_data=f"ban_user:{user_id}")])

        keyboard.append([InlineKeyboardButton("📊 مشاهده آمار", callback_data=f"user_stats:{user_id}")])
        keyboard.append([InlineKeyboardButton("💬 ارسال پیام", callback_data=f"send_to_user:{user_id}")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_users")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def banned_users_list(users: List[Dict]):
        """List of banned users"""
        keyboard = []

        for user in users[:15]:  # Limit to 15
            name = user.get('first_name') or user.get('username') or str(user.get('user_id'))
            keyboard.append([
                InlineKeyboardButton(
                    f"🚫 {name[:20]}",
                    callback_data=f"view_user:{user['user_id']}"
                )
            ])

        if not users:
            keyboard.append([InlineKeyboardButton("✅ کاربر بن شده‌ای وجود ندارد", callback_data="admin_users")])

        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def admin_instagram_accounts_menu(accounts: List[Dict]):
        """Admin Instagram accounts management"""
        keyboard = []

        for acc in accounts:
            status = "⭐" if acc.get('is_primary') else "📱"
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} @{acc['username']}",
                    callback_data=f"admin_ig_account:{acc['id']}"
                )
            ])

        keyboard.append([InlineKeyboardButton("➕ افزودن اکانت جدید", callback_data="add_admin_ig_account")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def admin_ig_account_actions(account_id: int, is_primary: bool):
        """Actions for admin Instagram account"""
        keyboard = []

        if not is_primary:
            keyboard.append([InlineKeyboardButton("⭐ تنظیم به عنوان اصلی", callback_data=f"set_primary_ig:{account_id}")])

        keyboard.append([InlineKeyboardButton("📤 آپلود سشن جدید", callback_data=f"upload_ig_session:{account_id}")])
        keyboard.append([InlineKeyboardButton("🔄 بررسی وضعیت", callback_data=f"check_ig_status:{account_id}")])
        keyboard.append([InlineKeyboardButton("🗑 حذف اکانت", callback_data=f"delete_admin_ig:{account_id}")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_instagram_accounts")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def session_management():
        """Session management keyboard"""
        keyboard = [
            [InlineKeyboardButton("🔄 بررسی وضعیت", callback_data="check_session_status")],
            [InlineKeyboardButton("🔐 ورود مجدد", callback_data="relogin_session")],
            [InlineKeyboardButton("📤 آپلود نشست", callback_data="upload_session")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def bot_settings():
        """Bot settings menu"""
        keyboard = [
            [InlineKeyboardButton("🔒 تنظیمات قفل کانال", callback_data="admin_channel_lock")],
            [InlineKeyboardButton("⏱ محدودیت نرخ", callback_data="settings_rate_limit")],
            [InlineKeyboardButton("📁 حداکثر حجم فایل", callback_data="settings_max_file_size")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_action(action: str, target_id: str):
        """Generic confirmation keyboard"""
        keyboard = [
            [InlineKeyboardButton("✅ بله، انجام بده", callback_data=f"confirm_{action}:{target_id}")],
            [InlineKeyboardButton("❌ خیر، انصراف", callback_data="cancel_action")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_button(callback_data="back_to_menu"):
        """Simple back button"""
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=callback_data)]]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def cancel_button():
        """Cancel keyboard"""
        keyboard = [[KeyboardButton("❌ انصراف")]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def waiting_session_options():
        """Options while waiting for session file"""
        keyboard = [
            [InlineKeyboardButton("📤 آپلود فایل سشن", callback_data="upload_session")],
            [InlineKeyboardButton("🔐 ورود با رمز عبور", callback_data="login_with_password")],
            [InlineKeyboardButton("❌ انصراف", callback_data="admin_instagram_accounts")],
        ]
        return InlineKeyboardMarkup(keyboard)

# Keyboards instance
keyboards = Keyboards()
