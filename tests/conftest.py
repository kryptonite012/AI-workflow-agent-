"""
Shared pytest fixtures for all test modules.

This file is automatically discovered by pytest.
Fixtures defined here are available to all tests.
"""
import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ============================================================================
# CORE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def project_root_path():
    """Return project root path."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def temp_dir(tmp_path):
    """Return temporary directory for tests."""
    return tmp_path


# ============================================================================
# MODEL MANAGER FIXTURES
# ============================================================================

@pytest.fixture
def model_manager():
    """Create ModelManager instance for testing."""
    from src.utils.model_manager import ModelManager
    from src.config import settings
    return ModelManager(model=settings.DEFAULT_MODEL)


# ============================================================================
# MCP FIXTURES
# ============================================================================

@pytest.fixture
def mcp_manager():
    """Create MCP_Manager instance for testing."""
    from src.mcp.manager import MCP_Manager
    return MCP_Manager()


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for unit tests."""
    server = Mock()
    server.name = "mock_server"
    server.is_running = True
    server.execute = AsyncMock(return_value={"result": "success"})
    return server


# ============================================================================
# LOGGING FIXTURES
# ============================================================================

@pytest.fixture
def dispatcher():
    """Create Dispatcher instance for testing."""
    from src.system_logging.dispatcher import Dispatcher
    return Dispatcher()


@pytest.fixture
def registry():
    """Create OnTimeRegistry instance for testing."""
    from src.system_logging.on_time_registry import OnTimeRegistry
    return OnTimeRegistry()


@pytest.fixture
def sample_log_message():
    """Sample log message for testing."""
    import json
    return json.dumps({
        "LOG_TYPE": "OTHER",
        "LEVEL": "INFO",
        "MESSAGE": "Test message",
        "TIME_STAMP": "2026-01-31T10:00:00",
        "METADATA": {"test": True}
    })


# ============================================================================
# API FIXTURES
# ============================================================================

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = Mock(return_value=Mock(
        choices=[Mock(message=Mock(content="Test response"))]
    ))
    return client


@pytest.fixture
def openai_integration():
    """Create OpenAIIntegration instance for testing."""
    from src.utils.open_ai_integration import OpenAIIntegration
    return OpenAIIntegration()


# ============================================================================
# STATE FIXTURES
# ============================================================================

@pytest.fixture
def empty_state():
    """Create empty State for testing."""
    from src.models.state import State
    return State()


@pytest.fixture
def state_accessor(empty_state):
    """Create StateAccessor for testing."""
    from src.models.state import StateAccessor
    return StateAccessor(empty_state)


# ============================================================================
# EVENT LOOP FIXTURES
# ============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "requires_api: marks tests that require API keys")
    config.addinivalue_line("markers", "requires_mcp: marks tests that require MCP servers")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on location."""
    for item in items:
        # Add integration marker to tests in integration folder
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add slow marker to certain test patterns
        if "comprehensive" in item.name.lower() or "full" in item.name.lower():
            item.add_marker(pytest.mark.slow)
