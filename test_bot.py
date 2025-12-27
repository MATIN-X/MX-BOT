#!/usr/bin/env python3
"""
Test script for MX-BOT
Validates basic functionality without external dependencies
"""
import sys
import os

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    
    modules = [
        'config', 'database', 'messages', 'utils'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ✗ {module}: {e}")
            return False
    
    return True

def test_utils():
    """Test utility functions"""
    print("\nTesting utility functions...")
    
    from utils import (
        generate_verification_code,
        extract_instagram_url,
        extract_media_url,
        is_instagram_url,
        is_ytdlp_supported_url,
        is_valid_instagram_username,
        format_number,
        sanitize_filename
    )
    
    # Test verification code
    code = generate_verification_code(8)
    if len(code) != 8:
        print(f"  ✗ Verification code length: expected 8, got {len(code)}")
        return False
    print(f"  ✓ Verification code: {code}")
    
    # Test URL extraction
    test_url = "Check https://instagram.com/p/ABC123/ out"
    extracted = extract_instagram_url(test_url)
    if not extracted:
        print("  ✗ URL extraction failed")
        return False
    print(f"  ✓ URL extraction: {extracted}")
    
    # Test media URL extraction
    youtube_test = "Check out https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    youtube_url = extract_media_url(youtube_test)
    if not youtube_url or 'youtube.com' not in youtube_url:
        print("  ✗ Media URL extraction failed")
        return False
    print(f"  ✓ Media URL extraction: {youtube_url}")
    
    # Test is_instagram_url
    if not is_instagram_url("https://instagram.com/p/ABC123/"):
        print("  ✗ is_instagram_url failed for Instagram URL")
        return False
    if is_instagram_url("https://youtube.com/watch?v=abc"):
        print("  ✗ is_instagram_url incorrectly accepted YouTube URL")
        return False
    # Security test: Malicious URL should not match
    if is_instagram_url("https://malicious-instagram.com.evil.com/"):
        print("  ✗ is_instagram_url security issue: accepted malicious URL")
        return False
    print("  ✓ is_instagram_url")
    
    # Test is_ytdlp_supported_url
    if not is_ytdlp_supported_url("https://youtube.com/watch?v=abc"):
        print("  ✗ is_ytdlp_supported_url failed for YouTube")
        return False
    if not is_ytdlp_supported_url("https://soundcloud.com/test/track"):
        print("  ✗ is_ytdlp_supported_url failed for SoundCloud")
        return False
    if is_ytdlp_supported_url("https://instagram.com/p/ABC123/"):
        print("  ✗ is_ytdlp_supported_url incorrectly accepted Instagram")
        return False
    # Security test: Malicious URL should not match
    if is_ytdlp_supported_url("https://malicious-youtube.com.evil.com/"):
        print("  ✗ is_ytdlp_supported_url security issue: accepted malicious URL")
        return False
    # Test subdomain support
    if not is_ytdlp_supported_url("https://music.youtube.com/watch?v=abc"):
        print("  ✗ is_ytdlp_supported_url failed for YouTube Music subdomain")
        return False
    print("  ✓ is_ytdlp_supported_url")
    
    # Test username validation
    if not is_valid_instagram_username("valid_user"):
        print("  ✗ Valid username rejected")
        return False
    if is_valid_instagram_username("@invalid"):
        print("  ✗ Invalid username accepted")
        return False
    print("  ✓ Username validation")
    
    # Test number formatting
    if format_number(1500) != "1.5K":
        print(f"  ✗ Number formatting: expected '1.5K', got '{format_number(1500)}'")
        return False
    print("  ✓ Number formatting")
    
    # Test filename sanitization
    dirty = "file<>name?.txt"
    clean = sanitize_filename(dirty)
    if '<' in clean or '>' in clean or '?' in clean:
        print(f"  ✗ Filename sanitization failed: {clean}")
        return False
    print("  ✓ Filename sanitization")
    
    return True

def test_database():
    """Test database operations"""
    print("\nTesting database operations...")
    
    from database import Database
    from datetime import datetime, timedelta
    
    # Create test database
    test_db_path = 'test_validation.db'
    db = Database(test_db_path)
    
    try:
        # Test user operations
        db.add_user(99999, 'testuser', 'Test User')
        user = db.get_user(99999)
        if not user or user['username'] != 'testuser':
            print("  ✗ User add/get failed")
            return False
        print("  ✓ User operations")
        
        # Test Instagram account
        expires = datetime.now() + timedelta(hours=1)
        acc_id = db.add_instagram_account(99999, 'ig_user', 'CODE123', expires)
        if not acc_id:
            print("  ✗ Instagram account creation failed")
            return False
        print("  ✓ Instagram account operations")
        
        # Test verification
        db.verify_instagram_account(acc_id)
        acc = db.get_instagram_account(acc_id)
        if acc['is_verified'] != 1:
            print("  ✗ Account verification failed")
            return False
        print("  ✓ Account verification")
        
        # Test download recording
        db.add_download(99999, 'post', 'https://instagram.com/p/test', 'ig_user', 2048)
        downloads = db.get_user_downloads(99999)
        if len(downloads) != 1:
            print("  ✗ Download recording failed")
            return False
        print("  ✓ Download recording")
        
        # Test statistics
        stats = {
            'users': db.get_total_users(),
            'downloads': db.get_total_downloads(),
            'verified': db.get_total_verified_accounts()
        }
        print(f"  ✓ Statistics: {stats}")
        
    finally:
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        print("  ✓ Cleanup completed")
    
    return True

def test_messages():
    """Test messages module"""
    print("\nTesting messages...")
    
    from messages import messages
    
    required_messages = [
        'WELCOME', 'HELP', 'MAIN_MENU', 'ADD_ACCOUNT',
        'VERIFICATION_CODE_SENT', 'VERIFICATION_SUCCESS',
        'DOWNLOAD_SUCCESS', 'DOWNLOAD_FAILED'
    ]
    
    for msg in required_messages:
        if not hasattr(messages, msg):
            print(f"  ✗ Missing message: {msg}")
            return False
    
    print(f"  ✓ All {len(required_messages)} required messages present")
    
    return True

def test_config():
    """Test configuration module"""
    print("\nTesting configuration...")
    
    from config import Config
    
    # Create test config
    test_config = Config('test_config.ini')
    test_config.bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    test_config.admin_id = 12345
    test_config.instagram_username = "test_user"
    test_config.instagram_password = "test_pass"
    
    # Save
    test_config.save()
    
    # Load
    test_config2 = Config('test_config.ini')
    test_config2.load()
    
    if test_config2.bot_token != test_config.bot_token:
        print("  ✗ Config save/load failed")
        return False
    
    print("  ✓ Config save/load")
    
    # Validate
    valid, errors = test_config2.validate()
    if not valid:
        print(f"  ✗ Config validation failed: {errors}")
        return False
    
    print("  ✓ Config validation")
    
    # Cleanup
    if os.path.exists('test_config.ini'):
        os.remove('test_config.ini')
    
    return True

def main():
    """Run all tests"""
    print("=" * 50)
    print("MX-BOT Validation Tests")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Utility Functions", test_utils),
        ("Database Operations", test_database),
        ("Messages", test_messages),
        ("Configuration", test_config),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 50)
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
