# ModelManager Test Suite

Comprehensive test suite for the ModelManager singleton class that wraps ChatOllama.

## Test Structure

### 1. `test_singleton_behavior.py`
Tests the singleton pattern implementation:
- Single instance creation
- Instance identity across different parameters
- Basic thread safety for singleton creation

### 2. `test_model_loading.py`
Tests model loading functionality:
- Loading valid/invalid models
- Model switching logic
- Detection of already running models
- Model stopping functionality

### 3. `test_integration.py`
Tests integration with ChatOllama:
- Method inheritance verification
- Parameter passing to parent class
- Multiple instance behavior
- Class variable persistence

### 4. `test_error_handling.py`
Tests error scenarios:
- Invalid model names
- Subprocess errors and timeouts
- Malformed output handling
- Unicode and large output handling

### 5. `test_thread_safety.py`
Advanced thread safety tests:
- Concurrent instance creation
- Concurrent model loading
- Race condition detection
- Thread pool executor compatibility

## Running Tests

### Run All Tests
```bash
python tests/model_manager_tests/test_runner.py
```

### Run Specific Test Categories
```bash
# Singleton tests
python tests/model_manager_tests/test_runner.py singleton

# Model loading tests
python tests/model_manager_tests/test_runner.py loading

# Integration tests
python tests/model_manager_tests/test_runner.py integration

# Error handling tests
python tests/model_manager_tests/test_runner.py error

# Thread safety tests
python tests/model_manager_tests/test_runner.py thread
```

### Run Individual Test Files
```bash
python -m unittest tests.model_manager_tests.test_singleton_behavior
python -m unittest tests.model_manager_tests.test_model_loading
python -m unittest tests.model_manager_tests.test_integration
python -m unittest tests.model_manager_tests.test_error_handling
python -m unittest tests.model_manager_tests.test_thread_safety
```

## Test Coverage

The test suite covers:
- ✅ Singleton pattern correctness
- ✅ Thread safety (basic and advanced)
- ✅ Model loading and switching
- ✅ Error handling and edge cases
- ✅ ChatOllama integration
- ✅ Class variable management
- ✅ Subprocess interaction mocking
- ✅ Unicode and large data handling

## Dependencies

Tests use Python's built-in `unittest` framework with mocking via `unittest.mock`. No additional test dependencies required.

## Notes

- All tests use mocking to avoid actual Ollama subprocess calls
- Singleton instance is reset before each test to ensure isolation
- Thread safety tests use various synchronization primitives to detect race conditions
- Error handling tests cover both expected and unexpected failure scenarios