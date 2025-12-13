# Testing Guide for Masto-RSS

This document describes the testing strategy and how to run tests for the Masto-RSS bot.

## Test Architecture

The test suite is organized into two main categories:

### Unit Tests ([test_bot.py](test_bot.py))
- Test individual functions and methods in isolation
- Use mocks and stubs for external dependencies
- Fast execution time
- High code coverage
- Test edge cases and error handling

### Integration Tests ([test_integration.py](test_integration.py))
- Test interactions between components
- Mock external services (RSS feeds, Mastodon API)
- Test end-to-end workflows
- Verify data persistence
- Test error recovery

## Running Tests Locally

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements-test.txt
```

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=bot --cov=main --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest test_bot.py

# Run only integration tests
pytest test_integration.py

# Run tests matching a pattern
pytest -k "test_parse_feed"
```

### Run with Markers

```bash
# Run only unit tests (using markers)
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=bot --cov=main --cov-report=html

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## GitHub Actions CI/CD

Tests run automatically on every push to `main` and on all pull requests via [.github/workflows/test.yml](.github/workflows/test.yml).

### Test Jobs

1. **Unit Tests**
   - Runs on Python 3.10, 3.11, 3.12
   - Executes all unit tests
   - Uploads coverage to Codecov

2. **Integration Tests**
   - Runs on Python 3.10, 3.11, 3.12
   - Executes all integration tests with mocked external services
   - Uploads coverage to Codecov

3. **Code Quality**
   - Runs flake8 for linting
   - Runs black for code formatting checks
   - Runs mypy for type checking

4. **Docker Build Test**
   - Builds the Docker image
   - Verifies Python and dependencies are installed
   - Ensures the image can run

5. **All Tests Pass**
   - Final job that requires all previous jobs to succeed
   - Provides a single status check for PR requirements

## Test Coverage Requirements

- **Minimum coverage**: 80%
- Coverage is measured for `bot.py` and `main.py`
- Test files are excluded from coverage metrics

## Code Quality Standards

### Flake8
- Maximum line length: 127 characters
- Maximum cyclomatic complexity: 10
- Critical error codes checked: E9, F63, F7, F82

### Black
- Line length: 88 characters (default)
- All Python files must pass black formatting

### Mypy
- Type hints encouraged but not required
- Runs in non-strict mode with missing imports ignored

## Test Data and Fixtures

### Mock RSS Feeds
Integration tests use realistic RSS 2.0 and Atom feed XML for testing feed parsing.

### Mock Mastodon API
The Mastodon API is mocked using `unittest.mock` to avoid making real API calls.

### Temporary State Files
Tests use `tempfile.mktemp()` to create temporary state files that are cleaned up after each test.

## Writing New Tests

### Unit Test Template

```python
import unittest
from unittest.mock import Mock, patch
from bot import MastodonRSSBot

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.bot = MastodonRSSBot(
            client_id='test',
            client_secret='test',
            access_token='test',
            instance_url='https://test.com',
            feed_url='https://feed.test/rss.xml',
            state_file='/tmp/test_state.txt'
        )

    def test_feature(self):
        """Test description"""
        result = self.bot.some_method()
        self.assertEqual(result, expected_value)
```

### Integration Test Template

```python
import unittest
import responses
from bot import MastodonRSSBot

class TestNewIntegration(unittest.TestCase):
    @responses.activate
    @patch('bot.Mastodon')
    def test_integration(self, mock_mastodon):
        """Test description"""
        # Mock HTTP responses
        responses.add(
            responses.GET,
            'https://example.com/feed.xml',
            body=rss_xml,
            status=200
        )

        # Run test
        bot = MastodonRSSBot(...)
        result = bot.process_new_entries()

        self.assertEqual(result, expected)
```

## Continuous Integration Status

[![Tests](https://img.shields.io/github/actions/workflow/status/aserper/masto-rss/test.yml?style=for-the-badge&logo=github&label=Tests)](https://github.com/aserper/masto-rss/actions/workflows/test.yml)

## Troubleshooting

### Tests Fail Locally But Pass in CI
- Ensure you're using the same Python version
- Check that all dependencies are installed: `pip install -r requirements-test.txt`
- Clear pytest cache: `pytest --cache-clear`

### Coverage Below 80%
- Identify untested code: `pytest --cov=bot --cov-report=term-missing`
- Add tests for the missing lines
- Some error handling paths may be acceptable to skip

### Import Errors
- Ensure the project root is in PYTHONPATH
- Run tests from the project root directory
- Check virtual environment is activated

## Best Practices

1. **Test One Thing**: Each test should verify one specific behavior
2. **Clear Names**: Test names should describe what they're testing
3. **Arrange-Act-Assert**: Structure tests with setup, execution, and verification
4. **Mock External Services**: Never make real HTTP requests or API calls
5. **Clean Up**: Always clean up temporary files and state
6. **Test Edge Cases**: Test both happy paths and error conditions
7. **Keep Tests Fast**: Unit tests should run in milliseconds
8. **Document Complex Tests**: Add comments explaining non-obvious test logic

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [responses library](https://github.com/getsentry/responses)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
