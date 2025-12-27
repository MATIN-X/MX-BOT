# 🤖 MX-BOT - Instagram Download Telegram Bot

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A powerful, production-ready Telegram bot for downloading Instagram content with user verification and admin panel.

## ✨ Features

### 📥 Download Capabilities
- **All Instagram Content Types**: Posts, Reels, Stories, IGTV, Albums/Carousels
- **Multiple Download Methods**: Direct URL paste or forward from Instagram
- **YT-DLP Integration**: Fallback download engine for various platforms
- **Audio Extraction**: Extract audio from videos
- **Quality Control**: Best quality downloads under 50MB limit
- **Rich Metadata**: Includes captions, likes, comments, account info

### 🔐 User Verification System
- **Instagram Account Verification**: Users verify their Instagram via DM code
- **Multi-Account Support**: Manage multiple Instagram accounts per user
- **Secure Process**: Random 8-character verification codes with expiration
- **Account Management**: Add, view, delete Instagram accounts

### 👨‍💼 Admin Panel
- **Statistics Dashboard**: Users, downloads, verified accounts tracking
- **User Management**: Ban/unban users
- **Session Management**: Monitor Instagram session status
- **Broadcast Messages**: Send messages to all users
- **Settings Control**: Configure bot behavior

### 🌍 Persian Interface
- **Farsi Messages**: Complete Persian language support
- **Intuitive Navigation**: Inline and reply keyboards
- **Progress Indicators**: Real-time download status
- **Helpful Errors**: Clear error messages with solutions

## 📋 Requirements

- **Python**: 3.10 or higher
- **FFmpeg**: For audio extraction
- **System**: Linux (Ubuntu/Debian recommended)
- **Storage**: At least 1GB free space
- **RAM**: Minimum 512MB

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/MATIN-X/MX-BOT.git
cd MX-BOT
```

### 2. Run Installer
```bash
./install.sh
```

The installer will:
- ✅ Check system requirements
- ✅ Install Python dependencies
- ✅ Configure bot settings
- ✅ Setup Instagram session
- ✅ Initialize database
- ✅ Create systemd service (optional)

### 3. Configuration

During installation, you'll be asked for:

1. **Telegram Bot Token**: Get from [@BotFather](https://t.me/BotFather)
2. **Admin Telegram ID**: Your numeric Telegram user ID
3. **Instagram Username**: Account for DM verification checks
4. **Instagram Password**: Password for the account

### 4. Instagram Session Setup

**Automatic Login** (Preferred):
- The installer tries automatic login
- If successful, you're ready to go!

**Manual Login** (If 2FA/Challenge):
If automatic login fails, follow these steps:

1. **On your local machine**, create `login_helper.py`:
```python
from instagrapi import Client

username = input("Instagram username: ")
password = input("Instagram password: ")

cl = Client()
try:
    cl.login(username, password)
    cl.dump_settings(f"{username}.json")
    print(f"✓ Success! Upload {username}.json to server")
except Exception as e:
    print(f"✗ Failed: {e}")
    if "two_factor" in str(e).lower():
        code = input("Enter 2FA code: ")
        cl.two_factor_login(username, password, code)
        cl.dump_settings(f"{username}.json")
```

2. **Run the script**:
```bash
python3 login_helper.py
```

3. **Upload session file** to server:
```bash
scp username.json user@server:/path/to/MX-BOT/sessions/
```

4. **Resume installation**:
```bash
./install.sh --continue
```

## 📁 Project Structure

```
MX-BOT/
├── install.sh              # Smart installation script
├── requirements.txt        # Python dependencies
├── config.py              # Configuration management
├── bot.py                 # Main bot with all handlers
├── database.py            # SQLite database operations
├── instagram_handler.py   # Instagram API wrapper
├── downloader.py          # Download manager with yt-dlp
├── keyboards.py           # Telegram keyboards (Persian)
├── messages.py            # Bot messages (Persian)
├── session_manager.py     # Instagram session management
├── utils.py               # Utility functions
├── sessions/              # Instagram session files (auto-created)
├── downloads/             # Temporary downloads (auto-created)
└── README.md              # This file
```

## 🎯 Usage

### For Users

1. **Start the bot**: `/start`
2. **Add Instagram account**: 
   - Click "افزودن حساب" (Add Account)
   - Enter your Instagram username
   - Send verification code to bot's Instagram DM
   - Click "بررسی تایید" (Check Verification)
3. **Download content**:
   - Click "دانلود" (Download)
   - Send Instagram link
   - Or forward post from Instagram app

### For Admins

- **Access panel**: Click "پنل مدیریت" (Admin Panel)
- **View stats**: See user and download statistics
- **Manage users**: Ban/unban users
- **Broadcast**: Send messages to all users
- **Manage sessions**: Check Instagram session status

## ⚙️ Systemd Service

If you installed the systemd service:

```bash
# Start bot
sudo systemctl start mx-bot

# Stop bot
sudo systemctl stop mx-bot

# Restart bot
sudo systemctl restart mx-bot

# View logs
sudo journalctl -u mx-bot -f

# Check status
sudo systemctl status mx-bot
```

## 🗄️ Database Schema

SQLite database with 5 tables:

- **users**: User information and statistics
- **instagram_accounts**: Verified Instagram accounts
- **downloads**: Download history
- **bot_sessions**: Instagram session management
- **pending_verifications**: Temporary verification codes

## 🔧 Configuration File

`config.ini` structure:
```ini
[Telegram]
bot_token = YOUR_BOT_TOKEN
admin_id = YOUR_TELEGRAM_ID

[Instagram]
username = instagram_username
password = instagram_password

[Paths]
database = bot.db
sessions = sessions
downloads = downloads
```

## 📝 Logging

Logs are stored in `bot.log` with rotating file handler:
- Application events
- Error tracking
- Download statistics
- Instagram API interactions

## 🛡️ Security Features

- **No Hardcoded Credentials**: All sensitive data in config.ini
- **Rate Limiting**: Prevents spam and Instagram blocks
- **Session Validation**: Regular session health checks
- **User Banning**: Admin can ban problematic users
- **Input Validation**: All user inputs are sanitized

## 🐛 Troubleshooting

### Bot won't start
```bash
# Check logs
sudo journalctl -u mx-bot -f

# Or if running manually
python3 bot.py
```

### Instagram session expired
```bash
# Delete old session
rm sessions/username.json

# Re-run installer
./install.sh --continue
```

### Database errors
```bash
# Reinitialize database
python3 -c "from database import db; db.init_database()"
```

### Download failures
- Verify Instagram session is active
- Check if post is public
- Ensure file size is under 50MB
- Try yt-dlp fallback

## 📦 Dependencies

Main dependencies (auto-installed):
- `python-telegram-bot==20.7` - Telegram Bot API
- `instagrapi==2.0.0` - Instagram API wrapper
- `yt-dlp` - Universal video downloader
- `aiohttp` - Async HTTP client
- `aiofiles` - Async file operations
- `Pillow` - Image processing
- `ffmpeg-python` - Video processing

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This bot is for educational purposes. Users are responsible for:
- Complying with Instagram's Terms of Service
- Respecting copyright and intellectual property
- Not using for commercial purposes without permission
- Following local laws and regulations

## 💡 Tips

1. **Regular Session Checks**: Monitor Instagram session health
2. **Disk Space**: Clean downloads folder regularly
3. **Rate Limits**: Don't spam downloads (5-second cooldown)
4. **Privacy**: Keep config.ini secure
5. **Updates**: Keep dependencies updated

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Contact: Admin via Telegram
- Check logs first: `sudo journalctl -u mx-bot -f`

## 🎉 Credits

Built with:
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [instagrapi](https://github.com/adw0rd/instagrapi)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)

---

**Made with ❤️ for the Instagram download community**
