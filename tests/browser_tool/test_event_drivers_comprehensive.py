"""
Comprehensive tests for browser tool event drivers.

Tests all 7 lifecycle drivers:
1. PreRequirementsCustomEvent - Check internet, RAM, browser_use
2. SetupDriver - Create LLM, Browser, Agent
3. OnStartDriver - Wait for browser, load sessions
4. OnRunningDriver - Start monitoring, run agent
5. OnCompleteDriver - Extract result, save sessions
6. OnExceptionDriver - Log errors, write error file
7. TeardownDriver - Close agent, handle keep_alive
"""
import pytest
import asyncio
import json
from pathlib import Path
from queue import Queue
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import drivers to trigger registration
from src.tools.lggraph_tools.tools.browser_tool.utils import events_drivers
from src.tools.lggraph_tools.tools.browser_tool.Handler import Handler, HandlerEnums
from src.tools.lggraph_tools.tools.browser_tool.config import BrowserRequiredConfig
from src.tools.lggraph_tools.tools.browser_tool.runner import Runner


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def config(tmp_path):
    """Create test config."""
    return BrowserRequiredConfig(
        query="Test query: navigate to example.com",
        file_path=tmp_path / "result.json",
        headless=True,
        keep_alive=False,
        log=True
    )


@pytest.fixture
def runner(config):
    """Create test Runner instance."""
    # Reset singleton for testing
    Runner._Runner__instance = None
    return Runner(config)


@pytest.fixture
def handler():
    """Create Handler instance."""
    return Handler()


@pytest.fixture
def bus():
    """Create moving_forward_bus Queue."""
    return Queue()


@pytest.fixture
def mock_browser():
    """Create mock Browser object."""
    browser = MagicMock()
    browser._cdp_client_root = MagicMock()  # Simulate ready browser
    browser.get_current_page_url = AsyncMock(return_value="https://example.com")
    browser.get_or_create_cdp_session = AsyncMock()
    browser.event_bus = MagicMock()
    browser.event_bus.dispatch = AsyncMock()
    return browser


@pytest.fixture
def mock_agent():
    """Create mock Agent object."""
    agent = MagicMock()
    agent.run = AsyncMock()
    agent.close = AsyncMock()

    # Mock result
    result = MagicMock()
    result.final_result = MagicMock(return_value="Test result from agent")
    agent.run.return_value = result

    return agent


# =============================================================================
# PRE-REQUIREMENTS DRIVER TESTS
# =============================================================================

class TestPreRequirementsDriver:
    """Test PreRequirementsCustomEvent driver."""

    def test_driver_registered(self):
        """Driver should be registered for ON_PRE_REQUIREMENTS."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_PRE_REQUIREMENTS)
        assert driver_class is not None
        assert driver_class.__name__ == 'PreRequirementsCustomEvent'

    def test_driver_has_huge_error_true(self):
        """Driver should have huge_error=True (critical driver)."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_PRE_REQUIREMENTS)
        assert hasattr(driver_class, 'huge_error')
        assert driver_class.huge_error is True

    @pytest.mark.asyncio
    async def test_check_internet_success(self, handler, runner, bus):
        """check_internet should succeed when internet is available."""
        driver = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)

        # This will actually check internet - may fail if no internet
        try:
            result = driver.check_internet()
            assert result['internet'] == 'connected'
        except ConnectionError:
            pytest.skip("No internet connection available")

    @pytest.mark.asyncio
    async def test_check_browser_use_installed(self, handler, runner, bus):
        """check_browser_use should succeed when browser_use is installed."""
        driver = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)

        result = driver.check_browser_use()
        assert result['browser_use'] == 'installed'

    @pytest.mark.asyncio
    async def test_execute_runs_all_methods(self, handler, runner, bus):
        """execute() should run all check methods."""
        driver = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)

        result = await driver.execute(bus)

        assert 'check_internet' in result
        assert 'check_ram' in result
        assert 'check_browser_use' in result


# =============================================================================
# SETUP DRIVER TESTS
# =============================================================================

class TestSetupDriver:
    """Test SetupDriver."""

    def test_driver_registered(self):
        """Driver should be registered for SET_UP."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.SET_UP)
        assert driver_class is not None
        assert driver_class.__name__ == 'SetupDriver'

    def test_driver_has_huge_error_true(self):
        """Driver should have huge_error=True."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.SET_UP)
        assert driver_class.huge_error is True

    def test_apply_monkey_patch(self, handler, runner):
        """apply_monkey_patch_on_watch_dog should succeed."""
        driver = handler.get(runner, HandlerEnums.SET_UP)

        result = driver.apply_monkey_patch_on_watch_dog()
        assert result['monkey_patch'] == 'applied'


# =============================================================================
# ON_START DRIVER TESTS
# =============================================================================

class TestOnStartDriver:
    """Test OnStartDriver."""

    def test_driver_registered(self):
        """Driver should be registered for ON_START."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_START)
        assert driver_class is not None
        assert driver_class.__name__ == 'OnStartDriver'

    def test_driver_not_critical(self):
        """Driver should NOT have huge_error (non-critical)."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_START)
        # Should not have huge_error or should be False
        has_huge_error = getattr(driver_class, 'huge_error', False)
        assert has_huge_error is False


# =============================================================================
# ON_RUNNING DRIVER TESTS
# =============================================================================

class TestOnRunningDriver:
    """Test OnRunningDriver."""

    def test_driver_registered(self):
        """Driver should be registered for ON_RUNNING."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_RUNNING)
        assert driver_class is not None
        assert driver_class.__name__ == 'OnRunningDriver'

    def test_driver_is_critical(self):
        """Driver should have huge_error=True (agent execution is critical)."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_RUNNING)
        assert driver_class.huge_error is True

    @pytest.mark.asyncio
    async def test_run_agent(self, handler, runner, mock_agent, bus):
        """run_agent should execute agent.run()."""
        driver = handler.get(runner, HandlerEnums.ON_RUNNING)

        # Inject mock agent
        runner._Runner__agent = mock_agent

        result = await driver.run_agent()

        assert result['agent_run'] == 'completed'
        mock_agent.run.assert_called_once()


# =============================================================================
# ON_COMPLETE DRIVER TESTS
# =============================================================================

class TestOnCompleteDriver:
    """Test OnCompleteDriver."""

    def test_driver_registered(self):
        """Driver should be registered for ON_COMPLETE."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_COMPLETE)
        assert driver_class is not None
        assert driver_class.__name__ == 'OnCompleteDriver'

    def test_driver_not_critical(self):
        """Driver should NOT have huge_error."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_COMPLETE)
        has_huge_error = getattr(driver_class, 'huge_error', False)
        assert has_huge_error is False

    @pytest.mark.asyncio
    async def test_extract_final_result(self, handler, runner, mock_agent, bus):
        """extract_final_result should get result from agent."""
        driver = handler.get(runner, HandlerEnums.ON_COMPLETE)

        # Simulate agent result
        mock_result = MagicMock()
        mock_result.final_result.return_value = "Test final result"
        runner._Runner__agent_result = mock_result

        result = await driver.extract_final_result()

        assert result['final_result'] == "Test final result"

    @pytest.mark.asyncio
    async def test_write_result_to_file(self, handler, runner, tmp_path, bus):
        """write_result_to_file should write JSON file."""
        # Create new runner with tmp_path
        config = BrowserRequiredConfig(
            query="Test",
            file_path=tmp_path / "result.json"
        )
        Runner._Runner__instance = None
        runner = Runner(config)

        driver = handler.get(runner, HandlerEnums.ON_COMPLETE)
        runner._Runner__final_result = "Test result content"

        result = await driver.write_result_to_file()

        assert result['file_written'] is True

        # Verify file content
        with open(tmp_path / "result.json", 'r') as f:
            data = json.load(f)

        assert data['status'] == 'success'
        assert data['result'] == 'Test result content'


# =============================================================================
# ON_EXCEPTION DRIVER TESTS
# =============================================================================

class TestOnExceptionDriver:
    """Test OnExceptionDriver."""

    def test_driver_registered(self):
        """Driver should be registered for ON_EXCEPTION."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_EXCEPTION)
        assert driver_class is not None
        assert driver_class.__name__ == 'OnExceptionDriver'

    @pytest.mark.asyncio
    async def test_log_exception(self, handler, runner, bus):
        """log_exception should log stored exception."""
        driver = handler.get(runner, HandlerEnums.ON_EXCEPTION)

        # Store an exception
        runner._Runner__last_exception = ValueError("Test error")

        result = await driver.log_exception()

        assert result['exception_logged'] is True
        assert result['type'] == 'ValueError'
        assert 'Test error' in result['message']

    @pytest.mark.asyncio
    async def test_write_error_to_file(self, handler, tmp_path, bus):
        """write_error_to_file should write error JSON."""
        config = BrowserRequiredConfig(
            query="Test",
            file_path=tmp_path / "error.json"
        )
        Runner._Runner__instance = None
        runner = Runner(config)

        driver = handler.get(runner, HandlerEnums.ON_EXCEPTION)
        runner._Runner__last_exception = RuntimeError("Critical failure")

        result = await driver.write_error_to_file()

        assert result['error_written'] is True

        # Verify file content
        with open(tmp_path / "error.json", 'r') as f:
            data = json.load(f)

        assert data['status'] == 'error'
        assert 'Critical failure' in data['error']


# =============================================================================
# TEARDOWN DRIVER TESTS
# =============================================================================

class TestTeardownDriver:
    """Test TeardownDriver."""

    def test_driver_registered(self):
        """Driver should be registered for TEAR_DOWN."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.TEAR_DOWN)
        assert driver_class is not None
        assert driver_class.__name__ == 'TeardownDriver'

    def test_driver_not_critical(self):
        """Driver should NOT have huge_error (best-effort cleanup)."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.TEAR_DOWN)
        has_huge_error = getattr(driver_class, 'huge_error', False)
        assert has_huge_error is False

    @pytest.mark.asyncio
    async def test_close_agent(self, handler, runner, mock_agent, bus):
        """close_agent should close the agent."""
        driver = handler.get(runner, HandlerEnums.TEAR_DOWN)
        runner._Runner__agent = mock_agent

        result = await driver.close_agent()

        assert result['agent_closed'] is True
        mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_resources(self, handler, runner, bus):
        """cleanup_resources should complete."""
        driver = handler.get(runner, HandlerEnums.TEAR_DOWN)

        result = await driver.cleanup_resources()

        assert result['cleanup'] == 'done'


# =============================================================================
# FULL RUNNER INTEGRATION TESTS
# =============================================================================

class TestRunnerIntegration:
    """Integration tests for full Runner.run() flow."""

    @pytest.mark.asyncio
    async def test_runner_prereqs_only(self, tmp_path):
        """Test Runner executes PRE_REQUIREMENTS phase."""
        config = BrowserRequiredConfig(
            query="Test",
            file_path=tmp_path / "result.json",
            headless=True,
            keep_alive=False
        )
        Runner._Runner__instance = None
        runner = Runner(config)

        # We can't run full flow without real browser, but PRE_REQUIREMENTS should work
        handler = Handler()
        bus = Queue()

        driver = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)
        result = await driver.execute(bus)

        assert 'check_internet' in result
        assert 'check_browser_use' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
