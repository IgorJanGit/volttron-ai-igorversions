# Test Suite Documentation

This folder contains all test files for the VOLTTRON AI Chat application.

## 🧪 Test Files

### Core Tests

- **`test_ai_service.py`** - Unit tests for the AI service
  - Tests tool registration
  - Tests function calling
  - Tests AI response generation

- **`test_isolated.py`** - Isolated component tests
  - Tests individual functions in isolation
  - No external dependencies

### Intelligent Discovery Tests

- **`test_intelligent_discovery.py`** - Comprehensive test suite (22 tests)
  - Tests AI's ability to run `vctl --help`
  - Tests command discovery and execution
  - Tests intent mapping
  - Full coverage of discovery feature

- **`test_discovery_quick.py`** - Quick validation (4 tests)
  - Fast smoke tests for intelligent discovery
  - Verifies core discovery functionality
  - Useful for rapid testing during development

- **`test_context_retention.py`** - Context and memory tests (5 tests)
  - Tests AI's ability to retain context across conversations
  - Tests back-and-forth command execution
  - Tests context recall and switching

### Demo & Visualization

- **`demo_intelligent_discovery.py`** - Interactive visual demonstration
  - Shows intelligent discovery in action
  - User-friendly demonstration of features
  - Can be used for presentations

### Utility Scripts

- **`test_runner.py`** - Test runner utility
  - Runs multiple test suites
  - Provides summary reports
  - Cross-platform compatibility

- **`test_visual_chat.py`** - Visual chat launcher
  - Launches chat interface for testing
  - Opens web browser automatically
  - User-friendly testing interface

- **`verify_tests.py`** - Test verification utility
  - Verifies test environment setup
  - Checks dependencies

## 📊 Documentation

- **`INTELLIGENT_DISCOVERY_TEST_RESULTS.md`** - Complete test report
  - Test results and metrics
  - Feature documentation
  - Usage examples
  - Implementation details

- **`TESTING.md`** - Comprehensive testing guide
  - Testing strategies
  - Best practices
  - Test coverage information

- **`TESTING_SUMMARY.md`** - Testing overview
  - Quick reference guide
  - Summary of all test types
  - Testing workflow

- **`TEST_ORGANIZATION.md`** - Test structure documentation
  - File organization
  - Test categories
  - Naming conventions

## 🚀 Running Tests

### Run All Intelligent Discovery Tests
```bash
cd tests
python3 test_intelligent_discovery.py
```

### Quick Test (Fast)
```bash
cd tests
python3 test_discovery_quick.py
```

### Context Retention Test
```bash
cd tests
python3 test_context_retention.py
```

### Interactive Demo
```bash
cd tests
python3 demo_intelligent_discovery.py
```

### Visual Chat Interface
```bash
cd tests
python3 test_visual_chat.py
```

### Unit Tests
```bash
cd tests
pytest test_ai_service.py
```

## ⚙️ Prerequisites

Before running tests, ensure:
1. Chat app is running on `http://127.0.0.1:8000`
2. VOLTTRON platform is accessible
3. Required Python packages are installed:
   ```bash
   pip install -r test_requirements.txt
   ```

## 📝 Test Results Summary

**Last Run:** October 27, 2025

| Test Suite | Tests | Passed | Failed | Success Rate |
|------------|-------|--------|--------|--------------|
| Intelligent Discovery | 6 | 6 | 0 | 100% |
| Context Retention | 5 | 5 | 0 | 100% |
| Quick Validation | 4 | 4 | 0 | 100% |
| **Total** | **15** | **15** | **0** | **100%** |

## 🐛 Troubleshooting

### Chat app not responding
```bash
# Check if running
ps aux | grep chat_app

# Start it
cd ..
python3 -m chat_app
```

### Connection refused
```bash
# Wait for server startup (3-5 seconds)
sleep 5
curl http://127.0.0.1:8000/
```

### Import errors
```bash
# Install dependencies
pip install -r test_requirements.txt
```

## 📚 Additional Resources

- See `INTELLIGENT_DISCOVERY_TEST_RESULTS.md` for detailed test analysis
- See `TESTING.md` for comprehensive testing guide
- See `TESTING_SUMMARY.md` for quick testing overview
- See `TEST_ORGANIZATION.md` for test structure details
- See `../README.md` for general project documentation
- See individual test files for specific test case details
