# 🧪 AI-LLM Test Suite - Refactored

> **📊 Refactoring Date:** 2026-01-31  
> **Structure:** Component-based test organization

## 📁 Test Package Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── pytest.ini                     # Pytest configuration
├── README.md                      # This file
│
├── unit/                          # Fast, isolated unit tests
│   ├── __init__.py
│   ├── test_config.py            # Configuration tests
│   ├── test_model_manager.py     # ModelManager tests
│   └── test_state.py             # State management tests
│
├── mcp/                           # MCP (Model Context Protocol) tests
│   ├── __init__.py
│   ├── test_mcp_manager.py       # MCP Manager tests
│   ├── test_mcp_servers.py       # MCP server health tests
│   └── test_universal_tool.py    # Universal tool tests
│
├── logging/                       # Logging system tests
│   ├── __init__.py
│   ├── test_dispatcher.py        # Dispatcher tests
│   ├── test_handlers.py          # Handler registration tests
│   └── test_error_transfer.py    # Error transfer tests
│
├── api/                           # API integration tests
│   ├── __init__.py
│   ├── test_openai_integration.py
│   └── test_error_handling.py    # API error handling
│
├── browser_tool/                  # Browser tool tests (NEW)
│   ├── unit/
│   └── integration/
│
├── integration/                   # Integration tests
│   ├── __init__.py
│   ├── test_workflow.py          # Complete workflow tests
│   └── test_agent_mode.py        # Agent mode tests
│
└── _legacy/                       # Deprecated tests (DO NOT RUN)
    └── README.md
```

## 🚀 Running Tests

```bash
# Run ALL tests
pytest tests/ -v

# Run specific component
pytest tests/unit/ -v
pytest tests/mcp/ -v
pytest tests/logging/ -v
pytest tests/api/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run only fast tests (unit)
pytest tests/unit/ -v --timeout=10

# Run integration tests
pytest tests/integration/ -v
```

## ✅ Test Standards

1. **All tests use pytest** - No standalone scripts
2. **Fixtures in conftest.py** - Shared setup/teardown
3. **Markers for slow tests** - `@pytest.mark.slow`
4. **Markers for integration** - `@pytest.mark.integration`
5. **Async tests** - Use `@pytest.mark.asyncio`

## 📊 Coverage Goals

- Unit tests: 80%+
- Integration: 60%+
- Overall: 70%+
