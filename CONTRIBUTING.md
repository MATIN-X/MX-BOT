# Contributing to MX-BOT

Thank you for considering contributing to MX-BOT! 

## 🐛 Bug Reports

If you find a bug, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Relevant logs or error messages

## ✨ Feature Requests

For feature requests, please:
- Check if it's already been suggested
- Provide clear use case
- Explain expected behavior
- Consider implementation complexity

## 🔧 Pull Requests

### Before Submitting

1. **Test your changes**
   ```bash
   python3 test_bot.py
   ```

2. **Follow code style**
   - Use Python PEP 8 style guide
   - Add docstrings to functions
   - Keep functions focused and small
   - Add comments for complex logic

3. **Update documentation**
   - Update README.md if needed
   - Add comments to new code
   - Update example config if adding settings

### Submitting PR

1. Fork the repository
2. Create a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Make your changes
   - Write clean, readable code
   - Add tests if applicable
   - Ensure all tests pass

4. Commit with clear messages
   ```bash
   git commit -m "Add feature: description"
   ```

5. Push and create PR
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 Code Guidelines

### Python Style
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use meaningful variable names
- Add type hints where appropriate

### Comments
```python
def function_name(param: str) -> bool:
    """
    Brief description
    
    Args:
        param: Parameter description
    
    Returns:
        Return value description
    """
    # Implementation comments
    pass
```

### Error Handling
- Always use try-except for external APIs
- Log errors appropriately
- Provide user-friendly error messages

### Database Operations
- Always close connections
- Use transactions for multiple operations
- Sanitize all inputs

### Security
- Never commit credentials
- Validate all user inputs
- Use rate limiting
- Keep dependencies updated

## 🧪 Testing

Run tests before submitting:
```bash
python3 test_bot.py
```

Add tests for new features:
```python
def test_new_feature():
    """Test description"""
    # Test implementation
    assert expected == actual
```

## 📋 Checklist

Before submitting PR:
- [ ] Tests pass
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No credentials in code
- [ ] Error handling added
- [ ] Logging added where appropriate

## 🤝 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn
- Focus on the code, not the person

## 📞 Questions?

Feel free to:
- Open an issue for questions
- Join discussions in issues
- Ask for clarification in PRs

Thank you for contributing! 🎉
