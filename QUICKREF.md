# 📱 MX-BOT Quick Reference

## 🚀 Quick Setup

```bash
# 1. Clone repository
git clone https://github.com/MATIN-X/MX-BOT.git
cd MX-BOT

# 2. Run installer
./install.sh

# 3. Follow prompts for:
#    - Telegram Bot Token
#    - Admin ID
#    - Instagram credentials

# 4. Start bot
sudo systemctl start mx-bot
```

## 🎯 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and show main menu |
| `/help` | Show help and usage instructions |
| `/stats` | View your statistics |

## 🔘 Main Menu Buttons

| Button (Persian) | English | Function |
|-----------------|---------|----------|
| 📥 دانلود | Download | Start download process |
| 📱 حساب‌های من | My Accounts | Manage Instagram accounts |
| 📊 آمار | Statistics | View your stats |
| ❓ راهنما | Help | Show help |
| 👨‍💼 پنل مدیریت | Admin Panel | Admin only |

## 📥 Downloading Content

### Method 1: Direct Link
1. Click "📥 دانلود"
2. Paste Instagram URL
3. Wait for download

### Method 2: Forward Post
1. In Instagram app, click Share
2. Forward to bot
3. Wait for download

### Supported URLs
- Posts: `instagram.com/p/CODE`
- Reels: `instagram.com/reel/CODE`
- IGTV: `instagram.com/tv/CODE`
- Stories: `instagram.com/stories/USER/ID`

## 👤 Account Verification

### First Time Setup
1. Click "📱 حساب‌های من" (My Accounts)
2. Click "➕ افزودن حساب" (Add Account)
3. Enter your Instagram username (without @)
4. You'll receive a verification code like: `AB12CD34`

### Sending Verification Code
1. Open Instagram app
2. Go to bot's Instagram profile
3. Send the code as a Direct Message
4. Return to Telegram bot
5. Click "🔍 بررسی تایید" (Check Verification)

### Verification Tips
- ✅ Code is valid for 30 minutes
- ✅ Make sure you DM the exact code
- ✅ Code is case-sensitive
- ✅ You can add multiple accounts

## 👨‍💼 Admin Functions

### Access Admin Panel
Click "👨‍💼 پنل مدیریت" (Admin Panel)

### Admin Options
- **📊 آمار**: View bot statistics
- **👥 مدیریت کاربران**: Manage users (ban/unban)
- **🔑 مدیریت نشست‌ها**: Manage Instagram sessions
- **📢 ارسال پیام همگانی**: Broadcast message to all users
- **⚙️ تنظیمات**: Bot settings

## 🛠️ Maintenance

### Check Bot Status
```bash
sudo systemctl status mx-bot
```

### View Logs
```bash
# Live logs
sudo journalctl -u mx-bot -f

# Last 100 lines
sudo journalctl -u mx-bot -n 100
```

### Restart Bot
```bash
sudo systemctl restart mx-bot
```

### Update Bot
```bash
cd /path/to/MX-BOT
git pull
pip3 install -r requirements.txt --upgrade
sudo systemctl restart mx-bot
```

### Clean Downloads
```bash
# Manually clean old files
cd downloads
rm -f *

# Or in Python
python3 -c "from downloader import downloader; downloader.cleanup_old_files(24)"
```

## ⚠️ Troubleshooting

### Bot Not Responding
```bash
# Check if running
sudo systemctl status mx-bot

# Check logs for errors
sudo journalctl -u mx-bot -n 50
```

### Instagram Session Expired
```bash
# Re-run installer
./install.sh --continue
```

### Database Issues
```bash
# Backup database
cp bot.db bot.db.backup

# Reinitialize if needed
python3 -c "from database import db; db.init_database()"
```

### Download Failures
- Check Instagram session is valid
- Verify post is public
- Ensure file size < 50MB
- Check internet connection

## 📊 File Locations

| File | Path | Description |
|------|------|-------------|
| Config | `config.ini` | Bot configuration |
| Database | `bot.db` | SQLite database |
| Logs | `bot.log` | Application logs |
| Sessions | `sessions/*.json` | Instagram sessions |
| Downloads | `downloads/*` | Temporary downloads |

## 🔐 Security Tips

1. **Protect config.ini**
   ```bash
   chmod 600 config.ini
   ```

2. **Regular backups**
   ```bash
   # Backup database
   cp bot.db backups/bot.db.$(date +%Y%m%d)
   ```

3. **Monitor logs**
   ```bash
   # Watch for suspicious activity
   tail -f bot.log
   ```

4. **Keep updated**
   ```bash
   # Update dependencies monthly
   pip3 install -r requirements.txt --upgrade
   ```

## 💡 Pro Tips

- **Rate Limits**: Wait 5 seconds between downloads
- **Large Files**: Files over 50MB will be rejected
- **Multiple Accounts**: Add backup Instagram account
- **Session Health**: Check session status weekly
- **Cleanup**: Run cleanup monthly for disk space

## 📞 Support

- 🐛 **Bug Reports**: Open GitHub issue
- 💬 **Questions**: Check README.md first
- 📧 **Contact**: Via Telegram admin

## 📚 Additional Resources

- [Full Documentation](README.md)
- [Installation Guide](README.md#quick-start)
- [Contributing Guide](CONTRIBUTING.md)
- [License](LICENSE)

---

**Made with ❤️ by MATIN-X**
