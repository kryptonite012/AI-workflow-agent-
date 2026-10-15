"""
Shared pytest fixtures for browser tool tests.

Fixtures are automatically discovered by pytest.
"""
import pytest
import asyncio
from pathlib import Path
from queue import Queue
import sys

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import drivers to trigger registration
from src.tools.lggraph_tools.tools.browser_tool.utils import events_drivers
from src.tools.lggraph_tools.tools.browser_tool.Handler import Handler, HandlerEnums
from src.tools.lggraph_tools.tools.browser_tool.config import BrowserRequiredConfig
from src.tools.lggraph_tools.tools.browser_tool.runner import Runner


@pytest.fixture
def minimal_config(tmp_path):
    """Create minimal BrowserRequiredConfig for testing."""
    result_file = tmp_path / "test_result.json"
    return BrowserRequiredConfig(
        query="test query",
        file_path=result_file
    )


@pytest.fixture
def full_config(tmp_path):
    """Create full BrowserRequiredConfig with all options."""
    result_file = tmp_path / "test_result.json"
    video_dir = tmp_path / "videos"
    user_data_dir = tmp_path / "profile"

    return BrowserRequiredConfig(
        query="Go to example.com",
        file_path=result_file,
        headless=True,
        keep_alive=False,
        log=True,
        max_failures=3,
        max_steps=100,
        vision_detail_level='medium',
        record_video=True,
        video_dir=video_dir,
        user_data_dir=user_data_dir,
        browser_ready_timeout=20,
        task_timeout=600
    )


@pytest.fixture
def handler():
    """Create Handler instance."""
    return Handler()


@pytest.fixture
def runner(minimal_config):
    """Create Runner instance with minimal config."""
    return Runner(minimal_config)


@pytest.fixture
def moving_forward_bus():
    """Create Queue for inter-driver communication."""
    return Queue()


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_handler_map():
    """Reset Handler.enum_driver_map before each test."""
    # This fixture runs automatically before each test
    # But we don't actually reset it since drivers are registered at import time
    # and re-importing would cause duplicate registration errors
    pass
