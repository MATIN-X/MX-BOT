#!/bin/bash

# MX-BOT Installation Script
# Smart installer for Instagram Download Telegram Bot

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_color() {
    color=$1
    shift
    echo -e "${color}$@${NC}"
}

print_header() {
    echo ""
    print_color "$BLUE" "================================"
    print_color "$BLUE" "$1"
    print_color "$BLUE" "================================"
    echo ""
}

print_success() {
    print_color "$GREEN" "✓ $1"
}

print_error() {
    print_color "$RED" "✗ $1"
}

print_warning() {
    print_color "$YELLOW" "⚠ $1"
}

print_info() {
    print_color "$BLUE" "ℹ $1"
}

# Check if running with --continue flag
CONTINUE_MODE=false
if [ "$1" == "--continue" ]; then
    CONTINUE_MODE=true
    print_info "Resuming installation..."
fi

# Step 1: Welcome
if [ "$CONTINUE_MODE" = false ]; then
    clear
    print_header "MX-BOT Installer"
    print_info "Instagram Download Telegram Bot"
    echo ""
    print_info "This installer will guide you through the setup process."
    echo ""
    read -p "Press Enter to continue..."
fi

# Step 2: Check system requirements
print_header "Checking System Requirements"

# Check Python version
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed!"
    print_info "Please install Python 3.10 or higher and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_success "Python $PYTHON_VERSION found"

# Check pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed!"
    print_info "Installing pip3..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi
print_success "pip3 found"

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    print_warning "ffmpeg not found"
    print_info "Installing ffmpeg..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y ffmpeg
    elif command -v yum &> /dev/null; then
        sudo yum install -y ffmpeg
    else
        print_error "Could not install ffmpeg. Please install it manually."
        exit 1
    fi
fi
print_success "ffmpeg found"

# Step 3: Install Python dependencies
if [ "$CONTINUE_MODE" = false ]; then
    print_header "Installing Python Dependencies"
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    print_info "Installing packages..."
    pip3 install -r requirements.txt --upgrade
    print_success "Dependencies installed"
fi

# Step 4: Configuration
print_header "Bot Configuration"

if [ -f "config.ini" ] && [ "$CONTINUE_MODE" = false ]; then
    print_warning "config.ini already exists!"
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        print_info "Skipping configuration..."
    else
        rm config.ini
    fi
fi

if [ ! -f "config.ini" ]; then
    print_info "Let's configure your bot..."
    echo ""
    
    # Get Telegram Bot Token
    while true; do
        read -p "Enter your Telegram Bot Token: " BOT_TOKEN
        
        # Validate token format
        if [[ $BOT_TOKEN =~ ^[0-9]+:[A-Za-z0-9_-]{35}$ ]]; then
            print_success "Valid token format"
            break
        else
            print_error "Invalid token format! Expected format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        fi
    done
    
    # Get Admin ID
    while true; do
        read -p "Enter your Telegram Admin ID (numeric): " ADMIN_ID
        
        if [[ $ADMIN_ID =~ ^[0-9]+$ ]]; then
            print_success "Valid admin ID"
            break
        else
            print_error "Invalid admin ID! Must be numeric."
        fi
    done
    
    # Get Instagram credentials
    echo ""
    print_info "Instagram Account Configuration"
    print_warning "This account will be used to check DMs for verification codes."
    echo ""
    
    read -p "Instagram Username: " IG_USERNAME
    read -sp "Instagram Password: " IG_PASSWORD
    echo ""
    
    # Save config
    cat > config.ini << EOF
[Telegram]
bot_token = $BOT_TOKEN
admin_id = $ADMIN_ID

[Instagram]
username = $IG_USERNAME
password = $IG_PASSWORD

[Paths]
database = bot.db
sessions = sessions
downloads = downloads
EOF
    
    print_success "Configuration saved to config.ini"
fi

# Step 5: Instagram Login
print_header "Instagram Session Setup"

# Check if session already exists
SESSION_FILE="sessions/${IG_USERNAME}.json"
if [ -f "$SESSION_FILE" ]; then
    print_success "Instagram session file found!"
    
    # Validate session
    print_info "Validating session..."
    python3 << EOF
import sys
sys.path.insert(0, '.')
from session_manager import session_manager
from config import config

config.load()

if session_manager.validate_session(config.instagram_username):
    print("Session is valid!")
    sys.exit(0)
else:
    print("Session is invalid or expired!")
    sys.exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        print_success "Session validated successfully!"
    else
        print_warning "Session validation failed. Attempting login..."
        rm "$SESSION_FILE"
    fi
fi

if [ ! -f "$SESSION_FILE" ] || [ "$CONTINUE_MODE" = true ]; then
    print_info "Attempting to login to Instagram..."
    
    # Try automatic login
    python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from session_manager import session_manager
from config import config

config.load()

print(f"Logging in as {config.instagram_username}...")
success, message, client = session_manager.login(
    config.instagram_username,
    config.instagram_password
)

if success:
    print("Login successful!")
    sys.exit(0)
else:
    print(f"Login failed: {message}")
    sys.exit(1)
EOF
    
    LOGIN_RESULT=$?
    
    if [ $LOGIN_RESULT -eq 0 ]; then
        print_success "Instagram login successful!"
    else
        print_error "Automatic Instagram login failed!"
        echo ""
        print_warning "Manual Session Setup Required"
        echo ""
        print_info "To set up your Instagram session manually:"
        echo ""
        print_color "$YELLOW" "1. On your LOCAL machine, create a file 'login_helper.py' with this content:"
        echo ""
        cat << 'PYCODE'
from instagrapi import Client
import sys

username = input("Instagram username: ")
password = input("Instagram password: ")

cl = Client()
try:
    cl.login(username, password)
    cl.dump_settings(f"{username}.json")
    print(f"\n✓ Success! Session saved to {username}.json")
    print(f"Upload this file to your server at: sessions/{username}.json")
except Exception as e:
    print(f"\n✗ Login failed: {e}")
    
    if "two_factor" in str(e).lower():
        code = input("Enter 2FA code: ")
        try:
            cl.two_factor_login(username, password, code)
            cl.dump_settings(f"{username}.json")
            print(f"\n✓ Success! Session saved to {username}.json")
        except Exception as e2:
            print(f"\n✗ Failed: {e2}")
PYCODE
        echo ""
        print_color "$YELLOW" "2. Run: python3 login_helper.py"
        print_color "$YELLOW" "3. Upload the generated session file to: $SCRIPT_DIR/sessions/"
        print_color "$YELLOW" "4. Run this installer again with: ./install.sh --continue"
        echo ""
        exit 1
    fi
fi

# Step 6: Initialize Database
print_header "Initializing Database"

python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from database import db

print("Creating database tables...")
db.init_database()
print("Database initialized!")
EOF

print_success "Database initialized"

# Step 7: Create systemd service
print_header "Setting up Systemd Service"

read -p "Do you want to create a systemd service for auto-start? (Y/n): " create_service
if [ "$create_service" != "n" ] && [ "$create_service" != "N" ]; then
    
    SERVICE_FILE="/etc/systemd/system/mx-bot.service"
    
    print_info "Creating systemd service..."
    
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=MX-BOT Instagram Download Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$(which python3) $SCRIPT_DIR/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    print_success "Service file created at $SERVICE_FILE"
    
    # Reload systemd
    sudo systemctl daemon-reload
    print_success "Systemd reloaded"
    
    # Enable service
    sudo systemctl enable mx-bot
    print_success "Service enabled for auto-start"
    
    # Ask to start now
    read -p "Do you want to start the bot now? (Y/n): " start_now
    if [ "$start_now" != "n" ] && [ "$start_now" != "N" ]; then
        sudo systemctl start mx-bot
        print_success "Bot started!"
        
        sleep 2
        
        # Check status
        if sudo systemctl is-active --quiet mx-bot; then
            print_success "Bot is running!"
        else
            print_error "Bot failed to start. Check logs with: sudo journalctl -u mx-bot -f"
        fi
    fi
    
    echo ""
    print_info "Useful commands:"
    print_color "$BLUE" "  Start bot:   sudo systemctl start mx-bot"
    print_color "$BLUE" "  Stop bot:    sudo systemctl stop mx-bot"
    print_color "$BLUE" "  Restart bot: sudo systemctl restart mx-bot"
    print_color "$BLUE" "  View logs:   sudo journalctl -u mx-bot -f"
    print_color "$BLUE" "  Check status: sudo systemctl status mx-bot"
else
    print_info "Skipping systemd service creation"
    print_info "You can start the bot manually with: python3 bot.py"
fi

# Final message
echo ""
print_header "Installation Complete!"
echo ""
print_success "MX-BOT has been installed successfully!"
echo ""
print_info "Configuration file: config.ini"
print_info "Database: bot.db"
print_info "Sessions: sessions/"
print_info "Downloads: downloads/"
echo ""
print_color "$GREEN" "🎉 Your bot is ready to use!"
echo ""
