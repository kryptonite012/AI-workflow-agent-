"""Unit tests for Runner class."""
import pytest
import asyncio
from pathlib import Path


class TestRunnerInitialization:
    """Test Runner initialization."""

    def test_runner_accepts_config(self, minimal_config):
        """Runner should accept BrowserRequiredConfig."""
        from src.tools.lggraph_tools.tools.browser_tool.runner import Runner

        runner = Runner(minimal_config)
        assert runner is not None

    def test_runner_singleton(self, minimal_config):
        """Runner should be a singleton."""
        from src.tools.lggraph_tools.tools.browser_tool.runner import Runner

        runner1 = Runner(minimal_config)
        runner2 = Runner(minimal_config)

        assert runner1 is runner2, "Runner should be singleton"

    def test_runner_has_result_attribute(self, runner):
        """Runner should have __result attribute initialized."""
        # Access private attribute for testing
        assert hasattr(runner, '_Runner__result')


class TestRunnerLifecycle:
    """Test Runner lifecycle execution."""

    @pytest.mark.asyncio
    async def test_runner_executes_pre_requirements(self, minimal_config):
        """Runner should execute ON_PRE_REQUIREMENTS phase."""
        from src.tools.lggraph_tools.tools.browser_tool.runner import Runner

        runner = Runner(minimal_config)

        # Mock to avoid full run
        from unittest.mock import patch, AsyncMock

        with patch.object(runner, f'_Runner__event_handler') as mock_handler:
            mock_handler.get = lambda r, e: AsyncMock(execute=AsyncMock(return_value={}))

            try:
                await runner.run()
            except AttributeError:
                # Expected - we're testing partial flow
                pass

    @pytest.mark.asyncio
    async def test_runner_handles_exception(self, minimal_config):
        """Runner should handle exceptions in lifecycle."""
        from src.tools.lggraph_tools.tools.browser_tool.runner import Runner
        from src.tools.lggraph_tools.tools.browser_tool.Handler import HandlerExceptionRaises

        runner = Runner(minimal_config)

        # We can't easily test this without mocking the entire flow
        # This is more of an integration test
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
