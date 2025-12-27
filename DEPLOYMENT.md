# 🚀 Deployment Guide for MX-BOT

## Quick Start

### One-Line Installation
```bash
git clone https://github.com/MATIN-X/MX-BOT.git && cd MX-BOT && ./install.sh
```

## Requirements
- Ubuntu 20.04+ / Debian 10+
- Python 3.10+
- 512MB RAM minimum
- 1GB free storage

## Installation Steps

1. **Clone Repository**
   ```bash
   git clone https://github.com/MATIN-X/MX-BOT.git
   cd MX-BOT
   ```

2. **Run Installer**
   ```bash
   ./install.sh
   ```

3. **Provide Configuration**
   - Telegram Bot Token (from @BotFather)
   - Admin Telegram ID
   - Instagram username and password

4. **Verify Installation**
   ```bash
   sudo systemctl status mx-bot
   ```

## Management Commands

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

## Updating

```bash
cd /path/to/MX-BOT
sudo systemctl stop mx-bot
git pull
pip3 install -r requirements.txt --upgrade
sudo systemctl start mx-bot
```

## Troubleshooting

### Bot won't start
```bash
# Check logs
sudo journalctl -u mx-bot -n 50

# Test manually
python3 bot.py
```

### Session expired
```bash
./install.sh --continue
```

### Database issues
```bash
cp bot.db bot.db.backup
python3 -c "from database import db; db.init_database()"
```

## Security

```bash
# Protect config
chmod 600 config.ini

# Setup backups
tar -czf backup.tar.gz config.ini bot.db sessions/
```

## Monitoring

```bash
# Watch logs
sudo journalctl -u mx-bot -f

# Check disk space
du -sh downloads/

# Monitor service
systemctl is-active mx-bot
```

For detailed deployment instructions, see [README.md](README.md)
