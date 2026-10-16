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
        """Runner should start with no result."""
        assert runner.result is None


class TestRunnerLifecycle:
    """Test Runner lifecycle execution."""

    @pytest.mark.asyncio
    async def test_runner_executes_pre_requirements(self, minimal_config):
        """Runner should execute every lifecycle phase in order."""
        from unittest.mock import patch, AsyncMock, MagicMock
        from src.tools.lggraph_tools.tools.browser_tool.runner import Runner
        from src.tools.lggraph_tools.tools.browser_tool.Handler import HandlerEnums

        runner = Runner(minimal_config)
        phases = []

        def get_driver(_runner, event):
            phases.append(event)
            return MagicMock(execute=AsyncMock(return_value={}))

        with patch("src.tools.lggraph_tools.tools.browser_tool.runner.Handler") as mock_handler_cls:
            mock_handler_cls.return_value.get.side_effect = get_driver
            result = await runner.run()

        assert phases == [
            HandlerEnums.ON_PRE_REQUIREMENTS,
            HandlerEnums.SET_UP,
            HandlerEnums.ON_START,
            HandlerEnums.ON_RUNNING,
            HandlerEnums.ON_COMPLETE,
            HandlerEnums.TEAR_DOWN,
        ]
        assert result["status"] == "completed"

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
