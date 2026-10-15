import pytest
import asyncio
from pathlib import Path
from queue import Queue

# Add project root to path
import sys
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import drivers FIRST to trigger registration
from src.tools.lggraph_tools.tools.browser_tool.utils import events_drivers

from src.tools.lggraph_tools.tools.browser_tool.Handler import (
    Handler,
    HandlerEnums,
    HandlerExceptionRaises,
    HandlerMeta
)
from src.tools.lggraph_tools.tools.browser_tool.config import BrowserRequiredConfig
from src.tools.lggraph_tools.tools.browser_tool.runner import Runner


class TestHandlerMetaclass:
    """Test the metaclass registration system."""

    def test_handler_has_enum_driver_map(self):
        """Handler class should have enum_driver_map attribute."""
        assert hasattr(Handler, 'enum_driver_map')
        assert isinstance(Handler.enum_driver_map, dict)

    def test_enum_driver_map_has_all_enums(self):
        """enum_driver_map should have entries for all HandlerEnums."""
        for enum_member in HandlerEnums:
            assert enum_member in Handler.enum_driver_map, f"{enum_member} missing from map"

    def test_drivers_are_registered(self):
        """All enum values should have driver classes registered."""
        # Note: This will fail until all drivers are implemented
        missing = [e.name for e, v in Handler.enum_driver_map.items() if v is None]
        if missing:
            pytest.skip(f"Drivers not yet implemented: {', '.join(missing)}")

        for enum_member, driver_class in Handler.enum_driver_map.items():
            assert driver_class is not None, f"{enum_member} has no driver"
            assert issubclass(driver_class, Handler), f"{driver_class} not a Handler subclass"


class TestExecuteMethodInjection:
    """Test that execute() is properly injected into driver classes."""

    def test_driver_has_execute_method(self):
        """Driver classes should have execute attribute."""
        # Get PreRequirementsCustomEvent driver
        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_PRE_REQUIREMENTS)

        if driver_class is None:
            pytest.skip("PreRequirementsCustomEvent not registered yet")

        # Check class has execute attribute
        assert hasattr(driver_class, 'execute'), "execute not injected"

    def test_execute_is_callable(self):
        """execute should be callable."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_PRE_REQUIREMENTS)

        if driver_class is None:
            pytest.skip("PreRequirementsCustomEvent not registered yet")

        assert callable(driver_class.execute), "execute not callable"

    @pytest.mark.asyncio
    async def test_execute_runs_driver_methods(self):
        """execute() should find and run driver methods."""
        driver_class = Handler.enum_driver_map.get(HandlerEnums.ON_PRE_REQUIREMENTS)

        if driver_class is None:
            pytest.skip("PreRequirementsCustomEvent not registered yet")

        # Create minimal config
        config = BrowserRequiredConfig(
            query="test",
            file_path=Path("test_result.json")
        )

        # Create runner (needed for driver __init__)
        runner = Runner(config)

        # Create driver instance
        driver_instance = driver_class(runner)

        # Create bus
        bus = Queue()

        # Execute driver
        try:
            result = await driver_instance.execute(bus)

            # Should return dict of results
            assert isinstance(result, dict), "execute should return dict"
            print(f"✅ Execute returned: {list(result.keys())}")

        except Exception as e:
            pytest.fail(f"execute() raised exception: {e}")


class TestHandlerGetMethod:
    """Test Handler.get() method."""

    def test_get_returns_driver_instance(self):
        """get() should return driver instance, not class."""
        handler = Handler()

        # Create minimal config and runner
        config = BrowserRequiredConfig(query="test", file_path=Path("test.json"))
        runner = Runner(config)

        # Try to get PreRequirements driver
        try:
            driver = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)

            # Should be an instance
            assert not isinstance(driver, type), "get() returned class, not instance"
            assert isinstance(driver, Handler), "Driver not a Handler instance"

            print(f"✅ get() returned: {type(driver).__name__}")

        except KeyError:
            pytest.skip("PreRequirementsCustomEvent not registered yet")


class TestFullLifecycleFlow:
    """Test complete Runner lifecycle."""

    @pytest.mark.asyncio
    async def test_runner_lifecycle_prereqs_only(self):
        """Test just the ON_PRE_REQUIREMENTS phase."""
        config = BrowserRequiredConfig(
            query="test query",
            file_path=Path("test_output.json"),
            headless=True
        )

        runner = Runner(config)
        handler = Handler()

        # Try just the pre-requirements phase
        try:
            driver = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)
            bus = Queue()

            result = await driver.execute(bus)

            print(f"✅ Pre-requirements completed: {result}")
            assert isinstance(result, dict)

        except Exception as e:
            # Expected if browser_use not installed
            if "browser_use" in str(e) and "not installed" in str(e):
                pytest.skip("browser_use not installed")
            else:
                raise

    @pytest.mark.asyncio
    async def test_runner_full_flow(self):
        """Test full Runner.run() flow (will fail until all drivers implemented)."""
        config = BrowserRequiredConfig(
            query="Go to example.com",
            file_path=Path("test_full_output.json"),
            headless=True,
            keep_alive=False
        )

        runner = Runner(config)

        try:
            result = await runner.run()
            print(f"✅ Full flow completed: {result}")

        except HandlerExceptionRaises.CustomEventNotFound as e:
            pytest.skip(f"Not all drivers implemented: {e}")
        except Exception as e:
            if "not installed" in str(e):
                pytest.skip(f"Missing dependency: {e}")
            else:
                raise


class TestExceptionHandling:
    """Test exception handling in drivers."""

    @pytest.mark.asyncio
    async def test_driver_exception_propagates(self):
        """Exceptions in driver methods should propagate."""
        # Create instance using existing driver
        config = BrowserRequiredConfig(query="test", file_path=Path("test.json"))
        runner = Runner(config)
        handler = Handler()

        # Get the PreRequirements driver
        driver = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)

        # Monkey-patch one of its methods to raise an exception
        original_check = driver.check_internet

        async def failing_check():
            raise ValueError("Test exception from check_internet")

        driver.check_internet = failing_check

        # Execute should propagate the exception
        bus = Queue()

        with pytest.raises(ValueError, match="Test exception"):
            await driver.execute(bus)

        # Restore original method
        driver.check_internet = original_check


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '-s'])
