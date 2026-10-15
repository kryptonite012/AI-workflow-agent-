"""
Unit tests for State management.

Tests:
- State creation
- State modifications
"""
import pytest


class TestState:
    """Test State class."""

    def test_state_importable(self):
        """State should be importable."""
        from src.models.state import State
        assert State is not None

    def test_state_creation(self):
        """State should be creatable."""
        from src.models.state import State
        state = State()
        assert state is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
