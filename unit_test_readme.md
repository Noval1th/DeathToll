# 🧪 Unit Testing Guide

## 📋 Overview

The test suite covers all major functionality of the Discord Stats Tracker:

- ✅ Helper functions (time formatting, ordinals, emojis)
- ✅ Player initialization and stats tracking
- ✅ Event handlers (death, respawn, level-up, login)
- ✅ Discord event routing
- ✅ Stats file persistence
- ✅ Discord notification formatting
- ✅ Leaderboard generation
- ✅ FTP operations

## 🚀 Running the Tests

### Prerequisites

```bash
pip install requests  # Only external dependency needed
```

### Run All Tests

```bash
python test_main.py
```

### Run with Verbose Output

```bash
python test_main.py -v
```

### Run Specific Test Class

```bash
python -m unittest test_main.TestHelperFunctions
```

### Run Specific Test Method

```bash
python -m unittest test_main.TestHelperFunctions.test_format_time_hours_only
```

### Run with Coverage (Optional)

```bash
pip install coverage

# Run tests with coverage
coverage run -m unittest test_main.py

# View coverage report
coverage report

# Generate HTML coverage report
coverage html
# Then open htmlcov/index.html in browser
```

## 📊 Test Coverage

### TestHelperFunctions
- `format_time()` - All edge cases (hours, days, singular/plural)
- `get_death_ordinal()` - Ordinal suffixes (1st, 2nd, 3rd, 11th-13th, 21st)
- `get_death_emoji()` - Death count emoji selection
- `parse_skills_string()` - Skill parsing with various formats

### TestPlayerInitialization
- New player creation
- Existing player preservation

### TestEventHandlers
- Death events (single, multiple, longest survival tracking)
- Spawn events
- Level-up events (milestone vs all notifications)
- Login events

### TestDiscordEventRouting
- Event type routing (death, level_up, sunrise, daily_survivors)
- Correct handler invocation

### TestStatsFilePersistence
- Saving player stats to JSON
- Loading player stats from JSON
- Handling missing files

### TestDiscordNotifications
- Death notification formatting
- Respawn notification formatting
- Sunrise notification formatting

### TestLeaderboards
- Death leaderboard sorting
- Survival leaderboard sorting
- Hours leaderboard sorting
- Skill-specific leaderboards

### TestFTPOperations
- Downloading new content
- Handling unchanged files
- Detecting log rotation

## 🎯 Expected Output

```
test_format_time_days_and_hours (test_main.TestHelperFunctions) ... ok
test_format_time_hours_only (test_main.TestHelperFunctions) ... ok
test_format_time_multiple_days (test_main.TestHelperFunctions) ... ok
test_format_time_single_hour (test_main.TestHelperFunctions) ... ok
test_get_death_emoji (test_main.TestHelperFunctions) ... ok
test_get_death_ordinal_first (test_main.TestHelperFunctions) ... ok
test_get_death_ordinal_fourth (test_main.TestHelperFunctions) ... ok
test_get_death_ordinal_second (test_main.TestHelperFunctions) ... ok
test_get_death_ordinal_teens (test_main.TestHelperFunctions) ... ok
test_get_death_ordinal_third (test_main.TestHelperFunctions) ... ok
test_get_death_ordinal_twenty_first (test_main.TestHelperFunctions) ... ok
test_parse_skills_string_empty (test_main.TestHelperFunctions) ... ok
test_parse_skills_string_multiple_skills (test_main.TestHelperFunctions) ... ok
test_parse_skills_string_single_skill (test_main.TestHelperFunctions) ... ok
test_parse_skills_string_with_spaces (test_main.TestHelperFunctions) ... ok
...

----------------------------------------------------------------------
Ran 40 tests in 0.123s

OK
```

## 🐛 Test-Driven Development Workflow

### Adding New Features

1. **Write the test first:**
```python
def test_new_feature(self):
    """Test that new feature works"""
    result = main.new_feature("input")
    self.assertEqual(result, "expected_output")
```

2. **Run test (it should fail):**
```bash
python -m unittest test_main.TestClassName.test_new_feature
```

3. **Implement the feature in main.py**

4. **Run test again (should pass)**

5. **Refactor if needed, tests keep you safe**

## 🔍 Mock Usage Examples

### Mocking Discord Webhooks

```python
@patch('main.send_discord_notification')
def test_my_function(self, mock_send):
    """Test without actually calling Discord"""
    main.my_function()
    mock_send.assert_called_once()
```

### Mocking FTP Connections

```python
@patch('ftplib.FTP')
def test_ftp_operation(self, mock_ftp_class):
    """Test FTP without actual connection"""
    mock_ftp = MagicMock()
    mock_ftp.size.return_value = 1024
    # Test logic here
```

### Mocking File I/O

```python
@patch('builtins.open', new_callable=mock_open, read_data='{"test": "data"}')
def test_file_read(self, mock_file):
    """Test file operations without touching disk"""
    # Test logic here
```

## ⚠️ Common Testing Pitfalls

### 1. **Not Resetting State**
```python
def setUp(self):
    """Always reset global state before each test"""
    main.player_stats = {}
    main.unsaved_changes = False
    main.last_events = set()
```

### 2. **Testing Implementation Instead of Behavior**
❌ **Bad:**
```python
def test_death_increments_counter(self):
    # Testing internal implementation
    self.assertEqual(player['_death_counter'], 1)
```

✅ **Good:**
```python
def test_death_event_tracked(self):
    # Testing observable behavior
    main.handle_death_event(data)
    self.assertEqual(main.player_stats['Player']['total_deaths'], 1)
```

### 3. **Not Using Mocks for External Dependencies**
❌ **Bad:**
```python
def test_send_notification(self):
    # Actually calls Discord API
    result = main.send_death_notification(...)
```

✅ **Good:**
```python
@patch('main.send_discord_notification')
def test_send_notification(self, mock_send):
    # Mocked, no actual API call
    result = main.send_death_notification(...)
    mock_send.assert_called_once()
```

### 4. **Brittle Assertions**
❌ **Bad:**
```python
self.assertEqual(embed['description'], 
    "⏱️ **Survived:** 1 day, 0 hours\n📍 **Location:** (100, 200, 0)")
```

✅ **Good:**
```python
self.assertIn("Survived:", embed['description'])
self.assertIn("(100, 200, 0)", embed['description'])
```

## 🔧 Continuous Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install requests coverage
    
    - name: Run tests
      run: |
        coverage run -m unittest test_main.py
    
    - name: Generate coverage report
      run: |
        coverage report
        coverage xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 📈 Testing Best Practices

### 1. **Arrange-Act-Assert Pattern**
```python
def test_player_death_updates_stats(self):
    # Arrange - Set up test data
    event_data = {'username': 'Player', 'hours_survived': 10.0, ...}
    
    # Act - Execute the function
    main.handle_death_event(event_data)
    
    # Assert - Verify the results
    self.assertEqual(main.player_stats['Player']['total_deaths'], 1)
```

### 2. **Test One Thing Per Test**
❌ **Bad:**
```python
def test_everything(self):
    # Tests death, respawn, level-up all at once
    main.handle_death_event(...)
    main.handle_spawn_event(...)
    main.handle_level_up_event(...)
    # Too much!
```

✅ **Good:**
```python
def test_death_increments_counter(self):
    main.handle_death_event(...)
    self.assertEqual(player['total_deaths'], 1)

def test_spawn_marks_alive(self):
    main.handle_spawn_event(...)
    self.assertTrue(player['current_character']['alive'])
```

### 3. **Use Descriptive Test Names**
❌ **Bad:** `test_1()`, `test_death()`, `test_function()`

✅ **Good:** 
- `test_death_event_updates_longest_survival()`
- `test_level_up_notification_sent_at_milestone()`
- `test_leaderboard_sorts_by_death_count_descending()`

### 4. **Test Edge Cases**
```python
def test_format_time_zero_hours(self):
    """Edge case: 0 hours"""
    result = main.format_time(0)
    self.assertEqual(result, "0 hours")

def test_format_time_fractional_hours(self):
    """Edge case: fractional hours"""
    result = main.format_time(24.7)
    self.assertEqual(result, "1 day, 0 hours")

def test_parse_skills_string_malformed(self):
    """Edge case: malformed input"""
    result = main.parse_skills_string("Aiming5,Fitness")
    # Should handle gracefully
```

## 🎯 Integration Testing

For full end-to-end testing, create a separate test file:

```python
# test_integration.py
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock
import main

class TestEndToEnd(unittest.TestCase):
    """Test complete workflows"""
    
    @patch('main.send_discord_notification')
    @patch('ftplib.FTP')
    def test_complete_death_workflow(self, mock_ftp_class, mock_discord):
        """Test from FTP read to Discord notification"""
        # Setup mock FTP
        mock_ftp = MagicMock()
        mock_ftp_class.return_value = mock_ftp
        mock_ftp.size.return_value = 100
        
        # Mock log content
        log_content = json.dumps({
            'timestamp': '2025-01-15 10:00:00',
            'type': 'death',
            'data': {
                'username': 'TestPlayer',
                'steam_id': '12345',
                'hours_survived': 24.5,
                'x': 100, 'y': 200, 'z': 0,
                'skills': 'Aiming=5'
            }
        }) + '\n'
        
        def mock_retrbinary(cmd, callback, rest=0):
            callback(log_content.encode())
        mock_ftp.retrbinary = mock_retrbinary
        
        # Execute
        main.monitor_discord_events_log(mock_ftp)
        
        # Verify entire workflow
        self.assertIn('TestPlayer', main.player_stats)
        self.assertEqual(main.player_stats['TestPlayer']['total_deaths'], 1)
        mock_discord.assert_called()
```

## 📝 Test Maintenance Checklist

- [ ] All tests pass before committing
- [ ] New features have corresponding tests
- [ ] Tests are independent (can run in any order)
- [ ] Mocks are used for external dependencies
- [ ] Edge cases are covered
- [ ] Test names are descriptive
- [ ] Setup/teardown cleans up properly
- [ ] No hardcoded paths or credentials in tests
- [ ] Tests run fast (< 1 second each)

## 🚨 Debugging Failed Tests

### 1. **Run Single Test with Print Statements**
```python
def test_my_feature(self):
    result = main.my_function(input_data)
    print(f"DEBUG: Result = {result}")  # Add debug output
    self.assertEqual(result, expected)
```

Run with:
```bash
python -m unittest test_main.TestClass.test_my_feature -v
```

### 2. **Use Python Debugger**
```python
def test_my_feature(self):
    import pdb; pdb.set_trace()  # Breakpoint
    result = main.my_function(input_data)
    self.assertEqual(result, expected)
```

### 3. **Check Mock Call Arguments**
```python
@patch('main.send_discord_notification')
def test_notification(self, mock_send):
    main.send_death_notification(...)
    
    # Debug what was actually called
    print(f"Called: {mock_send.called}")
    print(f"Call count: {mock_send.call_count}")
    print(f"Call args: {mock_send.call_args}")
```

## 🎓 Additional Resources

- [Python unittest documentation](https://docs.python.org/3/library/unittest.html)
- [unittest.mock guide](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)
- [Python Testing with pytest](https://pragprog.com/titles/bopytest/python-testing-with-pytest/) (Alternative to unittest)

## 💡 Quick Reference

### Common Assertions
```python
self.assertEqual(a, b)           # a == b
self.assertNotEqual(a, b)        # a != b
self.assertTrue(x)               # bool(x) is True
self.assertFalse(x)              # bool(x) is False
self.assertIs(a, b)              # a is b
self.assertIsNone(x)             # x is None
self.assertIn(a, b)              # a in b
self.assertIsInstance(a, b)      # isinstance(a, b)
self.assertGreater(a, b)         # a > b
self.assertAlmostEqual(a, b)     # round(a-b, 7) == 0
```

### Common Mock Assertions
```python
mock.assert_called()             # Called at least once
mock.assert_called_once()        # Called exactly once
mock.assert_called_with(args)    # Last call was with these args
mock.assert_called_once_with(a)  # Called once with these args
mock.assert_not_called()         # Never called
mock.call_count                  # Number of times called
mock.call_args                   # Args from last call
mock.call_args_list              # List of all calls
```

### Running Tests Summary
```bash
# All tests
python test_main.py

# Verbose
python test_main.py -v

# Specific class
python -m unittest test_main.TestHelperFunctions

# Specific test
python -m unittest test_main.TestHelperFunctions.test_format_time

# With coverage
coverage run -m unittest test_main.py
coverage report
```

---

**Happy Testing! 🧪✨**
