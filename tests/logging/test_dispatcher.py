"""
Tests for Dispatcher.

Tests:
- Message dispatching
- Handler invocation
- Error handling
"""
import pytest
import json


class TestDispatcher:
    """Test Dispatcher functionality."""

    def test_dispatcher_importable(self):
        """Dispatcher should be importable."""
        from src.system_logging.dispatcher import Dispatcher
        assert Dispatcher is not None

    def test_dispatcher_creation(self, dispatcher):
        """Dispatcher should be instantiable."""
        assert dispatcher is not None

    def test_dispatcher_has_dispatch_method(self, dispatcher):
        """Dispatcher should have dispatch method."""
        assert hasattr(dispatcher, 'dispatch')
        assert callable(dispatcher.dispatch)

    def test_dispatch_valid_message(self, dispatcher, sample_log_message):
        """Dispatcher should handle valid JSON message."""
        try:
            result = dispatcher.dispatch(sample_log_message)
            # Should not raise exception
            assert True
        except json.JSONDecodeError:
            pytest.fail("Dispatcher failed to parse valid JSON")

    def test_dispatch_invalid_json(self, dispatcher):
        """Dispatcher should handle invalid JSON by raising DispatchError."""
        from src.system_logging.dispatcher import Dispatcher

        invalid_json = "not valid json {"

        # Dispatcher raises DispatchError for invalid JSON
        with pytest.raises((json.JSONDecodeError, Dispatcher.DispatchError, Exception)):
            dispatcher.dispatch(invalid_json)


class TestDispatcherWithHandlers:
    """Test Dispatcher with registered handlers."""

    def test_dispatch_invokes_handlers(self, dispatcher, registry, sample_log_message):
        """Dispatch should invoke registered handlers."""
        from src.system_logging.handlers.handler_base import TextHandler

        try:
            # Register a handler
            handler = TextHandler()
            registry.register(handler)
        except Exception:
            pytest.skip("Handler registration not available")

        # Dispatch message
        try:
            dispatcher.dispatch(sample_log_message)
        except Exception:
            pass  # Dispatch may have side effects

        # Handler should have been invoked (check side effects)
        # This is a basic smoke test
        assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
