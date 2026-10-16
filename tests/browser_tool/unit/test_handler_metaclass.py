"""
Unit tests for Handler metaclass system.

Tests:
- Metaclass registration
- execute() method injection
- Driver enumeration
- Exception handling
"""
import pytest
import asyncio
from pathlib import Path
from queue import Queue


class TestHandlerMetaclass:
    """Test the metaclass registration system."""

    def test_handler_has_enum_driver_map(self, handler):
        """Handler class should have enum_driver_map attribute."""
        from src.tools.lggraph_tools.tools.browser_tool.Handler import Handler

        assert hasattr(Handler, 'enum_driver_map')
        assert isinstance(Handler.enum_driver_map, dict)

    def test_enum_driver_map_has_all_enums(self, handler):
        """enum_driver_map should have entries for all HandlerEnums."""
        from src.tools.lggraph_tools.tools.browser_tool.Handler import Handler, HandlerEnums

        for enum_member in HandlerEnums:
            assert enum_member in Handler.enum_driver_map, f"{enum_member} missing from map"

    def test_all_drivers_registered(self, handler):
        """All enum values should have driver classes registered."""
        from src.tools.lggraph_tools.tools.browser_tool.Handler import Handler

        for enum_member, driver_class in Handler.enum_driver_map.items():
            assert driver_class is not None, f"{enum_member} has no driver"
            assert issubclass(driver_class, Handler), f"{driver_class} not a Handler subclass"

    def test_driver_has_enum_value(self):
        """Each driver class should have enum_value attribute."""
        from src.tools.lggraph_tools.tools.browser_tool.Handler import Handler, HandlerEnums

        for enum_member, driver_class in Handler.enum_driver_map.items():
            assert hasattr(driver_class, 'enum_value'), f"{driver_class} missing enum_value"
            assert driver_class.enum_value == enum_member, f"{driver_class} enum_value mismatch"


class TestExecuteMethodInjection:
    """Test that execute() is properly injected into driver classes."""

    def test_driver_has_execute_method(self):
        """Driver classes should have execute attribute."""
        from src.tools.lggraph_tools.tools.browser_tool.Handler import Handler, HandlerEnums

        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_PRE_REQUIREMENTS)
        assert driver_class is not None, "PreRequirementsCustomEvent not registered"
        assert hasattr(driver_class, 'execute'), "execute not injected"

    def test_execute_is_coroutine(self):
        """execute should be a coroutine function."""
        from src.tools.lggraph_tools.tools.browser_tool.Handler import Handler, HandlerEnums

        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_PRE_REQUIREMENTS)
        assert asyncio.iscoroutinefunction(driver_class.execute), "execute not async"

    @pytest.mark.asyncio
    async def test_execute_runs_driver_methods(self, runner, moving_forward_bus):
        """execute() should find and run driver methods."""
        from src.tools.lggraph_tools.tools.browser_tool.Handler import Handler, HandlerEnums

        handler = Handler()
        driver = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)

        # Execute driver
        result = await driver.execute(moving_forward_bus)

        # Should return dict of results
        assert isinstance(result, dict), "execute should return dict"
        assert len(result) > 0, "execute should run at least one method"


class TestHandlerGetMethod:
    """Test Handler.get() method."""

    def test_get_returns_driver_instance(self, handler, runner):
        """get() should return driver instance, not class."""
        from src.tools.lggraph_tools.tools.browser_tool.Handler import Handler, HandlerEnums

        driver = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)

        # Should be an instance
        assert not isinstance(driver, type), "get() returned class, not instance"
        assert isinstance(driver, Handler), "Driver not a Handler instance"

    def test_get_injects_runner(self, handler, runner):
        """get() should inject runner instance into driver."""
        from src.tools.lggraph_tools.tools.browser_tool.Handler import HandlerEnums

        driver = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)

        # Driver should have runner attribute
        assert hasattr(driver, 'runner'), "Runner not injected into driver"
        assert driver.runner is runner, "Runner not same instance"

    def test_get_different_enums_returns_different_drivers(self, handler, runner):
        """get() with different enums should return different driver classes."""
        from src.tools.lggraph_tools.tools.browser_tool.Handler import HandlerEnums

        driver1 = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)
        driver2 = handler.get(runner, HandlerEnums.SET_UP)

        assert type(driver1) != type(driver2), "Different enums should return different drivers"


class TestExceptionHandling:
    """Test exception handling in drivers."""

    @pytest.mark.asyncio
    async def test_driver_exception_propagates(self, runner, moving_forward_bus):
        """Exceptions in driver methods should propagate."""
        from src.tools.lggraph_tools.tools.browser_tool.Handler import Handler, HandlerEnums

        handler = Handler()
        driver = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)

        # Monkey-patch a method to raise exception
        original_method = driver.check_internet

        async def failing_method():
            raise ValueError("Test exception from check_internet")

        driver.check_internet = failing_method

        # Execute should propagate the exception
        with pytest.raises(ValueError, match="Test exception"):
            await driver.execute(moving_forward_bus)

        # Restore original method
        driver.check_internet = original_method


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
