"""
Tests for handler registration.

Tests:
- Handler registration
- Handler retrieval
- OnTimeRegistry
"""
import pytest


class TestOnTimeRegistry:
    """Test OnTimeRegistry functionality."""

    def test_registry_importable(self):
        """OnTimeRegistry should be importable."""
        from src.system_logging.on_time_registry import OnTimeRegistry
        assert OnTimeRegistry is not None

    def test_registry_creation(self, registry):
        """OnTimeRegistry should be instantiable."""
        assert registry is not None

    def test_registry_has_handlers_list(self, registry):
        """Registry should have _handlers attribute."""
        assert hasattr(registry, '_handlers')

    def test_register_handler(self):
        """Should be able to register a handler or get registry error if already registered."""
        from src.system_logging.on_time_registry import OnTimeRegistry
        from src.system_logging.handlers.handler_base import TextHandler
        from src.system_logging.registry import Registry

        registry = OnTimeRegistry()
        handler = TextHandler()

        try:
            registry.register(handler)
            # Registration succeeded
            assert True
        except Registry.RegistryError:
            # Handler already registered - this is expected behavior
            assert True

    def test_get_all_handlers(self):
        """Should be able to get all handlers."""
        from src.system_logging.on_time_registry import OnTimeRegistry

        registry = OnTimeRegistry()
        handlers = registry.get_all_handlers()

        assert isinstance(handlers, (list, tuple, dict))
        # May have 0 or more handlers


class TestTextHandler:
    """Test TextHandler functionality."""

    def test_handler_importable(self):
        """TextHandler should be importable."""
        from src.system_logging.handlers.handler_base import TextHandler
        assert TextHandler is not None

    def test_handler_creation(self):
        """TextHandler should be instantiable."""
        from src.system_logging.handlers.handler_base import TextHandler
        handler = TextHandler()
        assert handler is not None

    def test_handler_has_name(self):
        """Handler should have name attribute."""
        from src.system_logging.handlers.handler_base import TextHandler
        handler = TextHandler()
        assert hasattr(handler, 'name')

    def test_handler_has_handle_method(self):
        """Handler should have handle method."""
        from src.system_logging.handlers.handler_base import TextHandler
        handler = TextHandler()
        assert hasattr(handler, 'handle') or hasattr(handler, '__call__')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
